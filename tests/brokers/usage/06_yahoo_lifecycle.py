"""FEAT-BRK-06: Yahoo research lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    BrokerOrderFilter,
    create_broker_adapter,
)


def fr_brokers_084() -> None:
    """FR-BRK-084: Return one provider position or POSITION_NOT_FOUND."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_position("p1")
        print("FR-BRK-084:", res.status)

    asyncio.run(run())


def fr_brokers_085() -> None:
    """FR-BRK-085: Return bounded page of provider orders matching filter."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_orders(BrokerOrderFilter())
        print("FR-BRK-085:", res.status)

    asyncio.run(run())


def fr_brokers_086() -> None:
    """FR-BRK-086: Return one provider order or ORDER_NOT_FOUND."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_order("o1")
        print("FR-BRK-086:", res.status)

    asyncio.run(run())


def fr_brokers_087() -> None:
    """FR-BRK-087: Return bounded page of historical provider orders."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_order_history()
        print("FR-BRK-087:", res.status)

    asyncio.run(run())


def fr_brokers_088() -> None:
    """FR-BRK-088: Return bounded page of historical provider deals."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_deal_history()
        print("FR-BRK-088:", res.status)

    asyncio.run(run())


def fr_brokers_089() -> None:
    """FR-BRK-089: Return one provider deal or DEAL_NOT_FOUND."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_deal("d1")
        print("FR-BRK-089:", res.status)

    asyncio.run(run())


def fr_brokers_090() -> None:
    """FR-BRK-090: Return bounded page of provider account transactions."""
    adapter = create_broker_adapter(BrokerId.YAHOO, config(BrokerId.YAHOO)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_account_transactions()
        print("FR-BRK-090:", res.status)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-084..090 usage function."""
    fr_brokers_084()
    fr_brokers_085()
    fr_brokers_086()
    fr_brokers_087()
    fr_brokers_088()
    fr_brokers_089()
    fr_brokers_090()


if __name__ == "__main__":
    main()
