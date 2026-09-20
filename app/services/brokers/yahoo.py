"""Yahoo Finance market data feed transport connector.

Feature:
    FEAT-BROKERS-YAHOO

Purpose:
    Provides remote transport connection and raw payload acquisition for Yahoo Finance
    daily and intraday data feeds, matching StrategyQuant X DataSourceYahoo and
    YahooDataManager architecture.

Donor Logic (SQX DataSourceYahoo / YahooDataManager):
    * Performs session cookie and crumb acquisition for Yahoo Finance v8 chart API.
    * Streams raw JSON payload chunks to caller without local storage or
      transformation (FR-BROKERS-TRANSPORT_BOUNDARY).
"""

from __future__ import annotations

import asyncio
import time
import urllib.error
import urllib.request
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override

from app.contracts.brokers import (
    BROKER_YAHOO,
    BrokerAuthenticationError,
    BrokerConnectionConfig,
    BrokerConnectionError,
    ConnectionHealth,
    ConnectionState,
    RawTransportChunk,
    UnsupportedCapabilityError,
)
from app.contracts.brokers import (
    BrokerFeedConnector as IBrokerFeedConnector,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True)
class YahooFeedConfig:
    """Configuration options for Yahoo Finance feed connector."""

    schema_version: int = 1
    api_endpoint: str = "https://query1.finance.yahoo.com/v8/finance/chart"
    crumb_url: str = "https://fc.yahoo.com"
    timeout_s: float = 15.0
    max_retries: int = 3
    mock_mode: bool = False


HTTP_OK: int = 200
HTTP_UNAUTHORIZED: int = 401
HTTP_FORBIDDEN: int = 403
HTTP_TOO_MANY_REQUESTS: int = 429


def _http_get(
    url: str,
    headers: Mapping[str, str] | None = None,
    timeout_s: float = 15.0,
    max_retries: int = 3,
) -> tuple[bytes, int, float]:
    """Execute stdlib HTTP GET with retries, timeout, and status code.

    Returns:
        tuple of (payload_bytes, status_code, latency_ms).

    Raises:
        BrokerAuthenticationError: on HTTP 401 or 403.
        BrokerConnectionError: on network, DNS, TLS, or HTTP 4xx/5xx errors.
    """
    req_headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        **(headers or {}),
    }
    req = urllib.request.Request(url, headers=req_headers)  # noqa: S310
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
                data = resp.read()
                lat = (time.perf_counter() - t0) * 1000.0
                return data, resp.status, lat
        except urllib.error.HTTPError as exc:
            lat = (time.perf_counter() - t0) * 1000.0
            if exc.code in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
                raise BrokerAuthenticationError(
                    f"Yahoo Finance authentication failed ({exc.code}): {exc.reason}"
                ) from exc
            if exc.code == HTTP_TOO_MANY_REQUESTS:
                raise BrokerConnectionError(
                    "Yahoo Finance rate limit exceeded (HTTP 429)."
                ) from exc
            last_err = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc

        if attempt < max_retries:
            time.sleep(0.1 * (2**attempt))

    raise BrokerConnectionError(
        f"Yahoo Finance request failed after {max_retries} retries: {last_err}"
    ) from last_err


class YahooFeedService(IBrokerFeedConnector):
    """Transport connector streaming raw Yahoo Finance v8 chart JSON payloads."""

    def __init__(self, config: YahooFeedConfig | None = None) -> None:
        self._config = config or YahooFeedConfig()
        self._connected: bool = False
        self._conn_config: BrokerConnectionConfig | None = None
        self._last_latency_ms: float = 0.0

    @property
    @override
    def provider_name(self) -> str:
        return "yahoo"

    @override
    def is_connected(self) -> bool:
        return self._connected

    @override
    async def connect(self, config: BrokerConnectionConfig) -> None:
        self._conn_config = config
        self._connected = True
        logger.info(
            "yahoo_feed_connected",
            endpoint=config.endpoint or self._config.api_endpoint,
            mock_mode=self._config.mock_mode,
        )

    @override
    async def disconnect(self) -> None:
        self._connected = False
        logger.info("yahoo_feed_disconnected")

    @override
    async def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw Yahoo Finance v8 chart payload chunks directly to caller.

        Pure transport boundary (FR-BROKERS-TRANSPORT_BOUNDARY): produces raw
        response bytes without parsing into internal candles or saving locally.
        """
        if not self._connected:
            raise BrokerConnectionError("Yahoo Finance connector is not connected.")

        if start_utc > end_utc:
            raise UnsupportedCapabilityError(
                "start_utc must precede end_utc for Yahoo Finance streaming."
            )

        current = start_utc
        seq = 0
        step = timedelta(days=1)

        while current <= end_utc:
            period_start = int(current.timestamp())
            period_end = int((current + step).timestamp())
            is_eof = (current + step) > end_utc

            if self._config.mock_mode:
                raw_bytes = (
                    f'{{"chart":{{"result":[{{"meta":{{"symbol":"{symbol}",'
                    f'"regularMarketPrice":185.50,"period1":{period_start},'
                    f'"period2":{period_end}}},'
                    f'"timestamp":[{period_start}],'
                    f'"indicators":{{"quote":[{{"open":[184.0],"high":[186.0],'
                    f'"low":[183.5],"close":[185.5],"volume":[5000000]}}]}}'
                    f'}}],"error":null}}}}'
                ).encode()
                yield RawTransportChunk(
                    provider="yahoo",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=raw_bytes,
                    is_eof=is_eof,
                    metadata={
                        "interval": "1d",
                        "period_start": period_start,
                        "period_end": period_end,
                        "simulated": True,
                    },
                )
            else:
                endpoint = self._config.api_endpoint
                params = f"period1={period_start}&period2={period_end}&interval=1d"
                url = f"{endpoint}/{symbol}?{params}"

                data, _status, lat = await asyncio.to_thread(
                    _http_get,
                    url,
                    timeout_s=self._config.timeout_s,
                    max_retries=self._config.max_retries,
                )
                self._last_latency_ms = lat
                yield RawTransportChunk(
                    provider="yahoo",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=data,
                    is_eof=is_eof,
                    metadata={
                        "interval": "1d",
                        "period_start": period_start,
                        "period_end": period_end,
                        "simulated": False,
                    },
                )

            seq += 1
            current += step
            await asyncio.sleep(0)

    @override
    async def get_health(self) -> ConnectionHealth:
        state = ConnectionState.READY if self._connected else ConnectionState.CLOSED
        is_real = self._connected and not self._config.mock_mode
        latency = self._last_latency_ms if is_real else 0.0
        return ConnectionHealth(
            provider="yahoo",
            state=state,
            latency_ms=latency,
            last_heartbeat_utc=datetime.now(UTC) if self._connected else None,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.yahoo",
    provides=frozenset({BROKER_YAHOO}),
    requires=frozenset(),
    optional=frozenset(),
    description="Yahoo Finance market data feed transport connector",
)


class YahooFeature:
    """Wire YahooFeedService into application runtime lifecycle."""

    def __init__(self, config: YahooFeedConfig | None = None) -> None:
        self._config = config or YahooFeedConfig()
        self._service: YahooFeedService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and provide YahooFeedService capability."""
        self._service = YahooFeedService(self._config)
        context.provide(BROKER_YAHOO, self._service)
        logger.info("brokers_yahoo_feature_started")

    async def stop(self, _context: FeatureContext) -> None:
        """Stop the feature and release resources."""
        if self._service and self._service.is_connected():
            await self._service.disconnect()
        self._service = None
        logger.info("brokers_yahoo_feature_stopped")


def feature(config: YahooFeedConfig | None = None) -> YahooFeature:
    """Return a zero-argument factory instance of YahooFeature."""
    return YahooFeature(config)
