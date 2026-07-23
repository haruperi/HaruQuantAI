# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""cTrader price-stream operations."""

import asyncio

from app.services.brokers.adapter_runtime.subscription import _BrokerSubscription
from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerQuote,
    BrokerResult,
    BrokerSubscription,
    BrokerSubscriptionInfo,
)
from app.services.brokers.ctrader_session.mapping import (
    _field,
    _map_quote,
)
from app.utils import generate_id, utc_now


class _CTraderPriceStreamsMixin:
    """Private provider operations owned by this feature."""

    async def subscribe_quotes(
        self, symbols: tuple[str, ...]
    ) -> BrokerResult[BrokerSubscription[BrokerQuote]]:
        """Open one bounded cTrader spot-event subscription.

        Returns:
            Adapter-owned canonical quote subscription.
        """
        subscription = await self._open_quote_subscription(symbols)
        return self._result(BrokerCapabilityId.SUBSCRIBE_QUOTES, data=subscription)

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]:
        """Close one exact adapter-owned cTrader subscription.

        Returns:
            Canonical unsubscribe result or not-found error.
        """
        subscription = self._subscriptions.get(subscription_id)
        if subscription is None:
            return self._error(
                BrokerCapabilityId.UNSUBSCRIBE,
                BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND,
            )
        await subscription.unsubscribe()
        return self._result(BrokerCapabilityId.UNSUBSCRIBE)

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]:
        """Return immutable cTrader subscription metadata.

        Returns:
            Current adapter-owned subscriptions.
        """
        return self._result(
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
            data=tuple(item.info for item in self._subscriptions.values()),
        )

    async def _open_quote_subscription(
        self, symbols: tuple[str, ...]
    ) -> _BrokerSubscription[BrokerQuote]:
        """Open one provider spot subscription and bind local delivery.

        Returns:
            Adapter-owned bounded quote subscription.

        Raises:
            ValueError: If symbols are empty or duplicated.
        """
        if not symbols or len(set(symbols)) != len(symbols):
            raise ValueError("cTrader subscription symbols must be unique")
        identities = [await self._symbol_identity(symbol) for symbol in symbols]
        symbol_ids = tuple(item[0] for item in identities)
        await self._request(
            "ProtoOASubscribeSpotsReq",
            "ProtoOASubscribeSpotsRes",
            symbolId=symbol_ids,
            subscribeToSpotTimestamp=True,
        )
        if not self._event_handler_registered:
            self._transport.register_event_handler(self._on_provider_event)
            self._event_handler_registered = True
        subscription_id = generate_id("evt")

        async def _close() -> None:
            """Handle close."""
            await self._request(
                "ProtoOAUnsubscribeSpotsReq",
                "ProtoOAUnsubscribeSpotsRes",
                symbolId=symbol_ids,
            )
            self._subscriptions.pop(subscription_id, None)

        subscription = _BrokerSubscription[BrokerQuote](
            broker=self._config.broker_id,
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            info=BrokerSubscriptionInfo(
                subscription_id=subscription_id,
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=symbols,
                created_at=utc_now(),
                buffer_size=self._config.stream_buffer_size,
            ),
            unsubscribe_callback=_close,
        )
        self._subscriptions[subscription_id] = subscription
        return subscription

    def _on_provider_event(self, event: object) -> None:
        """Map and dispatch one cTrader spot event without blocking callback IO."""
        if type(event).__name__ != "ProtoOASpotEvent":
            return
        symbol_id = int(_field(event, "symbolId"))
        symbol = self._symbol_names.get(symbol_id)
        spec = self._symbol_specs.get(symbol or "")
        if symbol is None or spec is None:
            return
        quote = _map_quote(event, symbol, int(_field(spec, "digits")))
        for subscription in tuple(self._subscriptions.values()):
            if symbol in subscription.info.symbols:
                task = asyncio.create_task(subscription.publish(quote))
                self._publish_tasks.add(task)
                task.add_done_callback(self._publish_tasks.discard)
