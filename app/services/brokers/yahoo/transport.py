"""Bounded Yahoo direct-channel transport without direct pandas imports."""

from __future__ import annotations

# ruff: noqa: ANN401 - yfinance returns a transitive table without a stable type.
import asyncio
import importlib
import logging
import time
from collections.abc import Callable
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.yahoo.config import YahooConfig

logger = logging.getLogger(__name__)


class _CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class _CircuitOpenError(ConnectionError):
    """Transport circuit is open."""


class _YahooCircuitBreaker:
    """Deterministic closed/open/half-open transport circuit."""

    def __init__(
        self,
        *,
        failure_threshold: int,
        recovery_timeout_sec: float,
        half_open_max_calls: int,
    ) -> None:
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
        return self._state.value

    async def before_call(self) -> bool:
        """Return True if call is allowed, False if circuit is open."""
        async with self._lock:
            if self._state == _CircuitState.OPEN:
                opened_at = self._opened_at
                elapsed = (
                    time.monotonic() - opened_at
                    if opened_at is not None
                    else self._recovery_timeout_sec
                )
                if opened_at is None or elapsed < self._recovery_timeout_sec:
                    return False
                self._state = _CircuitState.HALF_OPEN
                self._half_open_in_flight = 0
                self._half_open_successes = 0
                logger.info("Yahoo transport circuit entering half-open probe state")
            if self._state == _CircuitState.HALF_OPEN:
                if self._half_open_in_flight >= self._half_open_max_calls:
                    return False
                self._half_open_in_flight += 1
            return True

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == _CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._half_open_successes += 1
                if self._half_open_successes >= self._half_open_max_calls:
                    self._state = _CircuitState.CLOSED
                    self._opened_at = None
                    self._consecutive_failures = 0
                    self._half_open_in_flight = 0
                    self._half_open_successes = 0
                    logger.info("Yahoo transport circuit closed; resumed")
            elif self._state == _CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def record_failure(self) -> None:
        async with self._lock:
            if self._state == _CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._state = _CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._half_open_in_flight = 0
                self._half_open_successes = 0
                logger.warning("Yahoo transport circuit opened on probe failure")
                return
            if self._state == _CircuitState.CLOSED:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._failure_threshold:
                    self._state = _CircuitState.OPEN
                    self._opened_at = time.monotonic()
                    self._half_open_in_flight = 0
                    self._half_open_successes = 0
                    logger.warning(
                        "Yahoo transport circuit opened; provider calls fail closed"
                    )


class _YahooTransport:
    """Run one bounded yfinance history call off the event loop."""

    def __init__(
        self,
        config: YahooConfig | Any,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        self._config = config
        self._latency_sink = latency_sink
        failure_threshold = getattr(config, "circuit_failure_threshold", 5)
        recovery_timeout_sec = getattr(config, "circuit_recovery_timeout_sec", 30.0)
        half_open_max_calls = getattr(config, "circuit_half_open_max_calls", 1)
        self._circuit = _YahooCircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout_sec=recovery_timeout_sec,
            half_open_max_calls=half_open_max_calls,
        )

    async def history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: object | None = None,
        end: object | None = None,
    ) -> Any:
        """Return the public table object produced by one yfinance call.

        Args:
            symbol: Provider symbol string.
            timeframe: Interval string.
            start: Start date or timestamp.
            end: End date or timestamp.

        Returns:
            Exact public table produced by yfinance.

        Raises:
            _CircuitOpenError: If transport circuit is open.
            OSError: If provider transport fails.
            TimeoutError: If request times out.
        """
        admitted = await self._circuit.before_call()
        if not admitted:
            raise _CircuitOpenError(
                "BROKER_CIRCUIT_OPEN: Yahoo transport circuit is open"
            )

        timeout_sec = getattr(self._config, "request_timeout_sec", 30.0)

        def _history() -> Any:
            yfinance = importlib.import_module("yfinance")
            ticker = yfinance.Ticker(symbol)
            return ticker.history(
                interval=timeframe,
                start=start,
                end=end,
                timeout=timeout_sec,
            )

        started = time.perf_counter()
        try:
            value = await asyncio.wait_for(
                asyncio.to_thread(_history), timeout=timeout_sec
            )
        except TimeoutError, OSError:
            await self._circuit.record_failure()
            logger.warning("Yahoo history transport call failed for symbol=%s", symbol)
            raise
        finally:
            if self._latency_sink is not None:
                self._latency_sink((time.perf_counter() - started) * 1000.0)
        await self._circuit.record_success()
        logger.info("Yahoo history transport call completed for symbol=%s", symbol)
        return value
