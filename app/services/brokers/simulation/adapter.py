"""Private socket-free adapter backed by an injected authority port."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast, override

from app.services.brokers._shared.base import _UnsupportedAdapterBase
from app.services.brokers.canonical_contracts import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerConnectionStatus,
    StandardResponse,
)
from app.services.brokers.canonical_contracts.enums import BrokerErrorCode
from app.services.brokers.canonical_contracts.models import BrokerError
from app.services.brokers.canonical_contracts.protocols import BrokerAdapter
from app.services.brokers.simulation.contracts import SimulationReadEnvelope
from app.services.brokers.simulation.lifecycle import lifecycle_state_from_response

if TYPE_CHECKING:
    from app.services.brokers.simulation.contracts import SimulationAuthorityPort


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

    async def _delegate_read(  # noqa: C901, PLR0911 - explicit evidence failures.
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
        read = getattr(self._authority, "read", None)
        if not callable(read):
            return self._read_error(operation, "authority_read_unbound")
        try:
            envelope = await read(operation, MappingProxyType(dict(arguments)))
            if not isinstance(envelope, SimulationReadEnvelope):
                return self._read_error(operation, "invalid_envelope")
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
