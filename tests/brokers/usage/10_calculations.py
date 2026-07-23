"""FEAT-BRK-10: exercise provider-native margin and profit calculations.

Runs the genuine MT5 and cTrader adapters over offline transports so the real
provider-native calculation calls and their canonical Decimal mapping execute.
No local risk formula or approximation is ever substituted.
"""

import asyncio
from decimal import Decimal

from _support import (
    OfflineCTraderTransport,
    OfflineMT5Transport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import (
    BrokerId,
    BrokerMarginRequest,
    BrokerProfitRequest,
    CTraderBrokerAdapter,
    MT5BrokerAdapter,
)


def _margin(profile: str, quantity: Decimal) -> BrokerMarginRequest:
    """Build one provider-native margin request."""
    return BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=quantity,
        quantity_unit="lots",
        product_profile=profile,
    )


def _profit(profile: str, quantity: Decimal) -> BrokerProfitRequest:
    """Build one provider-native profit request."""
    return BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=quantity,
        quantity_unit="lots",
        open_price=Decimal("1.10"),
        close_price=Decimal("1.11"),
        product_profile=profile,
    )


async def example_provider_native_calculations() -> None:
    """Both providers return venue-authoritative values, never local formulas."""
    mt5 = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=OfflineMT5Transport()
    )
    ctrader = CTraderBrokerAdapter(
        config(BrokerId.CTRADER),
        available_capabilities(),
        transport=OfflineCTraderTransport(),
    )
    await mt5.connect()
    await ctrader.connect()

    mt5_margin = await mt5.calculate_margin(_margin("mt5", Decimal("0.01")))
    show_value("mt5-margin", mt5_margin, mt5_margin.data)
    mt5_profit = await mt5.calculate_profit(_profit("mt5", Decimal("0.01")))
    show_value("mt5-profit", mt5_profit, mt5_profit.data)

    ct_margin = await ctrader.calculate_margin(_margin("ctrader", Decimal(1)))
    show_value("ctrader-margin", ct_margin, ct_margin.data)
    ct_profit = await ctrader.calculate_profit(_profit("ctrader", Decimal(1)))
    show_value("ctrader-profit", ct_profit, ct_profit.data)


async def example_calculations_remain_gated() -> None:
    """A gated calculation returns unsupported without a provider call."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), unavailable_capabilities(), transport=transport
    )
    show(
        "gated-margin", await adapter.calculate_margin(_margin("mt5", Decimal("0.01")))
    )
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-10 operation offline."""
    await example_provider_native_calculations()
    await example_calculations_remain_gated()


if __name__ == "__main__":
    asyncio.run(main())
