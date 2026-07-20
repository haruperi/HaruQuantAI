"""FEAT-BRK-10: exercise broker margin and profit calculation signatures."""

import asyncio
from decimal import Decimal

from _support import config, show, unavailable_capabilities
from app.services.brokers import (
    BrokerId,
    BrokerMarginRequest,
    BrokerProfitRequest,
    CTraderBrokerAdapter,
    MT5BrokerAdapter,
)


async def main() -> None:
    """Call both calculations for MT5 and cTrader without external state."""
    mt5 = MT5BrokerAdapter(config(BrokerId.MT5), unavailable_capabilities())
    ctrader = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    for name, adapter in (("mt5", mt5), ("ctrader", ctrader)):
        margin = BrokerMarginRequest(
            symbol="EURUSD",
            side="BUY",
            quantity=Decimal("0.01"),
            quantity_unit="lots",
            product_profile=name,
        )
        profit = BrokerProfitRequest(
            symbol="EURUSD",
            side="BUY",
            quantity=Decimal("0.01"),
            quantity_unit="lots",
            open_price=Decimal("1.10"),
            close_price=Decimal("1.11"),
            product_profile=name,
        )
        show(f"{name}-margin", await adapter.calculate_margin(margin))
        show(f"{name}-profit", await adapter.calculate_profit(profit))


if __name__ == "__main__":
    asyncio.run(main())
