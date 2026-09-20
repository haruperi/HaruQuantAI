"""Cryptocurrency exchange market data transport connector.

Feature:
    FEAT-BROKERS-CRYPTO

Purpose:
    Provides remote transport connection and raw payload acquisition for cryptocurrency
    exchanges (Binance, Bybit, CCXT-compatible endpoints), matching StrategyQuant X
    DataSourceCrypto and CryptoExchangeBinance architecture.

Donor Logic (SQX DataSourceCrypto / CryptoExchangeBinance):
    * Connects to cryptocurrency REST and WebSocket transport feeds.
    * Streams raw payload chunks to caller without local storage or transformation
      (FR-BROKERS-TRANSPORT_BOUNDARY).
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
    BROKER_CRYPTO,
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
class CryptoFeedConfig:
    """Configuration options for Cryptocurrency exchange feed connector."""

    schema_version: int = 1
    exchange_id: str = "binance"
    rest_endpoint: str = "https://api.binance.com/api/v3"
    ws_endpoint: str = "wss://stream.binance.com:9443/ws"
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
        "User-Agent": "HaruQuantAI/1.0 (Brokers; Crypto)",
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
            if exc.code in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
                raise BrokerAuthenticationError(
                    f"Crypto exchange authentication failed ({exc.code}): {exc.reason}"
                ) from exc
            last_err = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc

        if attempt < max_retries:
            time.sleep(0.1 * (2**attempt))

    raise BrokerConnectionError(
        f"Crypto exchange request failed after {max_retries} retries: {last_err}"
    ) from last_err


class CryptoFeedService(IBrokerFeedConnector):
    """Transport connector streaming raw crypto exchange trade and kline chunks."""

    def __init__(self, config: CryptoFeedConfig | None = None) -> None:
        self._config = config or CryptoFeedConfig()
        self._connected: bool = False
        self._conn_config: BrokerConnectionConfig | None = None
        self._last_latency_ms: float = 0.0

    @property
    @override
    def provider_name(self) -> str:
        return "crypto"

    @property
    def exchange_id(self) -> str:
        """Configured exchange identifier."""
        return self._config.exchange_id

    @override
    def is_connected(self) -> bool:
        return self._connected

    @override
    async def connect(self, config: BrokerConnectionConfig) -> None:
        self._conn_config = config
        self._connected = True
        logger.info(
            "crypto_feed_connected",
            exchange=self._config.exchange_id,
            endpoint=config.endpoint or self._config.rest_endpoint,
            mock_mode=self._config.mock_mode,
        )

    @override
    async def disconnect(self) -> None:
        self._connected = False
        logger.info("crypto_feed_disconnected", exchange=self._config.exchange_id)

    @override
    async def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw crypto exchange transport chunks directly to caller.

        Pure transport boundary (FR-BROKERS-TRANSPORT_BOUNDARY): produces raw
        bytes without saving or aggregating into persistent tables.
        """
        if not self._connected:
            raise BrokerConnectionError("Crypto feed connector is not connected.")

        if start_utc > end_utc:
            raise UnsupportedCapabilityError(
                "start_utc must precede end_utc for crypto feed streaming."
            )

        current = start_utc
        seq = 0
        step = timedelta(hours=1)

        while current <= end_utc:
            start_ms = int(current.timestamp() * 1000)
            end_ms = int((current + step).timestamp() * 1000)
            is_eof = (current + step) > end_utc

            if self._config.mock_mode:
                raw_bytes = (
                    f'[["{start_ms}","64000.00","64500.00","63900.00","64200.00",'
                    f'"125.40","{end_ms}","8050680.00",512,"60.20","3864840.00","0"]]'
                ).encode()
                yield RawTransportChunk(
                    provider="crypto",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=raw_bytes,
                    is_eof=is_eof,
                    metadata={
                        "exchange": self._config.exchange_id,
                        "symbol": symbol,
                        "simulated": True,
                    },
                )
            else:
                params = (
                    f"symbol={symbol.upper()}&interval=1h"
                    f"&startTime={start_ms}&endTime={end_ms}&limit=1000"
                )
                url = f"{self._config.rest_endpoint}/klines?{params}"
                data, _status, lat = await asyncio.to_thread(
                    _http_get,
                    url,
                    timeout_s=self._config.timeout_s,
                    max_retries=self._config.max_retries,
                )
                self._last_latency_ms = lat
                yield RawTransportChunk(
                    provider="crypto",
                    symbol=symbol,
                    sequence_num=seq,
                    timestamp_utc=current,
                    payload_bytes=data,
                    is_eof=is_eof,
                    metadata={
                        "exchange": self._config.exchange_id,
                        "symbol": symbol,
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
            provider="crypto",
            state=state,
            latency_ms=latency,
            last_heartbeat_utc=datetime.now(UTC) if self._connected else None,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.crypto",
    provides=frozenset({BROKER_CRYPTO}),
    requires=frozenset(),
    optional=frozenset(),
    description="Cryptocurrency exchange market data transport connector",
)


class CryptoFeedFeature:
    """Wire CryptoFeedService into application runtime lifecycle."""

    def __init__(self, config: CryptoFeedConfig | None = None) -> None:
        self._config = config or CryptoFeedConfig()
        self._service: CryptoFeedService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, ctx: FeatureContext) -> None:
        """Start the feature and provide CryptoFeedService capability."""
        self._service = CryptoFeedService(self._config)
        ctx.provide(BROKER_CRYPTO, self._service)
        logger.info("brokers_crypto_feature_started")

    async def stop(self, _ctx: FeatureContext) -> None:
        """Stop the feature and release resources."""
        if self._service and self._service.is_connected():
            await self._service.disconnect()
        self._service = None
        logger.info("brokers_crypto_feature_stopped")


def feature(config: CryptoFeedConfig | None = None) -> CryptoFeedFeature:
    """Return a zero-argument factory instance of CryptoFeedFeature."""
    return CryptoFeedFeature(config)
