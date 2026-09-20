"""Direct Dukascopy historical binary tick feed transport connector.

Feature:
    FEAT-BROKERS-DUKASCOPY

Purpose:
    Provides HTTP transport connection and raw bi5 chunk acquisition for Dukascopy
    tick feeds, matching StrategyQuant X DataSourceDukascopy architecture.

Donor Logic (SQX DataSourceDukascopy):
    * Resolves hourly tick chunk URLs:
      https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5
    * Pure transport: Streams raw payload bytes directly without local decompression,
      bar aggregation, or database storage (FR-BROKERS-TRANSPORT_BOUNDARY).
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
    BROKER_DUKASCOPY,
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

DUKASCOPY_BASE_URL: str = "https://datafeed.dukascopy.com/datafeed"


@dataclass(slots=True)
class DukascopyFeedConfig:
    """Slotted immutable configuration for Dukascopy feed connector."""

    schema_version: int = 1
    base_url: str = DUKASCOPY_BASE_URL
    timeout_s: float = 15.0
    max_retries: int = 3
    rate_limit_rps: float = 10.0
    mock_mode: bool = False


HTTP_NOT_FOUND: int = 404
HTTP_UNAUTHORIZED: int = 401
HTTP_FORBIDDEN: int = 403


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
        BrokerConnectionError: on network, DNS, TLS, or non-404 HTTP errors.
    """
    req_headers = {
        "User-Agent": "HaruQuantAI/1.0 (Brokers; Dukascopy)",
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
                    f"Dukascopy authentication failed ({exc.code}): {exc.reason}"
                ) from exc
            if exc.code == HTTP_NOT_FOUND:
                return b"", HTTP_NOT_FOUND, lat
            last_err = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc

        if attempt < max_retries:
            time.sleep(0.1 * (2**attempt))

    raise BrokerConnectionError(
        f"Dukascopy HTTP request failed after {max_retries} retries: {last_err}"
    ) from last_err


def build_dukascopy_hour_url(base_url: str, symbol: str, dt_utc: datetime) -> str:
    """Construct hourly .bi5 URL matching StrategyQuant X format."""
    sym = symbol.upper()
    year = dt_utc.year
    month = dt_utc.month - 1  # Dukascopy uses 0-indexed month (00-11)
    day = dt_utc.day
    hour = dt_utc.hour
    return f"{base_url}/{sym}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"


class DukascopyFeedService(IBrokerFeedConnector):
    """Transport connector streaming raw Dukascopy binary tick payloads."""

    def __init__(self, config: DukascopyFeedConfig | None = None) -> None:
        self._config = config or DukascopyFeedConfig()
        self._connected: bool = False
        self._conn_config: BrokerConnectionConfig | None = None
        self._last_latency_ms: float = 0.0

    @property
    @override
    def provider_name(self) -> str:
        return "dukascopy"

    @override
    def is_connected(self) -> bool:
        return self._connected

    @override
    async def connect(self, config: BrokerConnectionConfig) -> None:
        self._conn_config = config
        self._connected = True
        logger.info(
            "dukascopy_feed_connected",
            mock_mode=self._config.mock_mode,
            endpoint=config.endpoint or self._config.base_url,
        )

    @override
    async def disconnect(self) -> None:
        self._connected = False
        logger.info("dukascopy_feed_disconnected")

    @override
    async def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw .bi5 chunks across requested time span without processing."""
        if not self._connected:
            raise BrokerConnectionError("Dukascopy connector is not connected.")

        if start_utc > end_utc:
            raise UnsupportedCapabilityError(
                "start_utc must precede end_utc for Dukascopy streaming."
            )

        current = start_utc.replace(minute=0, second=0, microsecond=0)
        end = end_utc.replace(minute=0, second=0, microsecond=0)
        seq = 0

        while current <= end:
            url = build_dukascopy_hour_url(self._config.base_url, symbol, current)
            is_eof = current == end

            if self._config.mock_mode:
                raw_payload = b"\x00\x00\x00\x01\x00\x01\x86\xa0"
                chunk = RawTransportChunk(
                    provider="dukascopy",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=raw_payload,
                    is_eof=is_eof,
                    metadata={
                        "url": url,
                        "hour_utc": current.isoformat(),
                        "simulated": True,
                    },
                )
                yield chunk
            else:
                data, status, lat = await asyncio.to_thread(
                    _http_get,
                    url,
                    timeout_s=self._config.timeout_s,
                    max_retries=self._config.max_retries,
                )
                self._last_latency_ms = lat
                if status == HTTP_NOT_FOUND:
                    logger.info("dukascopy_hour_not_found", url=url)
                else:
                    chunk = RawTransportChunk(
                        provider="dukascopy",
                        symbol=symbol,
                        sequence_num=seq,
                        timestamp_utc=current,
                        payload_bytes=data,
                        is_eof=is_eof,
                        metadata={
                            "url": url,
                            "hour_utc": current.isoformat(),
                            "simulated": False,
                        },
                    )
                    yield chunk

            seq += 1
            current += timedelta(hours=1)
            await asyncio.sleep(0)

    @override
    async def get_health(self) -> ConnectionHealth:
        state = ConnectionState.READY if self._connected else ConnectionState.CLOSED
        is_real = self._connected and not self._config.mock_mode
        latency = self._last_latency_ms if is_real else 0.0
        return ConnectionHealth(
            provider="dukascopy",
            state=state,
            latency_ms=latency,
            last_heartbeat_utc=datetime.now(UTC) if self._connected else None,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.dukascopy",
    provides=frozenset({BROKER_DUKASCOPY}),
    requires=frozenset(),
    optional=frozenset(),
    description="Direct Dukascopy binary tick transport connector",
)


class DukascopyFeature:
    """Wire DukascopyFeedService into the application runtime lifecycle."""

    def __init__(self, config: DukascopyFeedConfig | None = None) -> None:
        self._config = config or DukascopyFeedConfig()
        self._service: DukascopyFeedService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and provide DukascopyFeedService capability."""
        self._service = DukascopyFeedService(self._config)
        context.provide(BROKER_DUKASCOPY, self._service)
        logger.info("brokers_dukascopy_feature_started")

    async def stop(self, _context: FeatureContext) -> None:
        """Stop the feature and release resources."""
        if self._service and self._service.is_connected():
            await self._service.disconnect()
        self._service = None
        logger.info("brokers_dukascopy_feature_stopped")


def feature(config: DukascopyFeedConfig | None = None) -> DukascopyFeature:
    """Return a zero-argument factory instance of DukascopyFeature."""
    return DukascopyFeature(config)
