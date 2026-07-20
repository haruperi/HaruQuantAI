"""FEAT-BRK-11: exercise cTrader and Binance stream ownership signatures."""

import asyncio

from _support import config, show, unavailable_capabilities
from app.services.brokers import BinanceBrokerAdapter, BrokerId, CTraderBrokerAdapter


async def main() -> None:
    """Call every stream operation without opening a provider websocket."""
    ctrader = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    binance = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), unavailable_capabilities()
    )
    show("ctrader-quotes", await ctrader.subscribe_quotes(("EURUSD",)))
    show("ctrader-list", await ctrader.list_subscriptions())
    show("ctrader-unsubscribe", await ctrader.unsubscribe("evt-offline"))
    show("binance-quotes", await binance.subscribe_quotes(("BTCUSDT",)))
    show("binance-bars", await binance.subscribe_bars(("BTCUSDT",), "1m"))
    show(
        "binance-order-book",
        await binance.subscribe_order_book(("BTCUSDT",), depth=5),
    )
    show("binance-list", await binance.list_subscriptions())
    show("binance-unsubscribe", await binance.unsubscribe("evt-offline"))


if __name__ == "__main__":
    asyncio.run(main())
