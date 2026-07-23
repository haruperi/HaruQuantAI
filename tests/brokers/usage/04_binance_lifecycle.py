"""FEAT-BRK-04: Binance provider lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_066() -> None:
    """FR-BRK-066: Return provider order-book truth with depth/sequence evidence."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_order_book("BTCUSDT")
        print("FR-BRK-066:", res.status)

    asyncio.run(run())


def fr_brokers_067() -> None:
    """FR-BRK-067: Return provider-reported spread only without fixed placeholder."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_spread("BTCUSDT")
        print("FR-BRK-067:", res.status)

    asyncio.run(run())


def fr_brokers_068() -> None:
    """FR-BRK-068: Create adapter-scoped bounded quote stream handle."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_quotes(("BTCUSDT",))
        print("FR-BRK-068:", res.status)

    asyncio.run(run())


def fr_brokers_069() -> None:
    """FR-BRK-069: Create provider bar stream where genuine events are supported."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_bars(("BTCUSDT",), "1m")
        print("FR-BRK-069:", res.status)

    asyncio.run(run())


def fr_brokers_070() -> None:
    """FR-BRK-070: Create order-book stream where sequence safety is supported."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.subscribe_order_book(("BTCUSDT",))
        print("FR-BRK-070:", res.status)

    asyncio.run(run())


def fr_brokers_071() -> None:
    """FR-BRK-071: Terminate exactly one owned subscription."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.unsubscribe("invalid-id")
        print("FR-BRK-071:", res.status)

    asyncio.run(run())


def fr_brokers_072() -> None:
    """FR-BRK-072: List immutable metadata for subscriptions owned by current
    adapter."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_subscriptions()
        print("FR-BRK-072:", len(res.data) if res.data else 0)

    asyncio.run(run())


def fr_brokers_073() -> None:
    """FR-BRK-073: Return refreshed capability report with unapproved mutations
    unavailable."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_feature_flags()
        print("FR-BRK-073:", res.data.broker_id if res.data else None)

    asyncio.run(run())


def fr_brokers_074() -> None:
    """FR-BRK-074: Answer capability support from report without probing missing
    attribute."""
    adapter = create_broker_adapter(
        BrokerId.BINANCE_SPOT, config(BrokerId.BINANCE_SPOT)
    ).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.supports(BrokerCapabilityId.GET_QUOTE)
        print("FR-BRK-074:", res.data)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-066..074 usage function."""
    fr_brokers_066()
    fr_brokers_067()
    fr_brokers_068()
    fr_brokers_069()
    fr_brokers_070()
    fr_brokers_071()
    fr_brokers_072()
    fr_brokers_073()
    fr_brokers_074()


if __name__ == "__main__":
    main()
