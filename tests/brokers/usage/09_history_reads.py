"""FEAT-BRK-09: exercise bounded MT5 and cTrader history-read signatures."""

import asyncio
from datetime import UTC, datetime

from _support import config, show, unavailable_capabilities
from app.services.brokers import BrokerId, CTraderBrokerAdapter, MT5BrokerAdapter


async def main() -> None:
    """Call every FEAT-BRK-09 operation with one bounded UTC window."""
    mt5 = MT5BrokerAdapter(config(BrokerId.MT5), unavailable_capabilities())
    ctrader = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    show("mt5-orders", await mt5.get_orders(limit=10))
    show("mt5-order", await mt5.get_order("11"))
    show("mt5-order-history", await mt5.list_order_history(start, end, limit=10))
    show("mt5-deal-history", await mt5.list_deal_history(start, end, limit=10))
    show("mt5-deal", await mt5.get_deal("31"))
    show(
        "mt5-transactions",
        await mt5.list_account_transactions(start, end, limit=10),
    )
    show("mt5-position", await mt5.get_position("21"))
    show("ctrader-orders", await ctrader.get_orders(limit=10))
    show("ctrader-positions", await ctrader.get_positions(limit=10))
    show(
        "ctrader-order-history",
        await ctrader.list_order_history(start, end, limit=10),
    )
    show(
        "ctrader-deal-history",
        await ctrader.list_deal_history(start, end, limit=10),
    )


if __name__ == "__main__":
    asyncio.run(main())
