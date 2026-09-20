"""Darwinex market data feed transport connector.

Feature:
    FEAT-BROKERS-DARWINEX

Purpose:
    Provides remote transport connection and raw payload acquisition for Darwinex
    tick and quote data feeds, replicating StrategyQuant X DataSourceDarwinex
    architecture.

Donor Logic (SQX DataSourceDarwinex):
    * Connects to Darwinex tick data service (FTP/REST/WebSocket transport).
    * Streams raw payload chunks to caller without local storage or transformation
      (FR-BROKERS-TRANSPORT_BOUNDARY).
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
    BROKER_DARWINEX,
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
class DarwinexFeedConfig:
    """Configuration options for Darwinex feed connector."""

    schema_version: int = 1
    api_endpoint: str = "https://api.darwinex.com/v1"
    ftp_host: str = "tickdata.darwinex.com"
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
        "User-Agent": "HaruQuantAI/1.0 (Brokers; Darwinex)",
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
                    f"Darwinex authentication failed ({exc.code}): {exc.reason}"
                ) from exc
            last_err = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc

        if attempt < max_retries:
            time.sleep(0.1 * (2**attempt))

    raise BrokerConnectionError(
        f"Darwinex request failed after {max_retries} retries: {last_err}"
    ) from last_err


class DarwinexFeedService(IBrokerFeedConnector):
    """Transport connector streaming raw Darwinex tick payload chunks."""

    def __init__(self, config: DarwinexFeedConfig | None = None) -> None:
        self._config = config or DarwinexFeedConfig()
        self._connected: bool = False
        self._conn_config: BrokerConnectionConfig | None = None
        self._token: str | None = None
        self._last_latency_ms: float = 0.0

    @property
    @override
    def provider_name(self) -> str:
        return "darwinex"

    @override
    def is_connected(self) -> bool:
        return self._connected

    @override
    async def connect(self, config: BrokerConnectionConfig) -> None:
        self._conn_config = config
        if not self._config.mock_mode:
            token = config.secret_key_ref or os.environ.get(
                "HARU_BROKER_DARWINEX_TOKEN", ""
            )
            if not token:
                raise BrokerAuthenticationError(
                    "Darwinex token required: provide secret_key_ref or "
                    "set HARU_BROKER_DARWINEX_TOKEN."
                )
            self._token = token

        self._connected = True
        logger.info(
            "darwinex_feed_connected",
            endpoint=config.endpoint or self._config.api_endpoint,
            mock_mode=self._config.mock_mode,
        )

    @override
    async def disconnect(self) -> None:
        self._connected = False
        self._token = None
        logger.info("darwinex_feed_disconnected")

    @override
    async def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw Darwinex tick transport chunks directly to caller.

        Pure transport boundary (FR-BROKERS-TRANSPORT_BOUNDARY): produces raw
        bytes without parsing into domain bars or persisting to database.
        """
        if not self._connected:
            raise BrokerConnectionError("Darwinex connector is not connected.")

        if start_utc > end_utc:
            raise UnsupportedCapabilityError(
                "start_utc must precede end_utc for Darwinex streaming."
            )

        current = start_utc
        seq = 0
        step = timedelta(hours=1)

        while current <= end_utc:
            is_eof = (current + step) > end_utc

            if self._config.mock_mode:
                raw_bytes = (
                    f'{{"provider":"darwinex","symbol":"{symbol}",'
                    f'"timestamp":"{current.isoformat()}","bid":1.08500,'
                    f'"ask":1.08512,"vol":100}}'
                ).encode()
                yield RawTransportChunk(
                    provider="darwinex",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=raw_bytes,
                    is_eof=is_eof,
                    metadata={
                        "feed_type": "tick_stream",
                        "period": current.isoformat(),
                        "simulated": True,
                    },
                )
            else:
                auth_header = (
                    {"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                url = (
                    f"{self._config.api_endpoint}/ticks/{symbol}"
                    f"?from={current.isoformat()}"
                )
                data, _status, lat = await asyncio.to_thread(
                    _http_get,
                    url,
                    headers=auth_header,
                    timeout_s=self._config.timeout_s,
                    max_retries=self._config.max_retries,
                )
                self._last_latency_ms = lat
                yield RawTransportChunk(
                    provider="darwinex",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=data,
                    is_eof=is_eof,
                    metadata={
                        "feed_type": "tick_stream",
                        "period": current.isoformat(),
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
            provider="darwinex",
            state=state,
            latency_ms=latency,
            last_heartbeat_utc=datetime.now(UTC) if self._connected else None,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.darwinex",
    provides=frozenset({BROKER_DARWINEX}),
    requires=frozenset(),
    optional=frozenset(),
    description="Darwinex market data feed transport connector",
)


class DarwinexFeature:
    """Wire DarwinexFeedService into application runtime lifecycle."""

    def __init__(self, config: DarwinexFeedConfig | None = None) -> None:
        self._config = config or DarwinexFeedConfig()
        self._service: DarwinexFeedService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, ctx: FeatureContext) -> None:
        """Start the feature and provide DarwinexFeedService capability."""
        self._service = DarwinexFeedService(self._config)
        ctx.provide(BROKER_DARWINEX, self._service)
        logger.info("brokers_darwinex_feature_started")

    async def stop(self, _ctx: FeatureContext) -> None:
        """Stop the feature and release resources."""
        if self._service and self._service.is_connected():
            await self._service.disconnect()
        self._service = None
        logger.info("brokers_darwinex_feature_stopped")


def feature(config: DarwinexFeedConfig | None = None) -> DarwinexFeature:
    """Return a zero-argument factory instance of DarwinexFeature."""
    return DarwinexFeature(config)
