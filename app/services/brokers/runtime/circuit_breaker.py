"""Adapter-local transport circuit breaker."""

import asyncio
import time
from enum import StrEnum

from app.services.brokers.contracts import BrokerErrorCode
from app.utils import logger


class _CircuitState(StrEnum):
    """Internal circuit states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


_QUALIFYING_FAILURES = frozenset(
    {
        BrokerErrorCode.BROKER_CONNECTION_FAILED,
        BrokerErrorCode.BROKER_CONNECTION_LOST,
        BrokerErrorCode.BROKER_TIMEOUT,
        BrokerErrorCode.BROKER_PROVIDER_ERROR,
        BrokerErrorCode.BROKER_UNKNOWN_OUTCOME,
    }
)


class _TransportCircuitBreaker:
    """Deterministic closed/open/half-open transport circuit."""

    def __init__(
        self,
        *,
        failure_threshold: int,
        recovery_timeout_sec: float,
        half_open_max_calls: int,
    ) -> None:
        """Initialize the _TransportCircuitBreaker instance.

        Args:
            failure_threshold: Value supplied to the operation.
            recovery_timeout_sec: Value supplied to the operation.
            half_open_max_calls: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if min(failure_threshold, recovery_timeout_sec, half_open_max_calls) <= 0:
            raise ValueError("circuit bounds must be positive")
        self._failure_threshold = failure_threshold
        self._recovery_timeout_sec = recovery_timeout_sec
        self._half_open_max_calls = half_open_max_calls
        self._state = _CircuitState.CLOSED
        self._consecutive_failures = 0
        self._half_open_in_flight = 0
        self._half_open_successes = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        """Return the current serialized circuit state."""
        return self._state.value

    async def before_call(self) -> BrokerErrorCode | None:
        """Admit a call or return the fail-closed circuit error code.

        Returns:
            ``None`` when admitted, otherwise the open-circuit error code.
        """
        async with self._lock:
            if self._state == _CircuitState.OPEN:
                opened_at = self._opened_at
                if opened_at is None:
                    self._open()
                    return BrokerErrorCode.BROKER_CIRCUIT_OPEN
                if time.monotonic() - opened_at < self._recovery_timeout_sec:
                    return BrokerErrorCode.BROKER_CIRCUIT_OPEN
                self._state = _CircuitState.HALF_OPEN
                self._half_open_in_flight = 0
                self._half_open_successes = 0
                logger.bind(
                    component="transport_circuit",
                    transition="open_to_half_open",
                ).info("Transport circuit entering half-open probe state")
            if self._state == _CircuitState.HALF_OPEN:
                if self._half_open_in_flight >= self._half_open_max_calls:
                    return BrokerErrorCode.BROKER_CIRCUIT_OPEN
                self._half_open_in_flight += 1
            return None

    async def record_success(self) -> None:
        """Record one completed provider call or half-open probe."""
        async with self._lock:
            if self._state == _CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._half_open_successes += 1
                if self._half_open_successes >= self._half_open_max_calls:
                    self._close()
            elif self._state == _CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def record_failure(self, code: BrokerErrorCode) -> None:
        """Record a failure, counting only transport-qualified outcomes."""
        async with self._lock:
            if self._state == _CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
            if code not in _QUALIFYING_FAILURES:
                return
            if self._state == _CircuitState.HALF_OPEN:
                self._open()
                return
            if self._state == _CircuitState.CLOSED:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._failure_threshold:
                    self._open()

    def _open(self) -> None:
        """Handle open."""
        self._state = _CircuitState.OPEN
        self._opened_at = time.monotonic()
        self._half_open_in_flight = 0
        self._half_open_successes = 0
        logger.bind(
            component="transport_circuit",
            transition="open",
            consecutive_failures=self._consecutive_failures,
            failure_threshold=self._failure_threshold,
        ).warning("Transport circuit opened; provider calls fail closed")

    def _close(self) -> None:
        """Handle close."""
        self._state = _CircuitState.CLOSED
        self._opened_at = None
        self._consecutive_failures = 0
        self._half_open_in_flight = 0
        self._half_open_successes = 0
        logger.bind(
            component="transport_circuit",
            transition="close",
        ).info("Transport circuit closed; provider calls resumed")
