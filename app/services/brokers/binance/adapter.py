"""Canonical Binance product-profile broker adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.brokers.binance.mapping import (
    _map_kline,
    _map_quote,
    _map_symbol,
    _map_trade,
)
from app.services.brokers.binance.profiles import _BINANCE_PROFILES
from app.services.brokers.binance.transport import _BinanceTransport
from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerId,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase


class BinanceBrokerAdapter(_UnsupportedAdapterBase):
    """Immutable Binance profile adapter with initial Spot reads only."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _BinanceTransport | None = None,
    ) -> None:
        profile = _BINANCE_PROFILES[config.broker_id]
        if config.environment not in profile.environments:
            raise ValueError("Binance profile/environment mismatch")
        if config.endpoint is not None:
            raise ValueError("Binance custom endpoints are unavailable")
        if config.credentials and not set(config.credentials) <= set(
            profile.credential_keys
        ):
            raise ValueError("unknown Binance credential key")
        super().__init__(config, capabilities)
        self._profile = profile
        self._transport = transport or _BinanceTransport(config)

    async def connect(self) -> BrokerResult[None]:
        """Verify Spot ping/time; Futures profiles remain registry-only."""
        if self._config.broker_id != BrokerId.BINANCE_SPOT:
            return self._unsupported(BrokerCapabilityId.CONNECT)
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            await self._transport.connect()
        except (ImportError, OSError, TimeoutError, ValueError, ConnectionError):
            await self._transition(BrokerConnectionState.FAILED, reason="probe_failed")
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> BrokerResult[None]:
        """Close all clients and streams deterministically."""
        await self._transport.close()
        return await super().disconnect()

    async def ping(self) -> BrokerResult[None]:
        """Run the documented Spot ping."""
        await self._transport.call("ping")
        return self._result(BrokerCapabilityId.PING)

    async def get_server_time(self) -> BrokerResult[BrokerServerTime]:
        """Return server time and measured local timing evidence."""
        sent = datetime.now(UTC)
        value = await self._transport.call("get_server_time")
        received = datetime.now(UTC)
        provider = datetime.fromtimestamp(int(value["serverTime"]) / 1000, UTC)
        round_trip = (received - sent).total_seconds() * 1000
        midpoint = sent + (received - sent) / 2
        return self._result(
            BrokerCapabilityId.GET_SERVER_TIME,
            data=BrokerServerTime(
                provider_time=provider,
                local_send_time=sent,
                local_receive_time=received,
                estimated_clock_offset_ms=(provider - midpoint).total_seconds() * 1000,
                round_trip_latency_ms=round_trip,
            ),
        )

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return a caller-bounded page of exact Spot symbols."""
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive symbol limit is required")
        value = await self._transport.call("get_exchange_info")
        symbols = value["symbols"]
        if query is not None:
            symbols = [item for item in symbols if query in item["symbol"]]
        items = tuple(_map_symbol(item) for item in symbols[:limit])
        return self._result(
            BrokerCapabilityId.GET_SYMBOLS,
            data=BrokerPage(
                items=items, limit=limit, truncated=len(symbols) > len(items)
            ),
        )

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]:
        """Return direct Spot symbol metadata."""
        value = await self._transport.call("get_symbol_info", symbol=symbol)
        if value is None:
            return self._unsupported(BrokerCapabilityId.GET_SYMBOL_INFO)
        return self._result(BrokerCapabilityId.GET_SYMBOL_INFO, data=_map_symbol(value))

    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]:
        """Return a genuine Spot book ticker."""
        value = await self._transport.call("get_orderbook_ticker", symbol=symbol)
        return self._result(
            BrokerCapabilityId.GET_QUOTE, data=_map_quote(value, symbol)
        )

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return bounded genuine aggregate trades."""
        del start, end, cursor
        if limit is None or limit <= 0:
            raise ValueError("positive trade limit is required")
        values = await self._transport.call(
            "get_aggregate_trades", symbol=symbol, limit=limit
        )
        items = tuple(_map_trade(value, symbol) for value in values)
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(items=items, limit=limit),
        )

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return caller-bounded genuine Spot klines."""
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive kline limit is required")
        kwargs: dict[str, object] = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit,
        }
        if start is not None:
            kwargs["startTime"] = int(start.timestamp() * 1000)
        if end is not None:
            kwargs["endTime"] = int(end.timestamp() * 1000)
        values = await self._transport.call("get_klines", **kwargs)
        items = tuple(_map_kline(value, symbol, timeframe) for value in values)
        return self._result(
            BrokerCapabilityId.GET_HISTORICAL_BARS,
            data=BrokerPage(items=items, limit=limit),
        )

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return immutable selected Binance product profile."""
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="Binance",
                product_profile=self._profile.endpoint_mode,
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
            ),
        )
