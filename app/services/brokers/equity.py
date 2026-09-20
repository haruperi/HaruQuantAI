"""StrategyQuant Equity data feed transport connector.

Feature:
    FEAT-BROKERS-EQUITY

Purpose:
    Provides REST transport connection and raw payload acquisition for StrategyQuant
    official Equity stock data feeds, matching DataSourceSQEquityData architecture.

Donor Logic (SQX DataSourceSQEquityData):
    * Connects to StrategyQuant Equity server endpoints (/getExchanges, /lookup,
      /update).
    * Handles token / subscription verification metadata.
    * Pure transport: Streams raw payload bytes directly without local file or
      database writing (FR-BROKERS-TRANSPORT_BOUNDARY).
"""

from __future__ import annotations

import asyncio
import os
import time
import urllib.error
import urllib.request
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override

from app.contracts.brokers import (
    BROKER_EQUITY,
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
class SQEquityFeedConfig:
    """Configuration options for SQ Equity feed connector."""

    schema_version: int = 1
    api_endpoint: str = "https://data.strategyquant.com/api/v1/equity"
    timeout_s: float = 15.0
    max_retries: int = 3
    mock_mode: bool = False


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
        BrokerConnectionError: on network, DNS, TLS, or HTTP 4xx/5xx errors.
    """
    req_headers = {
        "User-Agent": "HaruQuantAI/1.0 (Brokers; SQEquity)",
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
                    f"SQ Equity authentication failed ({exc.code}): {exc.reason}"
                ) from exc
            last_err = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc

        if attempt < max_retries:
            time.sleep(0.1 * (2**attempt))

    raise BrokerConnectionError(
        f"SQ Equity request failed after {max_retries} retries: {last_err}"
    ) from last_err


class SQEquityFeedService(IBrokerFeedConnector):
    """Transport connector streaming raw SQ Equity stock data payloads."""

    def __init__(self, config: SQEquityFeedConfig | None = None) -> None:
        self._config = config or SQEquityFeedConfig()
        self._connected: bool = False
        self._conn_config: BrokerConnectionConfig | None = None
        self._license_key: str | None = None
        self._last_latency_ms: float = 0.0

    @property
    @override
    def provider_name(self) -> str:
        return "sq_equity"

    @override
    def is_connected(self) -> bool:
        return self._connected

    @override
    async def connect(self, config: BrokerConnectionConfig) -> None:
        self._conn_config = config
        if not self._config.mock_mode:
            license_key = config.secret_key_ref or os.environ.get(
                "HARU_BROKER_SQ_LICENSE", ""
            )
            if not license_key:
                raise BrokerAuthenticationError(
                    "StrategyQuant license required: provide secret_key_ref or "
                    "set HARU_BROKER_SQ_LICENSE."
                )
            self._license_key = license_key

        self._connected = True
        logger.info(
            "sq_equity_feed_connected",
            endpoint=config.endpoint or self._config.api_endpoint,
            mock_mode=self._config.mock_mode,
        )

    @override
    async def disconnect(self) -> None:
        self._connected = False
        self._license_key = None
        logger.info("sq_equity_feed_disconnected")

    @override
    async def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw historical stock payload chunks directly to caller."""
        if not self._connected:
            raise BrokerConnectionError("SQ Equity connector is not connected.")

        if start_utc > end_utc:
            raise UnsupportedCapabilityError(
                "start_utc must precede end_utc for SQ Equity streaming."
            )

        current = start_utc
        seq = 0
        step = timedelta(days=1)

        while current <= end_utc:
            d_str = current.strftime("%Y-%m-%d")
            is_eof = (current + step) > end_utc

            if self._config.mock_mode:
                raw_bytes = (
                    f'{{"ticker":"{symbol}","date":"{d_str}","close":150.25}}'.encode()
                )
                yield RawTransportChunk(
                    provider="sq_equity",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=raw_bytes,
                    is_eof=is_eof,
                    metadata={
                        "exchange": "US_EQUITY",
                        "date": current.isoformat(),
                        "simulated": True,
                    },
                )
            else:
                headers = (
                    {"X-License-Key": self._license_key} if self._license_key else {}
                )
                url = f"{self._config.api_endpoint}?symbol={symbol}&date={d_str}"
                data, _status, lat = await asyncio.to_thread(
                    _http_get,
                    url,
                    headers=headers,
                    timeout_s=self._config.timeout_s,
                    max_retries=self._config.max_retries,
                )
                self._last_latency_ms = lat
                yield RawTransportChunk(
                    provider="sq_equity",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=data,
                    is_eof=is_eof,
                    metadata={
                        "exchange": "US_EQUITY",
                        "date": current.isoformat(),
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
            provider="sq_equity",
            state=state,
            latency_ms=latency,
            last_heartbeat_utc=datetime.now(UTC) if self._connected else None,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.equity",
    provides=frozenset({BROKER_EQUITY}),
    requires=frozenset(),
    optional=frozenset(),
    description="StrategyQuant Equity data feed transport connector",
)


class SQEquityFeature:
    """Wire SQEquityFeedService into the application runtime lifecycle."""

    def __init__(self, config: SQEquityFeedConfig | None = None) -> None:
        self._config = config or SQEquityFeedConfig()
        self._service: SQEquityFeedService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, ctx: FeatureContext) -> None:
        """Start the feature and provide SQEquityFeedService capability."""
        self._service = SQEquityFeedService(self._config)
        ctx.provide(BROKER_EQUITY, self._service)
        logger.info("brokers_equity_feature_started")

    async def stop(self, _ctx: FeatureContext) -> None:
        """Stop the feature and release resources."""
        if self._service and self._service.is_connected():
            await self._service.disconnect()
        self._service = None
        logger.info("brokers_equity_feature_stopped")


def feature(config: SQEquityFeedConfig | None = None) -> SQEquityFeature:
    """Return a zero-argument factory instance of SQEquityFeature."""
    return SQEquityFeature(config)
