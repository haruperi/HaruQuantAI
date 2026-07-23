"""Canonical Binance product-profile broker adapter."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, override

from app.services.brokers.adapter_runtime.subscription import (  # noqa: TC001
    _BrokerSubscription,
)
from app.services.brokers.binance_session.mapping import (
    _map_kline,
    _map_order_book,
    _map_quote,
    _map_symbol,
    _map_trade,
    _provider_interval,
)
from app.services.brokers.binance_session.profiles import _BINANCE_PROFILES
from app.services.brokers.binance_session.transport import _BinanceTransport
from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerId,
    BrokerMarketStatus,
    BrokerOrderBook,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.price_streams.binance import _BinancePriceStreamsMixin


class BinanceBrokerAdapter(_BinancePriceStreamsMixin, _UnsupportedAdapterBase):
    """Immutable Binance profile adapter with initial Spot reads only."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        transport: _BinanceTransport | None = None,
    ) -> None:
        """Initialize the BinanceBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            transport: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        profile = _BINANCE_PROFILES[config.broker_id]
        if config.environment not in profile.environments:
            raise ValueError("Binance profile/environment mismatch")
        if config.endpoint is not None:
            raise ValueError("Binance custom endpoints are unavailable")
        if config.credentials and not set(config.credentials) <= set(
            profile.credential_keys
        ):
            raise ValueError("unknown Binance credential key")
        super().__init__(config)
        self._profile = profile
        self._transport = transport or _BinanceTransport(
            config, self._record_provider_latency
        )
        self._subscriptions: dict[
            str, tuple[_BrokerSubscription[Any], asyncio.Task[None]]
        ] = {}

    @override
    async def connect(self) -> BrokerResult[None]:
        """Verify Spot ping/time; Futures profiles remain registry-only.

        Returns:
            Canonical verified connection result.
        """
        if self._config.broker_id != BrokerId.BINANCE_SPOT:
            return self._unsupported(BrokerCapabilityId.CONNECT)
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            await self._transport.connect()
        except ImportError, OSError, TimeoutError, ValueError, ConnectionError:
            await self._transition(BrokerConnectionState.FAILED, reason="probe_failed")
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def disconnect(self) -> BrokerResult[None]:
        """Close all clients and streams deterministically.

        Returns:
            Canonical idempotent disconnection result.
        """
        for subscription, _task in tuple(self._subscriptions.values()):
            await subscription.unsubscribe()
        await self._transport.close()
        return await super().disconnect()

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Verify current Binance reachability with the documented ping.

        Returns:
            Canonical current connectivity evidence.
        """
        await self._transport.call("ping")
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> BrokerResult[None]:
        """Run the documented Spot ping.

        Returns:
            Canonical provider-health result.
        """
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
        """Return a caller-bounded page of exact Spot symbols.

        Raises:
            ValueError: If limit is not positive.
        """
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

    async def get_spread(self, symbol: str) -> BrokerResult[Decimal]:
        """Return the current genuine Spot book-ticker spread.

        Returns:
            Canonical quote-asset spread.

        Raises:
            ValueError: If the provider omits bid or ask evidence.
        """
        value = await self._transport.call("get_orderbook_ticker", symbol=symbol)
        quote = _map_quote(value, symbol)
        if quote.bid is None or quote.ask is None:
            raise ValueError("Binance book ticker omitted bid or ask")
        return self._result(BrokerCapabilityId.GET_SPREAD, data=quote.ask - quote.bid)

    async def get_market_status(self, symbol: str) -> BrokerResult[BrokerMarketStatus]:
        """Return Binance's provider-reported symbol trading status.

        Returns:
            Canonical market status.
        """
        value = await self._transport.call("get_symbol_info", symbol=symbol)
        if value is None:
            return self._unsupported(BrokerCapabilityId.GET_MARKET_STATUS)
        provider_status = str(value.get("status", ""))
        status: Literal["OPEN", "CLOSED", "HALTED", "UNKNOWN"] = (
            "OPEN" if provider_status == "TRADING" else "HALTED"
        )
        return self._result(
            BrokerCapabilityId.GET_MARKET_STATUS,
            data=BrokerMarketStatus(
                symbol=symbol,
                status=status,
                retrieved_at=datetime.now(UTC),
                reason=provider_status,
            ),
        )

    async def get_order_book(
        self, symbol: str, depth: int | None = None
    ) -> BrokerResult[BrokerOrderBook]:
        """Return a genuine bounded Binance Spot depth snapshot.

        Returns:
            Canonical sequence-aware order-book snapshot.

        Raises:
            ValueError: If depth is not positive.
        """
        if depth is None or depth <= 0:
            raise ValueError("positive Binance order-book depth is required")
        value = await self._transport.call("get_order_book", symbol=symbol, limit=depth)
        return self._result(
            BrokerCapabilityId.GET_ORDER_BOOK,
            data=_map_order_book(value, symbol, depth=depth, is_snapshot=True),
        )

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return bounded genuine aggregate trades.

        Raises:
            ValueError: If limit is not positive.
        """
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
        """Return caller-bounded genuine Spot klines.

        Raises:
            ValueError: If limit is not positive.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive kline limit is required")
        provider_timeframe = _provider_interval(timeframe)
        kwargs: dict[str, object] = {
            "symbol": symbol,
            "interval": provider_timeframe,
            "limit": limit,
        }
        if start is not None:
            kwargs["startTime"] = int(start.timestamp() * 1000)
        if end is not None:
            kwargs["endTime"] = int(end.timestamp() * 1000)
        values = await self._transport.call("get_klines", **kwargs)
        items = tuple(
            _map_kline(
                value,
                symbol,
                provider_timeframe,
                requested_timeframe=timeframe,
            )
            for value in values
        )
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

    @staticmethod
    def _validate_single_symbol(symbols: tuple[str, ...]) -> None:
        """Require one exact symbol for one Binance websocket.

        Raises:
            ValueError: If the symbol tuple does not contain exactly one value.
        """
        if len(symbols) != 1 or not symbols[0].strip():
            raise ValueError("Binance websocket requires exactly one symbol")
