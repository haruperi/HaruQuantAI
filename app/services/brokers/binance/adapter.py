"""Canonical Binance product-profile broker adapter."""

import asyncio
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast, override

from app.services.brokers.binance.mapping import (
    _map_kline,
    _map_order_book,
    _map_quote,
    _map_stream_bar,
    _map_stream_quote,
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
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerMarketStatus,
    BrokerOrderBook,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSubscription,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.runtime.subscription import _BrokerSubscription
from app.utils import generate_id, utc_now


class BinanceBrokerAdapter(_UnsupportedAdapterBase):
    """Immutable Binance profile adapter with initial Spot reads only."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _BinanceTransport | None = None,
    ) -> None:
        """Initialize the BinanceBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            capabilities: Value supplied to the operation.
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
        super().__init__(config, capabilities)
        self._profile = profile
        self._transport = transport or _BinanceTransport(config)
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
        except (ImportError, OSError, TimeoutError, ValueError, ConnectionError):
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

    async def subscribe_quotes(
        self, symbols: tuple[str, ...]
    ) -> BrokerResult[BrokerSubscription[BrokerQuote]]:
        """Open a bounded Binance book-ticker stream.

        Returns:
            Adapter-owned quote subscription.
        """
        self._validate_single_symbol(symbols)
        symbol = symbols[0]
        subscription = await self._open_stream(
            capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
            symbols=symbols,
            stream_name="symbol_book_ticker_socket",
            stream_kwargs={"symbol": symbol.lower()},
            mapper=lambda value: _map_stream_quote(value, symbol),
        )
        return self._result(BrokerCapabilityId.SUBSCRIBE_QUOTES, data=subscription)

    async def subscribe_bars(
        self, symbols: tuple[str, ...], timeframe: str
    ) -> BrokerResult[BrokerSubscription[BrokerBar]]:
        """Open a bounded Binance kline stream.

        Returns:
            Adapter-owned bar subscription.
        """
        self._validate_single_symbol(symbols)
        symbol = symbols[0]
        subscription = await self._open_stream(
            capability=BrokerCapabilityId.SUBSCRIBE_BARS,
            symbols=symbols,
            stream_name="kline_socket",
            stream_kwargs={"symbol": symbol.lower(), "interval": timeframe},
            mapper=lambda value: _map_stream_bar(value, symbol),
        )
        return self._result(BrokerCapabilityId.SUBSCRIBE_BARS, data=subscription)

    async def subscribe_order_book(
        self, symbols: tuple[str, ...], depth: int | None = None
    ) -> BrokerResult[BrokerSubscription[BrokerOrderBook]]:
        """Open a bounded Binance depth stream after a genuine snapshot.

        Returns:
            Adapter-owned order-book subscription.

        Raises:
            ValueError: If depth is not positive.
        """
        self._validate_single_symbol(symbols)
        if depth is None or depth <= 0:
            raise ValueError("positive Binance stream depth is required")
        symbol = symbols[0]
        snapshot = await self._transport.call(
            "get_order_book", symbol=symbol, limit=depth
        )
        subscription = await self._open_stream(
            capability=BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
            symbols=symbols,
            stream_name="depth_socket",
            stream_kwargs={"symbol": symbol.lower(), "depth": depth},
            mapper=lambda value: _map_order_book(
                value, symbol, depth=depth, is_snapshot=False
            ),
            initial_event=_map_order_book(
                snapshot, symbol, depth=depth, is_snapshot=True
            ),
        )
        return self._result(BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK, data=subscription)

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]:
        """Close one exact Binance websocket subscription.

        Returns:
            Canonical unsubscribe result or not-found error.
        """
        record = self._subscriptions.get(subscription_id)
        if record is None:
            return self._unsupported(BrokerCapabilityId.UNSUBSCRIBE)
        await record[0].unsubscribe()
        return self._result(BrokerCapabilityId.UNSUBSCRIBE)

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]:
        """Return immutable Binance subscription metadata.

        Returns:
            Current adapter-owned subscriptions.
        """
        return self._result(
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
            data=tuple(record[0].info for record in self._subscriptions.values()),
        )

    async def _open_stream[T](
        self,
        *,
        capability: BrokerCapabilityId,
        symbols: tuple[str, ...],
        stream_name: str,
        stream_kwargs: Mapping[str, object],
        mapper: Callable[[dict[str, Any]], T],
        initial_event: T | None = None,
    ) -> _BrokerSubscription[T]:
        """Bind one provider websocket generator to a bounded subscription.

        Returns:
            Adapter-owned typed subscription.
        """
        subscription_id = generate_id("evt")
        task_holder: list[asyncio.Task[None]] = []

        async def _close() -> None:
            """Handle close."""
            if task_holder:
                task_holder[0].cancel()
            self._subscriptions.pop(subscription_id, None)

        subscription = _BrokerSubscription[T](
            broker=self._config.broker_id,
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            info=BrokerSubscriptionInfo(
                subscription_id=subscription_id,
                capability=capability,
                symbols=symbols,
                created_at=utc_now(),
                buffer_size=self._config.stream_buffer_size,
            ),
            unsubscribe_callback=_close,
        )
        if initial_event is not None:
            await subscription.publish(initial_event)
        task = asyncio.create_task(
            self._pump_stream(subscription, stream_name, stream_kwargs, mapper)
        )
        task_holder.append(task)
        self._subscriptions[subscription_id] = (
            cast("_BrokerSubscription[Any]", subscription),
            task,
        )
        return subscription

    async def _pump_stream[T](
        self,
        subscription: _BrokerSubscription[T],
        stream_name: str,
        stream_kwargs: Mapping[str, object],
        mapper: Callable[[dict[str, Any]], T],
    ) -> None:
        """Map provider events until explicit unsubscribe or terminal failure.

        Raises:
            asyncio.CancelledError: If the owning subscription is cancelled.
        """
        try:
            async for value in self._transport.stream(stream_name, **stream_kwargs):
                if not await subscription.publish(mapper(value)):
                    return
        except asyncio.CancelledError:
            raise
        except (
            ImportError,
            OSError,
            TimeoutError,
            ValueError,
            ConnectionError,
        ) as error:
            code = (
                BrokerErrorCode.BROKER_TIMEOUT
                if isinstance(error, TimeoutError)
                else BrokerErrorCode.BROKER_SUBSCRIPTION_FAILED
            )
            await subscription.fail(
                BrokerError(
                    code=code,
                    message="Binance subscription failed",
                    provider_message=type(error).__name__,
                    capability=subscription.info.capability,
                )
            )

    @staticmethod
    def _validate_single_symbol(symbols: tuple[str, ...]) -> None:
        """Require one exact symbol for one Binance websocket.

        Raises:
            ValueError: If the symbol tuple does not contain exactly one value.
        """
        if len(symbols) != 1 or not symbols[0].strip():
            raise ValueError("Binance websocket requires exactly one symbol")
