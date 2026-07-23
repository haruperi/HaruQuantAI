# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""Binance price-stream operations."""

import asyncio
from collections.abc import Callable, Mapping
from typing import Any, cast

from app.services.brokers.adapter_runtime.subscription import _BrokerSubscription
from app.services.brokers.binance_session.mapping import (
    _map_order_book,
    _map_stream_bar,
    _map_stream_quote,
)
from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerOrderBook,
    BrokerQuote,
    BrokerResult,
    BrokerSubscription,
    BrokerSubscriptionInfo,
)
from app.utils import generate_id, utc_now


class _BinancePriceStreamsMixin:
    """Private provider operations owned by this feature."""

    _last_error: BrokerError | None

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
            Canonical unsubscribe result, or `BROKER_SUBSCRIPTION_NOT_FOUND`
            when this adapter instance does not own the supplied identifier.
        """
        record = self._subscriptions.get(subscription_id)
        if record is None:
            error = BrokerError(
                code=BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND,
                message="Subscription is not owned by this adapter",
                capability=BrokerCapabilityId.UNSUBSCRIBE,
            )
            self._last_error = error
            return self._result(BrokerCapabilityId.UNSUBSCRIBE, error=error)
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
