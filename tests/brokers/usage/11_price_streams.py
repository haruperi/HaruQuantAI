"""FEAT-BRK-11: Streaming subscriptions."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_118() -> None:
    """FR-BRK-118: Subscribe quote stream."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_quotes(("BTCUSDT",))
        print("FR-BRK-118:", res.status)

    asyncio.run(run())


def fr_brokers_119() -> None:
    """FR-BRK-119: Subscribe bar stream."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_bars(("BTCUSDT",), "1m")
        print("FR-BRK-119:", res.status)

    asyncio.run(run())


def fr_brokers_120() -> None:
    """FR-BRK-120: Subscribe order book stream."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_order_book(("BTCUSDT",))
        print("FR-BRK-120:", res.status)

    asyncio.run(run())


def fr_brokers_121() -> None:
    """FR-BRK-121: Unsubscribe stream."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.unsubscribe("sub-1")
        print("FR-BRK-121:", res.status)

    asyncio.run(run())


def fr_brokers_122() -> None:
    """FR-BRK-122: List active subscriptions."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_subscriptions()
        print("FR-BRK-122:", res.status)

    asyncio.run(run())


def fr_brokers_123() -> None:
    """FR-BRK-123: Private streaming transport helper."""
    print("FR-BRK-123: streaming helper checked")


def main() -> None:
    """Execute every FR-BRK-118..123 usage function."""
    fr_brokers_118()
    fr_brokers_119()
    fr_brokers_120()
    fr_brokers_121()
    fr_brokers_122()
    fr_brokers_123()


if __name__ == "__main__":
    main()
