# mypy: ignore-errors
"""Bounded Dukascopy direct-channel tick transport."""

from __future__ import annotations

# ruff: noqa: ANN401, S310 - URL is constructed from a fixed HTTPS provider base.
import asyncio
import hashlib
import json
import logging
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, cast

from app.services.brokers.dukascopy._legacy_types import (
    _CircuitOpenError,
    _ProviderResponseError,
)
from app.services.brokers.dukascopy.instruments import _web_symbol

if TYPE_CHECKING:
    from app.services.brokers.dukascopy.config import DukascopyConfig

logger = logging.getLogger(__name__)


class _CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class _DukascopyCircuitBreaker:
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

    async def before_call(self) -> str | None:
        """Return None if call is allowed, or state reason if circuit is open."""
        async with self._lock:
            if self._state == _CircuitState.OPEN:
                opened_at = self._opened_at
                elapsed = (
                    time.monotonic() - opened_at
                    if opened_at is not None
                    else self._recovery_timeout_sec
                )
                if opened_at is None or elapsed < self._recovery_timeout_sec:
                    return self._state.value
                self._state = _CircuitState.HALF_OPEN
                self._half_open_in_flight = 0
                self._half_open_successes = 0
                logger.info(
                    "Dukascopy transport circuit entering half-open probe state"
                )
            if self._state == _CircuitState.HALF_OPEN:
                if self._half_open_in_flight >= self._half_open_max_calls:
                    return self._state.value
                self._half_open_in_flight += 1
            return None

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
                    logger.info("Dukascopy transport circuit closed; resumed")
            elif self._state == _CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def record_failure(self, _code: object = None) -> None:
        async with self._lock:
            if self._state == _CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._state = _CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._half_open_in_flight = 0
                self._half_open_successes = 0
                logger.warning("Dukascopy transport circuit opened on probe failure")
                return
            if self._state == _CircuitState.CLOSED:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._failure_threshold:
                    self._state = _CircuitState.OPEN
                    self._opened_at = time.monotonic()
                    self._half_open_in_flight = 0
                    self._half_open_successes = 0
                    logger.warning(
                        "Dukascopy transport circuit opened; provider calls fail closed"
                    )


class _DukascopyTransport:
    """Retrieve bounded genuine ticks from Dukascopy's public web chart."""

    _BASE_URL = "https://freeserv.dukascopy.com/2.0/index.php"

    def __init__(
        self,
        config: DukascopyConfig | Any,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the tick transport.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for provider latency measurements.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._circuit = _DukascopyCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    @staticmethod
    def _parse_page(body: str, callback: str) -> tuple[tuple[object, ...], ...]:
        """Parse and structurally validate one JSONP tick page.

        Args:
            body: Provider response text.
            callback: Exact callback requested from the provider.

        Returns:
            Immutable raw provider rows.

        Raises:
            _ProviderResponseError: If the JSONP envelope or page is invalid.
        """
        prefix = f"{callback}("
        if not body.startswith(prefix) or not body.endswith(");"):
            raise _ProviderResponseError("invalid Dukascopy tick JSONP envelope")
        try:
            decoded = json.loads(body.removeprefix(prefix).removesuffix(");"))
        except json.JSONDecodeError as error:
            raise _ProviderResponseError("invalid Dukascopy tick JSON") from error
        if not isinstance(decoded, list):
            raise _ProviderResponseError("invalid Dukascopy tick page")
        if any(not isinstance(row, list) for row in decoded):
            raise _ProviderResponseError("invalid Dukascopy tick row")
        return tuple(tuple(row) for row in decoded)

    async def get_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> tuple[tuple[object, ...], ...]:
        """Retrieve one caller-bounded page of genuine provider ticks.

        Args:
            symbol: Exact canonical Dukascopy symbol.
            start: Inclusive timezone-aware range boundary.
            end: Exclusive timezone-aware range boundary.
            limit: Positive maximum returned rows.

        Returns:
            Raw provider tick rows within the requested range.

        Raises:
            ValueError: If the range or limit is invalid.
            _CircuitOpenError: If the transport circuit rejects the request.
            OSError: If provider transport fails.
            TimeoutError: If the configured request bound is exceeded.
            UnicodeError: If provider text cannot be decoded.
            _ProviderResponseError: If provider evidence is malformed.
        """
        if (
            start.tzinfo is None
            or start.utcoffset() is None
            or end.tzinfo is None
            or end.utcoffset() is None
            or start >= end
            or limit <= 0
        ):
            raise ValueError("ordered tick range and positive limit are required")
        provider_symbol = _web_symbol(symbol)
        cursor = int(start.timestamp() * 1000)
        callback = (
            "_callbacks____"
            + hashlib.sha256(
                f"{provider_symbol}|TICK|{cursor}|{limit}".encode()
            ).hexdigest()[:12]
        )
        query = urllib.parse.urlencode(
            {
                "path": "chart/json3",
                "splits": "true",
                "stocks": "true",
                "time_direction": "N",
                "jsonp": callback,
                "last_update": str(cursor),
                "offer_side": "B",
                "instrument": provider_symbol,
                "interval": "TICK",
                "limit": str(limit),
            }
        )
        url = f"{self._BASE_URL}?{query}"
        if await self._circuit.before_call() is not None:
            raise _CircuitOpenError("Dukascopy tick circuit is open")

        def _read() -> str:
            """Read one bounded provider response.

            Returns:
                UTF-8 provider response text.
            """
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/135.0.0.0 Safari/537.36"
                    ),
                    "Referer": "https://freeserv.dukascopy.com/2.0/?path=chart/index",
                },
            )
            with urllib.request.urlopen(
                request,
                timeout=self._config.request_timeout_sec,
            ) as response:
                return cast("bytes", response.read()).decode("utf-8")

        started = time.perf_counter()
        try:
            body = await asyncio.wait_for(
                asyncio.to_thread(_read),
                timeout=self._config.request_timeout_sec,
            )
            rows = self._parse_page(body, callback)
        except TimeoutError, OSError, UnicodeError, _ProviderResponseError:
            await self._circuit.record_failure()
            logger.warning("Dukascopy tick transport call failed for symbol %s", symbol)
            raise
        finally:
            if self._latency_sink is not None:
                self._latency_sink((time.perf_counter() - started) * 1000.0)
        await self._circuit.record_success()
        end_ms = int(end.timestamp() * 1000)
        bounded = tuple(
            row
            for row in rows
            if row and isinstance(row[0], int) and cursor <= row[0] < end_ms
        )[:limit]
        logger.info(
            "Dukascopy tick transport call completed for symbol %s returned %d",
            symbol,
            len(bounded),
        )
        return bounded


__all__: list[str] = [
    "_CircuitOpenError",
    "_DukascopyCircuitBreaker",
    "_DukascopyTransport",
    "_ProviderResponseError",
]
