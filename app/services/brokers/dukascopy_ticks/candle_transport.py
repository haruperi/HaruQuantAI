"""Bounded Dukascopy web-chart candle transport with cursor pagination."""

# ruff: noqa: S310 - URL is constructed from a fixed HTTPS provider base.

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, cast

from app.services.brokers.adapter_runtime.circuit_breaker import (
    _TransportCircuitBreaker,
)
from app.services.brokers.contracts.protocols import (
    _CircuitOpenError,
    _ProviderResponseError,
)
from app.services.brokers.dukascopy_ticks.candle_mapping import _provider_interval
from app.services.brokers.dukascopy_ticks.instruments import _web_symbol
from app.utils import logger

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig

_PAGE_LIMIT = 5_000
_RETRY_BASE_SECONDS = 0.25
_RETRY_MAX_SECONDS = 2.0


@dataclass(frozen=True, slots=True)
class _CandleBatch:
    """One bounded set of raw candle rows plus pagination evidence."""

    rows: tuple[tuple[object, ...], ...]
    provider_symbol: str
    provider_interval: str
    page_count: int
    truncated: bool


class _DukascopyCandleTransport:
    """Retrieve genuine BID candles from Dukascopy's public web chart."""

    _BASE_URL = "https://freeserv.dukascopy.com/2.0/index.php"

    def __init__(
        self,
        config: BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
        waiter: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the candle transport.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for provider latency measurements.
            waiter: Optional asynchronous retry waiter for deterministic tests.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._waiter = waiter or asyncio.sleep
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    @staticmethod
    def _callback(
        symbol: str,
        interval: str,
        cursor: int,
        limit: int,
    ) -> str:
        """Derive a deterministic JSONP callback identifier.

        Returns:
            Callback name accepted by the JSONP interface.
        """
        material = f"{symbol}|{interval}|{cursor}|{limit}"
        suffix = hashlib.sha256(material.encode()).hexdigest()[:12]
        return f"_callbacks____{suffix}"

    @staticmethod
    def _parse_page(body: str, callback: str) -> tuple[tuple[object, ...], ...]:
        """Parse and structurally validate one JSONP page.

        Args:
            body: Provider response text.
            callback: Exact callback requested from the provider.

        Returns:
            Immutable raw provider rows.

        Raises:
            _ProviderResponseError: If the JSONP envelope or row shape is invalid.
        """
        prefix = f"{callback}("
        if not body.startswith(prefix) or not body.endswith(");"):
            raise _ProviderResponseError("invalid Dukascopy JSONP envelope")
        try:
            decoded = json.loads(body.removeprefix(prefix).removesuffix(");"))
        except json.JSONDecodeError as error:
            raise _ProviderResponseError("invalid Dukascopy candle JSON") from error
        if not isinstance(decoded, list):
            raise _ProviderResponseError("invalid Dukascopy candle page")
        rows: list[tuple[object, ...]] = []
        for row in decoded:
            if not isinstance(row, list):
                raise _ProviderResponseError("invalid Dukascopy candle row")
            rows.append(tuple(row))
        return tuple(rows)

    async def _request_page(
        self,
        *,
        symbol: str,
        interval: str,
        cursor: int,
        limit: int,
    ) -> tuple[tuple[object, ...], ...]:
        """Retrieve one bounded candle page with deterministic retries.

        Args:
            symbol: Web-chart provider symbol.
            interval: Web-chart provider interval.
            cursor: Inclusive provider timestamp in milliseconds.
            limit: Maximum rows requested from this page.

        Returns:
            Parsed raw provider rows.

        Raises:
            ConnectionError: If the transport circuit is open.
            _CircuitOpenError: If the circuit rejects the page request.
            OSError: If bounded retries cannot recover transport access.
            TimeoutError: If bounded retries exceed the configured timeout.
            UnicodeError: If bounded retries return undecodable text.
            _ProviderResponseError: If bounded retries receive malformed evidence.
            AssertionError: If the structurally exhaustive retry loop is violated.
        """
        callback = self._callback(symbol, interval, cursor, limit)
        query = urllib.parse.urlencode(
            {
                "path": "chart/json3",
                "splits": "true",
                "stocks": "true",
                "time_direction": "N",
                "jsonp": callback,
                "last_update": str(cursor),
                "offer_side": "B",
                "instrument": symbol,
                "interval": interval,
                "limit": str(limit),
            }
        )
        url = f"{self._BASE_URL}?{query}"
        attempts = self._config.transport_reconnect_max_attempts + 1
        for attempt in range(1, attempts + 1):
            blocked = await self._circuit.before_call()
            if blocked is not None:
                raise _CircuitOpenError("Dukascopy candle circuit is open")

            def _read() -> str:
                """Read one bounded provider response.

                Returns:
                    UTF-8 provider response text.
                """
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "HaruQuantAI/1.0",
                        "Referer": (
                            "https://freeserv.dukascopy.com/2.0/?path=chart/index"
                        ),
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
            except (
                TimeoutError,
                OSError,
                UnicodeError,
                _ProviderResponseError,
            ) as error:
                from app.services.brokers.contracts import BrokerErrorCode

                await self._circuit.record_failure(
                    BrokerErrorCode.BROKER_PROVIDER_ERROR
                )
                final = attempt == attempts
                logger.bind(
                    broker=self._config.broker_id.value,
                    environment=self._config.environment.value,
                    symbol=symbol,
                    interval=interval,
                    cursor=cursor,
                    attempt=attempt,
                    max_attempts=attempts,
                    result="error",
                    provider_code=BrokerErrorCode.BROKER_PROVIDER_ERROR.value,
                    exception_type=type(error).__name__,
                ).warning("Dukascopy candle page transport call failed")
                if final:
                    raise
                delay = min(
                    _RETRY_BASE_SECONDS * (2 ** (attempt - 1)),
                    _RETRY_MAX_SECONDS,
                )
                await self._waiter(delay)
                continue
            finally:
                if self._latency_sink is not None:
                    self._latency_sink((time.perf_counter() - started) * 1000.0)
            await self._circuit.record_success()
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                symbol=symbol,
                interval=interval,
                cursor=cursor,
                attempt=attempt,
                result="success",
                returned_count=len(rows),
            ).info("Dukascopy candle page transport call completed")
            return rows
        raise AssertionError("Dukascopy candle retry loop exhausted")

    @staticmethod
    def _consume_page(
        page: tuple[tuple[object, ...], ...],
        collected: list[tuple[object, ...]],
        *,
        cursor: int,
        start_ms: int,
        end_ms: int,
        limit: int,
        is_followup: bool,
    ) -> tuple[int, bool, bool]:
        """Consume one ordered page into the bounded output collection.

        Args:
            page: Raw provider page.
            collected: Mutable request-owned output collection.
            cursor: Inclusive timestamp used for the page request.
            start_ms: Inclusive requested range boundary.
            end_ms: Exclusive requested range boundary.
            limit: Maximum output row count.
            is_followup: Whether the inclusive cursor row should be skipped.

        Returns:
            Latest timestamp, whether output advanced, and whether range end was met.

        Raises:
            _ProviderResponseError: If timestamps are malformed or unordered.
        """
        progress = False
        latest = cursor
        for row in page:
            if not row or isinstance(row[0], bool) or not isinstance(row[0], int):
                raise _ProviderResponseError("invalid Dukascopy candle timestamp")
            timestamp = row[0]
            if timestamp < latest:
                raise _ProviderResponseError("unordered Dukascopy candle page")
            latest = timestamp
            if timestamp < start_ms or (is_followup and timestamp <= cursor):
                continue
            if timestamp >= end_ms:
                return latest, progress, True
            collected.append(row)
            progress = True
            if len(collected) == limit:
                break
        return latest, progress, False

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> _CandleBatch:
        """Retrieve a bounded, deduplicated forward candle range.

        Args:
            symbol: Exact canonical Dukascopy symbol.
            timeframe: Supported canonical candle timeframe.
            start: Inclusive timezone-aware range boundary.
            end: Exclusive timezone-aware range boundary.
            limit: Positive maximum returned rows.

        Returns:
            Raw provider rows and bounded pagination evidence.

        Raises:
            ValueError: If the range or limit is invalid.
            _ProviderResponseError: If timestamps are malformed or non-progressing.
        """
        if (
            start.tzinfo is None
            or start.utcoffset() is None
            or end.tzinfo is None
            or end.utcoffset() is None
            or start >= end
            or limit <= 0
        ):
            raise ValueError("ordered candle range and positive limit are required")
        provider_symbol = _web_symbol(symbol)
        provider_interval = _provider_interval(timeframe)
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        cursor = start_ms
        collected: list[tuple[object, ...]] = []
        page_count = 0
        reached_end = False
        max_pages = max(1, math.ceil(limit / (_PAGE_LIMIT - 1)) + 1)

        while len(collected) < limit and page_count < max_pages:
            duplicate_allowance = 1 if page_count else 0
            page_limit = min(
                _PAGE_LIMIT,
                limit - len(collected) + duplicate_allowance,
            )
            page = await self._request_page(
                symbol=provider_symbol,
                interval=provider_interval,
                cursor=cursor,
                limit=page_limit,
            )
            page_count += 1
            if not page:
                reached_end = True
                break

            latest, progress, reached_end = self._consume_page(
                page,
                collected,
                cursor=cursor,
                start_ms=start_ms,
                end_ms=end_ms,
                limit=limit,
                is_followup=page_count > 1,
            )
            if reached_end or len(collected) == limit:
                break
            if not progress or latest <= cursor:
                raise _ProviderResponseError(
                    "Dukascopy candle pagination did not advance"
                )
            cursor = latest

        truncated = len(collected) == limit and not reached_end
        return _CandleBatch(
            rows=tuple(collected),
            provider_symbol=provider_symbol,
            provider_interval=provider_interval,
            page_count=page_count,
            truncated=truncated,
        )


__all__: list[str] = []
