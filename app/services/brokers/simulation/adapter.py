"""Private socket-free adapter backed by an injected authority port."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast, override

from app.services.brokers._shared.base import _UnsupportedAdapterBase
from app.services.brokers.canonical_contracts import (
    BrokerAccountTransaction,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerOrderCheck,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    StandardResponse,
)
from app.services.brokers.canonical_contracts.enums import BrokerErrorCode
from app.services.brokers.canonical_contracts.models import (
    BrokerError,
    BrokerPositionReductionRequest,
)
from app.services.brokers.canonical_contracts.protocols import BrokerAdapter
from app.services.brokers.metatrader.mapping import (
    _map_error_code,
    _map_order_check,
    _map_order_result,
)
from app.services.brokers.simulation.contracts import (
    SimulationMutationEnvelope,
    SimulationReadEnvelope,
)
from app.services.brokers.simulation.lifecycle import lifecycle_state_from_response

if TYPE_CHECKING:
    from app.services.brokers.simulation.contracts import SimulationAuthorityPort

_MAX_HISTORY_PAGE_SIZE = 1000


class SimulationBrokerAdapter(_UnsupportedAdapterBase):
    """Delegate admitted broker behavior without owning simulation semantics."""

    def __init__(
        self, config: BrokerConnectionConfig, authority_port: object | None
    ) -> None:
        """Initialize the adapter with an exact structural authority.

        Args:
            config: Exact simulation connection configuration.
            authority_port: Object implementing the Brokers-owned port.

        Raises:
            TypeError: If the injected authority does not satisfy the port.
        """
        required = (
            "connect",
            "disconnect",
            "reconnect",
            "is_connected",
            "get_connection_status",
            "ping",
            "connection_events",
            "finalize_session",
        )
        if authority_port is None or any(
            not callable(getattr(authority_port, name, None)) for name in required
        ):
            raise TypeError("authority_port must satisfy SimulationAuthorityPort")
        super().__init__(config)
        self._authority = cast("SimulationAuthorityPort", authority_port)
        self._last_read_sequence: dict[tuple[str, str], int] = {}
        self._mutation_keys: set[str] = set()

    @staticmethod
    def _validate_time(value: datetime, name: str) -> None:
        """Require one aware zero-offset UTC timestamp.

        Args:
            value: Timestamp supplied by the authority.
            name: Stable field name for diagnostics.

        Raises:
            ValueError: If the timestamp is naive or non-UTC.
        """
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            message = f"{name} must be aware UTC"
            raise ValueError(message)

    def _read_error(
        self, operation: BrokerCapabilityId, reason: str
    ) -> StandardResponse[Any]:
        """Return a fail-closed delivery-evidence error.

        Args:
            operation: Read capability that could not be proven clean.
            reason: Bounded non-sensitive failure reason.

        Returns:
            Canonical Brokers error response.
        """
        error = BrokerError(
            code=BrokerErrorCode.BROKER_RESPONSE_INVALID,
            message=f"Simulation {operation.value} authority evidence is invalid",
            capability=operation,
            details={"delivery_state": reason},
        )
        self._last_error = error
        return self._result(operation, error=error)

    def _deal_not_found(self, deal_id: str) -> StandardResponse[Any]:
        """Return the canonical missing-deal result without authority invention.

        Args:
            deal_id: Exact authority identity that was not found.

        Returns:
            Canonical missing-deal response.
        """
        error = BrokerError(
            code=BrokerErrorCode.BROKER_DEAL_NOT_FOUND,
            message="Simulation authority did not find the requested deal",
            capability=BrokerCapabilityId.GET_DEAL,
            details={"deal_id": deal_id},
        )
        self._last_error = error
        return self._result(BrokerCapabilityId.GET_DEAL, error=error)

    @staticmethod
    def _valid_history_arguments(
        operation: BrokerCapabilityId, arguments: Mapping[str, object]
    ) -> bool:
        """Return whether a history request is explicitly bounded and UTC.

        Args:
            operation: History operation being validated.
            arguments: Exact caller-supplied arguments.

        Returns:
            Whether the arguments satisfy the bounded-history contract.
        """
        if operation is BrokerCapabilityId.GET_DEAL:
            deal_id = arguments.get("deal_id")
            return isinstance(deal_id, str) and bool(deal_id.strip())
        start = arguments.get("start")
        end = arguments.get("end")
        limit = arguments.get("limit")
        return (
            isinstance(start, datetime)
            and isinstance(end, datetime)
            and start.tzinfo is not None
            and end.tzinfo is not None
            and start.utcoffset() == timedelta(0)
            and end.utcoffset() == timedelta(0)
            and start < end
            and isinstance(limit, int)
            and not isinstance(limit, bool)
            and 0 < limit <= _MAX_HISTORY_PAGE_SIZE
        )

    @staticmethod
    def _valid_history_payload(  # noqa: PLR0911 - each contract fault fails closed.
        operation: BrokerCapabilityId,
        payload: object,
        arguments: Mapping[str, object],
    ) -> bool:
        """Validate canonical type, bounds, ordering, and referential fields.

        Args:
            operation: History operation being validated.
            payload: Exact authority payload.
            arguments: Validated invocation arguments.

        Returns:
            Whether the authority payload proves the requested history contract.
        """
        if operation is BrokerCapabilityId.GET_DEAL:
            return (
                isinstance(payload, BrokerDeal)
                and payload.deal_id == arguments.get("deal_id")
                and payload.order_id is not None
                and payload.position_id is not None
                and payload.entry is not None
                and payload.reason is not None
                and payload.provider_timestamp is not None
            )
        if not isinstance(payload, BrokerPage):
            return False
        expected_type = (
            BrokerDeal
            if operation is BrokerCapabilityId.LIST_DEAL_HISTORY
            else BrokerAccountTransaction
        )
        if any(not isinstance(item, expected_type) for item in payload.items):
            return False
        if operation is BrokerCapabilityId.LIST_DEAL_HISTORY and any(
            not isinstance(item, BrokerDeal)
            or item.order_id is None
            or item.position_id is None
            or item.entry is None
            or item.reason is None
            or item.provider_timestamp is None
            for item in payload.items
        ):
            return False
        start = cast("datetime", arguments["start"])
        end = cast("datetime", arguments["end"])
        timestamps = tuple(item.provider_timestamp for item in payload.items)
        if any(
            timestamp is None or not start <= timestamp < end
            for timestamp in timestamps
        ):
            return False
        if timestamps != tuple(sorted(timestamps)):
            return False
        symbol = arguments.get("symbol")
        if symbol is not None and any(
            not isinstance(item, BrokerDeal) or item.symbol != symbol
            for item in payload.items
        ):
            return False
        return payload.limit == arguments.get("limit")

    async def _delegate_read(  # noqa: C901, PLR0911, PLR0912 - explicit failures.
        self, operation: BrokerCapabilityId, arguments: Mapping[str, object]
    ) -> StandardResponse[Any]:
        """Validate and project one authority-owned canonical read.

        Args:
            operation: Admitted canonical read operation.
            arguments: Public invocation arguments.

        Returns:
            Exact canonical payload or a fail-closed delivery error.
        """
        if self._state is not BrokerConnectionState.READY:
            return self._not_connected(operation)
        history_operations = {
            BrokerCapabilityId.LIST_DEAL_HISTORY,
            BrokerCapabilityId.GET_DEAL,
            BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS,
        }
        if operation in history_operations and not self._valid_history_arguments(
            operation, arguments
        ):
            return self._read_error(operation, "unbounded_or_invalid_history_request")
        read = getattr(self._authority, "read", None)
        if not callable(read):
            return self._read_error(operation, "authority_read_unbound")
        try:
            envelope = await read(operation, MappingProxyType(dict(arguments)))
            if not isinstance(envelope, SimulationReadEnvelope):
                return self._read_error(operation, "invalid_envelope")
            if operation is BrokerCapabilityId.GET_DEAL and envelope.payload is None:
                return self._deal_not_found(str(arguments["deal_id"]))
            if operation in history_operations and not self._valid_history_payload(
                operation, envelope.payload, arguments
            ):
                return self._read_error(operation, "invalid_history_payload")
            for name in ("observed_at", "received_at", "available_at", "simulated_at"):
                self._validate_time(getattr(envelope, name), name)
            if envelope.source_sequence < 0:
                return self._read_error(operation, "invalid_sequence")
            if (
                operation is BrokerCapabilityId.GET_TRADING_SESSIONS
                and not envelope.session_revision
            ):
                return self._read_error(operation, "exceptional_session_unproven")
            if not (
                envelope.observed_at
                <= envelope.received_at
                <= envelope.available_at
                <= envelope.simulated_at
            ):
                return self._read_error(operation, "future_or_reversed_time")
            if (
                envelope.stale
                or envelope.gap
                or envelope.duplicate
                or envelope.out_of_order
            ):
                states = (
                    name
                    for name in ("stale", "gap", "duplicate", "out_of_order")
                    if getattr(envelope, name)
                )
                return self._read_error(operation, "+".join(states))
            key = (operation.value, repr(tuple(sorted(arguments.items()))))
            previous = self._last_read_sequence.get(key)
            if previous is not None and envelope.source_sequence != previous + 1:
                reason = (
                    "duplicate_or_out_of_order"
                    if envelope.source_sequence <= previous
                    else "missing_sequence"
                )
                return self._read_error(operation, reason)
            self._last_read_sequence[key] = envelope.source_sequence
            return self._result(
                operation,
                data=envelope.payload,
                provider_metadata={
                    "source_sequence": envelope.source_sequence,
                    "observed_at": envelope.observed_at.isoformat(),
                    "received_at": envelope.received_at.isoformat(),
                    "available_at": envelope.available_at.isoformat(),
                    "simulated_at": envelope.simulated_at.isoformat(),
                    "session_revision": envelope.session_revision,
                    "stale": False,
                    "gap": False,
                },
            )
        except Exception as error:  # noqa: BLE001 - public boundary normalization.
            return self._exception_result(operation, error)

    async def _delegate_lifecycle(self, operation: str) -> StandardResponse[object]:
        """Delegate and synchronize one lifecycle operation.

        Args:
            operation: Authority method name.

        Returns:
            Unmodified canonical authority response.
        """
        try:
            response = await getattr(self._authority, operation)()
        except Exception as error:  # noqa: BLE001 - public boundary normalization.
            capability = (
                BrokerCapabilityId.DISCONNECT
                if operation == "finalize_session"
                else BrokerCapabilityId(operation)
            )
            return cast(
                "StandardResponse[object]", self._exception_result(capability, error)
            )
        state = lifecycle_state_from_response(operation, response)
        if state is not None:
            self._state = state
            if (
                operation in {"connect", "reconnect"}
                and state is BrokerConnectionState.READY
            ):
                self._session_generation += 1
        return cast("StandardResponse[object]", response)

    @override
    async def connect(self) -> StandardResponse[None]:
        """Connect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast("StandardResponse[None]", await self._delegate_lifecycle("connect"))

    @override
    async def disconnect(self) -> StandardResponse[None]:
        """Disconnect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]", await self._delegate_lifecycle("disconnect")
        )

    @override
    async def reconnect(self) -> StandardResponse[None]:
        """Reconnect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]", await self._delegate_lifecycle("reconnect")
        )

    @override
    async def is_connected(self) -> StandardResponse[bool]:
        """Read connectivity from the injected authority.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[bool]", await self._delegate_lifecycle("is_connected")
        )

    @override
    async def get_connection_status(self) -> StandardResponse[BrokerConnectionStatus]:
        """Read detailed status from the injected authority.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[BrokerConnectionStatus]",
            await self._delegate_lifecycle("get_connection_status"),
        )

    async def ping(self) -> StandardResponse[None]:
        """Ping the injected authority.

        Returns:
            Canonical authority response, or disconnected failure.
        """
        if self._state is not BrokerConnectionState.READY:
            return self._not_connected(BrokerCapabilityId.PING)
        return cast("StandardResponse[None]", await self._delegate_lifecycle("ping"))

    @override
    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Return the authority-owned deterministic event stream.

        Returns:
            Authority event iterator.
        """
        return self._authority.connection_events()

    async def finalize_session(self) -> StandardResponse[None]:
        """Finalize the run-scoped authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]",
            await self._delegate_lifecycle("finalize_session"),
        )

    @staticmethod
    def _provider_retcode(value: object) -> int:
        """Return an exact integer retcode from one provider-shaped payload.

        Args:
            value: MT5-shaped mapping or record.

        Returns:
            Provider retcode.

        Raises:
            TypeError: If the payload has no valid integer retcode.
        """
        candidate = (
            value.get("retcode")
            if isinstance(value, dict)
            else getattr(value, "retcode", None)
        )
        if isinstance(candidate, bool) or not isinstance(candidate, int):
            raise TypeError("simulation mutation retcode must be an integer")
        return candidate

    def _mutation_error(
        self,
        operation: BrokerCapabilityId,
        code: BrokerErrorCode,
        reason: str,
        *,
        provider_code: str | None = None,
    ) -> StandardResponse[Any]:
        """Return one bounded deterministic mutation error.

        Args:
            operation: Canonical mutation capability.
            code: Verified canonical error classification.
            reason: Bounded failure reason.
            provider_code: Optional verified native retcode.

        Returns:
            Canonical error response.
        """
        error = BrokerError(
            code=code,
            message=f"Simulation {operation.value} rejected",
            provider_code=provider_code,
            capability=operation,
            details={"mutation_state": reason},
        )
        self._last_error = error
        return self._result(operation, error=error)

    @staticmethod
    def _idempotency_key(request: object) -> str | None:
        """Return an explicit caller idempotency identity when supplied.

        Args:
            request: Canonical request or cancel argument tuple.

        Returns:
            Explicit key, or ``None``.
        """
        if isinstance(request, tuple):
            candidate = request[1] if len(request) > 1 else None
        else:
            candidate = getattr(request, "idempotency_key", None) or getattr(
                request, "client_request_id", None
            )
        return candidate if isinstance(candidate, str) and candidate else None

    async def _delegate_mutation(  # noqa: C901, PLR0911, PLR0912
        self,
        operation: BrokerCapabilityId,
        request: object,
        *,
        check_only: bool = False,
        position_result: bool = False,
    ) -> StandardResponse[Any]:
        """Delegate once and classify one provider-shaped authority result.

        Args:
            operation: Canonical mutation capability.
            request: Exact immutable request or cancel argument tuple.
            check_only: Whether to use MT5 order-check mapping.
            position_result: Whether an exact projected position is required.

        Returns:
            Canonical mapped result or deterministic fail-closed error.
        """
        if self._state is not BrokerConnectionState.READY:
            return self._not_connected(operation)
        if (
            self._config.broker_id.value != "sim"
            or self._config.environment.value != "simulation"
        ):
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
                "route_mismatch",
            )
        if (
            isinstance(request, BrokerOrderRequest)
            and request.environment != self._config.environment
        ):
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_REQUEST_INVALID,
                "target_environment_mismatch",
            )
        key = self._idempotency_key(request)
        if key is not None and key in self._mutation_keys:
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_REQUEST_REJECTED,
                "duplicate_idempotency_key",
            )
        mutate = getattr(self._authority, "mutate", None)
        if not callable(mutate):
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
                "authority_mutation_unbound",
            )
        try:
            envelope = await mutate(operation, request)
        except TimeoutError:
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
                "unseeded_timeout",
            )
        except Exception as error:  # noqa: BLE001 - public boundary normalization.
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
                type(error).__name__,
            )
        if not isinstance(envelope, SimulationMutationEnvelope):
            return self._mutation_error(
                operation, BrokerErrorCode.BROKER_RESPONSE_INVALID, "invalid_envelope"
            )
        try:
            self._validate_time(envelope.simulated_at, "simulated_at")
        except ValueError:
            return self._mutation_error(
                operation, BrokerErrorCode.BROKER_RESPONSE_INVALID, "invalid_clock"
            )
        if envelope.seeded_fault:
            return self._mutation_error(
                operation,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
                "phase_20_fault_not_admitted",
            )
        if envelope.request_echo != request:
            return self._mutation_error(
                operation, BrokerErrorCode.BROKER_REQUEST_INVALID, "request_tamper"
            )
        try:
            retcode = self._provider_retcode(envelope.provider_result)
        except TypeError:
            return self._mutation_error(
                operation, BrokerErrorCode.BROKER_RESPONSE_INVALID, "malformed_result"
            )
        verified = {
            0,
            10006,
            10007,
            10008,
            10009,
            10010,
            10013,
            10014,
            10015,
            10016,
            10017,
            10018,
            10019,
            10021,
            10022,
            10025,
            10030,
            10031,
            10032,
            10033,
            10034,
            10035,
            10038,
        }
        if retcode not in verified or (check_only and retcode != 0):
            if retcode not in verified:
                return self._mutation_error(
                    operation,
                    BrokerErrorCode.BROKER_RESPONSE_INVALID,
                    "unverified_retcode",
                    provider_code=str(retcode),
                )
            return self._mutation_error(
                operation,
                _map_error_code(retcode),
                "provider_rejection",
                provider_code=str(retcode),
            )
        if check_only:
            if key is not None:
                self._mutation_keys.add(key)
            return self._result(
                operation, data=_map_order_check(envelope.provider_result)
            )
        mapped = _map_order_result(
            envelope.provider_result, clock=lambda: envelope.simulated_at
        )
        if mapped.outcome not in {"ACCEPTED", "PARTIAL"}:
            return self._mutation_error(
                operation,
                _map_error_code(retcode),
                "provider_rejection",
                provider_code=str(retcode),
            )
        if position_result:
            if not isinstance(envelope.projected_position, BrokerPosition):
                return self._mutation_error(
                    operation,
                    BrokerErrorCode.BROKER_RESPONSE_INVALID,
                    "projected_position_missing",
                )
            data: object = envelope.projected_position
        else:
            data = mapped
        if key is not None:
            self._mutation_keys.add(key)
        return self._result(operation, data=data)

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderCheck]:
        """Validate one exact order through the injected authority.

        Args:
            request: Immutable canonical order request.

        Returns:
            Canonical provider order-check result.
        """
        return cast(
            "StandardResponse[BrokerOrderCheck]",
            await self._delegate_mutation(
                BrokerCapabilityId.CHECK_ORDER, request, check_only=True
            ),
        )

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Place one exact order through the injected authority.

        Args:
            request: Immutable canonical order request.

        Returns:
            Canonical provider acknowledgement.
        """
        return cast(
            "StandardResponse[BrokerOrderResult]",
            await self._delegate_mutation(BrokerCapabilityId.PLACE_ORDER, request),
        )

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Modify one exact order through the injected authority.

        Args:
            request: Immutable canonical order modification.

        Returns:
            Canonical provider acknowledgement.
        """
        return cast(
            "StandardResponse[BrokerOrderResult]",
            await self._delegate_mutation(BrokerCapabilityId.MODIFY_ORDER, request),
        )

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> StandardResponse[BrokerOrderResult]:
        """Cancel one exact order through the injected authority.

        Args:
            order_id: Exact target order identity.
            client_request_id: Optional caller idempotency identity.

        Returns:
            Canonical provider acknowledgement.
        """
        request = (order_id, client_request_id)
        return cast(
            "StandardResponse[BrokerOrderResult]",
            await self._delegate_mutation(BrokerCapabilityId.CANCEL_ORDER, request),
        )

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> StandardResponse[BrokerPosition]:
        """Modify one exact position through the injected authority.

        Args:
            request: Immutable position modification.

        Returns:
            Exact authority-projected post-mutation position.
        """
        return cast(
            "StandardResponse[BrokerPosition]",
            await self._delegate_mutation(
                BrokerCapabilityId.MODIFY_POSITION,
                request,
                position_result=True,
            ),
        )

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Close one exact position through the injected authority.

        Args:
            request: Immutable position close request.

        Returns:
            Canonical provider acknowledgement.
        """
        return cast(
            "StandardResponse[BrokerOrderResult]",
            await self._delegate_mutation(BrokerCapabilityId.CLOSE_POSITION, request),
        )

    async def reduce_position(
        self, request: BrokerPositionReductionRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Reduce one exact position through the injected authority.

        Args:
            request: Immutable position reduction request.

        Returns:
            Canonical provider acknowledgement.
        """
        return cast(
            "StandardResponse[BrokerOrderResult]",
            await self._delegate_mutation(BrokerCapabilityId.REDUCE_POSITION, request),
        )


_ADMITTED_READS = frozenset(
    {
        BrokerCapabilityId.GET_SYMBOLS,
        BrokerCapabilityId.GET_SYMBOL_INFO,
        BrokerCapabilityId.GET_PROVIDER_SPECIFICATION,
        BrokerCapabilityId.GET_TRADING_SESSIONS,
        BrokerCapabilityId.GET_QUOTE,
        BrokerCapabilityId.GET_SPREAD,
        BrokerCapabilityId.GET_TICKS,
        BrokerCapabilityId.GET_HISTORICAL_BARS,
        BrokerCapabilityId.GET_PERMISSIONS,
        BrokerCapabilityId.GET_ACCOUNT_INFO,
        BrokerCapabilityId.GET_BALANCES,
        BrokerCapabilityId.GET_POSITIONS,
        BrokerCapabilityId.GET_POSITION,
        BrokerCapabilityId.GET_ORDERS,
        BrokerCapabilityId.GET_ORDER,
        BrokerCapabilityId.LIST_ORDER_HISTORY,
        BrokerCapabilityId.LIST_DEAL_HISTORY,
        BrokerCapabilityId.GET_DEAL,
        BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS,
    }
)


def _make_read_method(
    operation: BrokerCapabilityId,
) -> Callable[..., Awaitable[StandardResponse[Any]]]:
    """Create one protocol-signature-preserving read delegate.

    Args:
        operation: Canonical admitted read.

    Returns:
        Asynchronous adapter method.
    """
    protocol_method = getattr(BrokerAdapter, operation.value)
    signature = inspect.signature(protocol_method)

    async def _method(
        self: SimulationBrokerAdapter, *args: object, **kwargs: object
    ) -> StandardResponse[Any]:
        """Delegate one authority-owned simulation read.

        Args:
            self: Simulation adapter receiving the read.
            *args: Positional canonical operation arguments.
            **kwargs: Keyword canonical operation arguments.

        Returns:
            Exact authority payload or a fail-closed canonical error.
        """
        bound = signature.bind(self, *args, **kwargs)
        arguments = dict(bound.arguments)
        arguments.pop("self", None)
        return await self._delegate_read(operation, arguments)

    _method.__name__ = operation.value
    _method.__annotations__ = dict(protocol_method.__annotations__)
    _method.__signature__ = signature  # type: ignore[attr-defined]
    return _method


for _read_operation in _ADMITTED_READS:
    setattr(
        SimulationBrokerAdapter,
        _read_operation.value,
        _make_read_method(_read_operation),
    )


__all__ = ("SimulationBrokerAdapter",)
