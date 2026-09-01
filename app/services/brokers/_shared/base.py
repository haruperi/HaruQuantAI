"""Shared invocation-local lifecycle and fail-closed adapter runtime."""

from __future__ import annotations

# ruff: noqa: BLE001, C901 - canonical public-boundary normalization.
import asyncio
import contextvars
import functools
from collections.abc import AsyncIterator, Mapping
from dataclasses import replace
from typing import Any, Literal, cast, override

from app.composition.logging import get_logger
from app.contracts.common.models import get_execution_ms
from app.kernel.identity import generate_id
from app.services.brokers._shared.errors import (
    _CircuitOpenError,
    _ProviderResponseError,
    _RateLimitedError,
    _RequestValidationError,
)
from app.services.brokers.canonical_contracts.enums import (
    BrokerCapabilityId,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.canonical_contracts.models import (
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionStatus,
    BrokerError,
    BrokerFeatureFlags,
)
from app.services.brokers.canonical_contracts.responses import (
    StandardResponse,
    broker_start_time,
    build_broker_response,
)
from app.services.brokers.canonical_contracts.unsupported import _utc_now

logger = get_logger(__name__)


class _UnsupportedAdapterBase:
    """Lifecycle and fail-closed defaults shared by concrete adapters."""

    ADAPTER_VERSION = "1.0.0"
    _ENFORCE_DECLARED_AVAILABILITY = True
    _LOCAL_FAIL_SAFE_OPERATIONS = frozenset(
        {
            BrokerCapabilityId.DISCONNECT,
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            BrokerCapabilityId.GET_LAST_ERROR,
            BrokerCapabilityId.CONNECTION_EVENTS,
            BrokerCapabilityId.GET_FEATURE_FLAGS,
            BrokerCapabilityId.SUPPORTS,
            BrokerCapabilityId.UNSUBSCRIBE,
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
        }
    )
    _MUTATION_OPERATIONS = frozenset(
        {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
            BrokerCapabilityId.REPLACE_ORDER,
            BrokerCapabilityId.ATTACH_PROTECTION,
            BrokerCapabilityId.REDUCE_POSITION,
        }
    )

    _SESSION_EXEMPT_OPERATIONS = frozenset(
        {
            BrokerCapabilityId.CONNECT,
            BrokerCapabilityId.DISCONNECT,
            BrokerCapabilityId.RECONNECT,
            BrokerCapabilityId.IS_CONNECTED,
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            BrokerCapabilityId.GET_LAST_ERROR,
            BrokerCapabilityId.CONNECTION_EVENTS,
            BrokerCapabilityId.GET_FEATURE_FLAGS,
            BrokerCapabilityId.SUPPORTS,
        }
    )

    def __init__(
        self,
        config: BrokerConnectionConfig,
    ) -> None:
        """Initialize an adapter from Brokers-owned capability policy.

        Args:
            config: Immutable provider connection configuration.

        Raises:
            ValueError: If the internal capability catalogue response is
                unavailable.
        """
        from app.services.brokers.capabilities.matrix import (
            get_broker_capability_catalogue,
        )

        self._config = config
        catalogue_response = get_broker_capability_catalogue()
        if catalogue_response.status != "success" or catalogue_response.data is None:
            raise ValueError("broker capability catalogue is unavailable")
        catalogue = catalogue_response.data[config.broker_id]
        self._capabilities = {
            item.capability: (
                replace(
                    item,
                    availability="UNAVAILABLE",
                    reason="Mutation capability is released only for demo environments",
                )
                if item.capability in self._MUTATION_OPERATIONS
                and item.availability == "AVAILABLE"
                and config.environment is not BrokerEnvironment.DEMO
                and config.broker_id is not BrokerId.SIM
                else item
            )
            for item in catalogue
        }
        self._state = BrokerConnectionState.DISCONNECTED
        self._session_generation = 0
        self._last_error: BrokerError | None = None
        self._event_queue: asyncio.Queue[BrokerConnectionEvent] = asyncio.Queue(
            config.stream_buffer_size + 1
        )
        self._event_overflowed = False
        # Wall time of the operation currently resolving at the public
        # boundary, measured by `__getattribute__` and consumed once by
        # `_result`. Provider-network time is reported separately by the
        # transports through `_record_provider_latency`.
        self._call_timing: contextvars.ContextVar[tuple[int, float | None] | None] = (
            contextvars.ContextVar(
                f"broker_call_timing_{id(self)}",
                default=None,
            )
        )

    @property
    def contract_version(self) -> Literal["v1"]:
        """Return the implemented broker boundary version.

        Returns:
            Literal['v1']: The operation result.
        """
        return "v1"

    @property
    def schema_id(self) -> Literal["brokers.adapter.v1"]:
        """Return the composite adapter schema identifier.

        Returns:
            Literal['brokers.adapter.v1']: The operation result.
        """
        return "brokers.adapter.v1"

    @override
    def __getattribute__(self, name: str) -> Any:
        """Enforce declared availability and session state before provider access.

        Args:
            name: Attribute name requested by the caller.

        Returns:
            The declared attribute or a fail-closed error operation.
        """
        operation: BrokerCapabilityId | None = None
        if not name.startswith("_"):
            try:
                operation = BrokerCapabilityId(name)
            except ValueError:
                operation = None
            if operation is not None:
                enforce = object.__getattribute__(
                    self, "_ENFORCE_DECLARED_AVAILABILITY"
                )
                local = object.__getattribute__(self, "_LOCAL_FAIL_SAFE_OPERATIONS")
                capabilities = object.__getattribute__(self, "_capabilities")
                declared = capabilities.get(operation)
                if (
                    enforce
                    and operation not in local
                    and (declared is None or declared.availability == "UNAVAILABLE")
                ):

                    async def _blocked(
                        *args: object, **kwargs: object
                    ) -> StandardResponse[Any]:
                        """Return the declared unavailable capability result.

                        Args:
                            *args: Value supplied to the operation.
                            **kwargs: Value supplied to the operation.

                        Returns:
                            StandardResponse[Any]: The operation result.
                        """
                        del args, kwargs
                        return self._unsupported(operation)

                    return _blocked

                exempt = object.__getattribute__(self, "_SESSION_EXEMPT_OPERATIONS")
                state = object.__getattribute__(self, "_state")
                if operation not in exempt and state != BrokerConnectionState.READY:

                    async def _not_ready(
                        *args: object, **kwargs: object
                    ) -> StandardResponse[Any]:
                        """Return the disconnected session result.

                        Args:
                            *args: Value supplied to the operation.
                            **kwargs: Value supplied to the operation.

                        Returns:
                            StandardResponse[Any]: The operation result.
                        """
                        del args, kwargs
                        return self._not_connected(operation)

                    return _not_ready

        attribute = object.__getattribute__(self, name)
        if operation is None or operation == BrokerCapabilityId.CONNECTION_EVENTS:
            return attribute
        if not callable(attribute):
            return attribute

        @functools.wraps(attribute)
        async def _guarded(*args: object, **kwargs: object) -> StandardResponse[Any]:
            """Normalize an adapter call into a canonical result.

            Args:
                *args: Value supplied to the operation.
                **kwargs: Value supplied to the operation.

            Returns:
                The canonical operation result.

            Raises:
                asyncio.CancelledError: If caller cancels the operation.
            """
            timing = object.__getattribute__(self, "_call_timing")
            token = timing.set((broker_start_time(), None))
            try:
                result = await attribute(*args, **kwargs)
                return cast("StandardResponse[Any]", result)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                return self._exception_result(operation, error)
            finally:
                timing.reset(token)

        return _guarded

    def _elapsed_ms(self) -> float:
        """Return elapsed milliseconds for the active invocation context.

        Returns:
            Elapsed time in milliseconds.
        """
        context = self._call_timing.get()
        if context is None:
            return 0.0
        started, _ = context
        elapsed: float = get_execution_ms(started)
        return elapsed

    def _result[T](
        self,
        operation: BrokerCapabilityId,
        *,
        data: T | None = None,
        error: BrokerError | None = None,
        request_id: str | None = None,
        provider_metadata: Mapping[str, object] | None = None,
    ) -> StandardResponse[T]:
        """Build and log one canonical adapter result.

        Total latency is the measured wall time of the public call. Provider
        latency is whatever the transports reported for this call, and adapter
        overhead is the remainder, so the two are always separable.

        Args:
            operation: Value supplied to the operation.
            data: Value supplied to the operation.
            error: Value supplied to the operation.
            request_id: Value supplied to the operation.
            provider_metadata: Value supplied to the operation.

        Returns:
            The canonical result envelope.
        """
        context = self._call_timing.get()
        started = context[0] if context is not None else broker_start_time()
        provider_latency_ms = context[1] if context is not None else None
        result = build_broker_response(
            broker=self._config.broker_id,
            operation=operation,
            request_id=request_id or generate_id("req"),
            timestamp=_utc_now(),
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            start_time=started,
            data=data,
            error=error,
            provider_metadata=provider_metadata or {},
            provider_latency_ms=provider_latency_ms,
        )
        bound = logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            operation=operation.value,
            request_id=result.metadata.request_id,
            result=result.status,
            provider_code=error.code.value if error is not None else None,
            latency_ms=result.metadata.execution_ms,
        )
        if error is not None:
            bound.warning("Broker operation returned canonical error")
        else:
            bound.info("Broker operation completed")
        return result

    def _record_provider_latency(self, latency_ms: float) -> None:
        """Record provider network latency measured by underlying transport.

        Args:
            latency_ms: Provider round-trip time in milliseconds.
        """
        context = self._call_timing.get()
        if context is not None:
            started, current = context
            accumulated = float(latency_ms) + (current or 0.0)
            self._call_timing.set((started, accumulated))

    def _propagated_error[T](
        self,
        operation: BrokerCapabilityId,
        response: StandardResponse[Any],
    ) -> StandardResponse[T]:
        """Re-scope one failed nested Broker response to the caller operation.

        Args:
            operation: Public Broker operation receiving the nested failure.
            response: Failed response from a nested Broker operation.

        Returns:
            Failed response retaining all available canonical error evidence.

        Raises:
            ValueError: If the supplied response is not an error response.
        """
        standard_error = response.error
        if standard_error is None:
            raise ValueError("nested Broker response does not contain an error")
        details = standard_error.details
        raw_capability = details.get("capability")
        capability = None
        if isinstance(raw_capability, str):
            try:
                capability = BrokerCapabilityId(raw_capability)
            except ValueError:
                capability = None
        raw_legacy_details = details.get("legacy_details")
        legacy_details = (
            raw_legacy_details if isinstance(raw_legacy_details, Mapping) else {}
        )
        try:
            code = BrokerErrorCode(standard_error.code)
        except ValueError:
            code = BrokerErrorCode.BROKER_RESPONSE_INVALID
        raw_provider_code = details.get("provider_code")
        raw_provider_message = details.get("provider_message")
        canonical = BrokerError(
            code=code,
            message=response.message,
            retryable=details.get("retryable") is True,
            provider_code=(
                raw_provider_code if isinstance(raw_provider_code, str) else None
            ),
            provider_message=(
                raw_provider_message if isinstance(raw_provider_message, str) else None
            ),
            capability=capability,
            details=legacy_details,
        )
        self._last_error = canonical
        return self._result(operation, error=canonical)

    async def _transition(
        self,
        state: BrokerConnectionState,
        *,
        reason: str | None = None,
        resynchronization_required: bool = False,
    ) -> None:
        """Handle transition.

        Args:
            state: Value supplied to the operation.
            reason: Value supplied to the operation.
            resynchronization_required: Value supplied to the operation.
        """
        if state == self._state:
            return
        event = BrokerConnectionEvent(
            previous_state=self._state,
            new_state=state,
            timestamp=_utc_now(),
            session_generation=self._session_generation,
            reason=reason,
            resynchronization_required=resynchronization_required,
        )
        self._state = state
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            previous_state=event.previous_state.value,
            new_state=state.value,
            session_generation=self._session_generation,
            reason=reason,
            resynchronization_required=resynchronization_required,
        ).info("Broker connection state transition")
        if self._event_queue.qsize() < self._config.stream_buffer_size:
            self._event_queue.put_nowait(event)
        else:
            self._state = BrokerConnectionState.DEGRADED
            if not self._event_overflowed:
                self._event_overflowed = True
                self._event_queue.put_nowait(
                    BrokerConnectionEvent(
                        previous_state=event.previous_state,
                        new_state=BrokerConnectionState.DEGRADED,
                        timestamp=_utc_now(),
                        session_generation=self._session_generation,
                        reason="connection_event_backpressure",
                        resynchronization_required=True,
                    )
                )
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                new_state=BrokerConnectionState.DEGRADED.value,
            ).warning("Connection event buffer overflow; adapter degraded")

    async def connect(self) -> StandardResponse[None]:
        """Fail closed unless a provider verifies a real session.

        Returns:
            A canonical unsupported connection result.
        """
        return self._unsupported(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> StandardResponse[None]:
        """Idempotently close adapter-local state.

        Returns:
            A canonical successful disconnection result.
        """
        if self._state != BrokerConnectionState.DISCONNECTED:
            await self._transition(BrokerConnectionState.CLOSING)
            await self._transition(BrokerConnectionState.DISCONNECTED)
        return self._result(BrokerCapabilityId.DISCONNECT)

    async def reconnect(self) -> StandardResponse[None]:
        """Reconnect the same session without replaying an operation.

        Returns:
            The canonical result of the new connection attempt.
        """
        await self.disconnect()
        return await self.connect()

    async def is_connected(self) -> StandardResponse[bool]:
        """Return conservative locally retained session evidence.

        Provider adapters override this method when current connectivity can be
        verified. The shared default never upgrades non-provider evidence.

        Returns:
            A canonical result that is true only for a retained verified session.
        """
        return self._result(
            BrokerCapabilityId.IS_CONNECTED,
            data=self._state == BrokerConnectionState.READY,
        )

    async def get_connection_status(
        self,
    ) -> StandardResponse[BrokerConnectionStatus]:
        """Return detailed fail-closed session state.

        Returns:
            StandardResponse[BrokerConnectionStatus]: The operation result.
        """
        return self._result(
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            data=BrokerConnectionStatus(
                state=self._state,
                transport_connected=self._state == BrokerConnectionState.READY,
                environment=self._config.environment,
                session_generation=self._session_generation,
                observed_at=_utc_now(),
                application_authenticated=None,
                account_authenticated=None,
                trading_permitted=None,
                subscriptions_ready=None,
            ),
        )

    async def get_last_error(self) -> StandardResponse[BrokerError | None]:
        """Return the latest redacted non-authoritative error.

        Returns:
            StandardResponse[BrokerError | None]: The operation result.
        """
        return self._result(BrokerCapabilityId.GET_LAST_ERROR, data=self._last_error)

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Return bounded lifecycle events for this adapter instance.

        Returns:
            An asynchronous iterator over connection lifecycle events.
        """

        async def _events() -> AsyncIterator[BrokerConnectionEvent]:
            """Yield adapter lifecycle events in publication order.

            Yields:
                The next connection lifecycle event.
            """
            while True:
                yield await self._event_queue.get()

        return _events()

    async def get_feature_flags(self) -> StandardResponse[BrokerFeatureFlags]:
        """Return the complete catalogue supplied by the capability matrix.

        Returns:
            StandardResponse[BrokerFeatureFlags]: The operation result.
        """
        flags = BrokerFeatureFlags(
            broker_id=self._config.broker_id,
            environment=self._config.environment,
            generated_at=_utc_now(),
            capabilities=self._capabilities,
            adapter_version=self.ADAPTER_VERSION,
            account_reference_redacted=(
                "***" if self._config.account_reference is not None else None
            ),
        )
        return self._result(BrokerCapabilityId.GET_FEATURE_FLAGS, data=flags)

    async def supports(self, capability: BrokerCapabilityId) -> StandardResponse[bool]:
        """Answer from the static declaration without probing a provider.

        Args:
            capability: Capability whose declared availability is requested.

        Returns:
            A canonical result containing declared support status.
        """
        declared = self._capabilities[capability]
        return self._result(
            BrokerCapabilityId.SUPPORTS,
            data=declared.availability in {"AVAILABLE", "DEGRADED"},
        )

    def _not_connected[T](self, operation: BrokerCapabilityId) -> StandardResponse[T]:
        """Return and record a deterministic BROKER_NOT_CONNECTED result.

        Args:
            operation: Value supplied to the operation.

        Returns:
            The canonical disconnected error result.
        """
        self._elapsed_ms()
        error = BrokerError(
            code=BrokerErrorCode.BROKER_NOT_CONNECTED,
            message=(
                f"Broker operation {operation.value} requires an active "
                f"verified session (state={self._state.value})"
            ),
            retryable=False,
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)

    def _unsupported[T](self, operation: BrokerCapabilityId) -> StandardResponse[T]:
        """Return and record a deterministic unsupported result.

        No provider call is made, so the gate consumes and discards any timing
        started at the public boundary rather than attributing it to a later
        operation.

        Args:
            operation: Value supplied to the operation.

        Returns:
            The canonical unsupported result.
        """
        self._elapsed_ms()
        error = BrokerError(
            code=BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
            message=f"Broker operation {operation.value} is unavailable",
            retryable=False,
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)

    def _exception_result[T](
        self,
        operation: BrokerCapabilityId,
        error: BaseException,
    ) -> StandardResponse[T]:
        """Translate one public-boundary failure to a canonical result.

        Args:
            operation: Canonical operation that failed.
            error: Bounded exception raised by validation or provider access.

        Returns:
            A redacted canonical failure result.
        """
        if isinstance(error, _CircuitOpenError):
            code = BrokerErrorCode.BROKER_CIRCUIT_OPEN
        elif isinstance(error, _RateLimitedError):
            code = BrokerErrorCode.BROKER_RATE_LIMITED
        elif operation in self._MUTATION_OPERATIONS:
            # A mutation fails closed. Only pre-transmission structural
            # validation may claim the request never reached the provider;
            # every other failure is a possible transmission and must be
            # reported as an unknown outcome so the caller reconciles instead
            # of assuming the mutation did not happen.
            code = (
                BrokerErrorCode.BROKER_REQUEST_INVALID
                if isinstance(error, _RequestValidationError)
                else BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
            )
        elif isinstance(error, TimeoutError):
            code = BrokerErrorCode.BROKER_TIMEOUT
        elif isinstance(error, (OSError, ConnectionError)):
            code = BrokerErrorCode.BROKER_CONNECTION_LOST
        elif isinstance(error, ImportError):
            code = BrokerErrorCode.BROKER_DEPENDENCY_MISSING
        elif isinstance(error, _ProviderResponseError):
            code = BrokerErrorCode.BROKER_RESPONSE_INVALID
        elif isinstance(error, ValueError):
            code = BrokerErrorCode.BROKER_REQUEST_INVALID
        else:
            code = BrokerErrorCode.BROKER_RESPONSE_INVALID
        canonical = BrokerError(
            code=code,
            message=f"Broker {operation.value} failed",
            retryable=False,
            provider_message=type(error).__name__,
            capability=operation,
        )
        self._last_error = canonical
        return self._result(operation, error=canonical)
