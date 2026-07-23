"""FEAT-BRK-09: exercise bounded order, deal, and position history reads.

Runs the genuine MT5 and cTrader adapters over offline transports, so real
pagination bounds, provider identifier preservation, and canonical mapping
execute for both providers without network traffic.
"""

import asyncio
from datetime import UTC, datetime

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
    BrokerOrderFilter,
    BrokerPositionFilter,
    CTraderBrokerAdapter,
    MT5BrokerAdapter,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 2, tzinfo=UTC)


async def example_mt5_execution_state_reads() -> None:
    """MT5 preserves exact provider tickets across every bounded read."""
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=OfflineMT5Transport()
    )
    await adapter.connect()

    positions = await adapter.get_positions(BrokerPositionFilter(), limit=10)
    show_value(
        "mt5-positions",
        positions,
        f"id={positions.data.items[0].position_id} "
        f"profit={positions.data.items[0].profit}"
        if positions.data
        else None,
    )
    show_value(
        "mt5-position", await adapter.get_position("555001"), "single target resolved"
    )

    orders = await adapter.get_orders(BrokerOrderFilter(), limit=10)
    show_value(
        "mt5-orders",
        orders,
        f"id={orders.data.items[0].order_id} remaining={orders.data.items[0].remaining}"
        if orders.data
        else None,
    )
    show_value("mt5-order", await adapter.get_order("555002"), "single target resolved")

    deals = await adapter.list_deal_history(_START, _END, limit=10)
    show_value(
        "mt5-deals",
        deals,
        f"id={deals.data.items[0].deal_id} price={deals.data.items[0].price}"
        if deals.data
        else None,
    )
    show("mt5-order-history", await adapter.list_order_history(_START, _END, limit=10))
    show(
        "mt5-transactions",
        await adapter.list_account_transactions(_START, _END, limit=10),
    )


async def example_ctrader_execution_state_reads() -> None:
    """cTrader preserves exact provider identifiers across bounded reads."""
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER),
        available_capabilities(),
        transport=OfflineCTraderTransport(),
    )
    await adapter.connect()

    positions = await adapter.get_positions(BrokerPositionFilter(), limit=10)
    show_value(
        "ctrader-positions",
        positions,
        f"id={positions.data.items[0].position_id}" if positions.data else None,
    )
    orders = await adapter.get_orders(BrokerOrderFilter(), limit=10)
    show_value(
        "ctrader-orders",
        orders,
        f"id={orders.data.items[0].order_id}" if orders.data else None,
    )
    deals = await adapter.list_deal_history(_START, _END, limit=10)
    show_value(
        "ctrader-deals",
        deals,
        f"id={deals.data.items[0].deal_id}" if deals.data else None,
    )
    show(
        "ctrader-order-history",
        await adapter.list_order_history(_START, _END, limit=10),
    )


async def example_unbounded_history_is_rejected() -> None:
    """History reads are always caller-bounded; no whole-history fan-out."""
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=OfflineMT5Transport()
    )
    await adapter.connect()
    show("mt5-unbounded-history", await adapter.list_order_history(_START, _END))


async def example_reads_remain_gated() -> None:
    """A gated read returns unsupported without a provider call."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), unavailable_capabilities(), transport=transport
    )
    show("gated-orders", await adapter.get_orders(BrokerOrderFilter(), limit=1))
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-09 operation offline."""
    await example_mt5_execution_state_reads()
    await example_ctrader_execution_state_reads()
    await example_unbounded_history_is_rejected()
    await example_reads_remain_gated()


if __name__ == "__main__":
    asyncio.run(main())
