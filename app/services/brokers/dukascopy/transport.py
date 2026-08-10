"""Bounded Dukascopy direct-channel tick transport."""

from __future__ import annotations

# ruff: noqa: S310 - URL is constructed from a fixed HTTPS provider base.
import asyncio
import hashlib
import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, cast

from app.services.brokers._shared.circuit_breaker import _TransportCircuitBreaker
from app.services.brokers.canonical_contracts.protocols import (
    _CircuitOpenError,
    _ProviderResponseError,
)
from app.services.brokers.dukascopy.instruments import _web_symbol
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts import BrokerConnectionConfig

logger = get_logger(__name__)


class _DukascopyTransport:
    """Retrieve bounded genuine ticks from Dukascopy's public web chart."""

    _BASE_URL = "https://freeserv.dukascopy.com/2.0/index.php"

    def __init__(
        self,
        config: BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the tick transport.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for provider latency measurements.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._circuit = _TransportCircuitBreaker(
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
            from app.services.brokers.canonical_contracts import BrokerErrorCode

            await self._circuit.record_failure(BrokerErrorCode.BROKER_PROVIDER_ERROR)
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                symbol=symbol,
                result="error",
            ).warning("Dukascopy tick transport call failed")
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
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            symbol=symbol,
            result="success",
            returned_count=len(bounded),
        ).info("Dukascopy tick transport call completed")
        return bounded


__all__: list[str] = []
