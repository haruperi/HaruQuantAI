"""FEAT-BRK-12: cTrader market data."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_124() -> None:
    """FR-BRK-124: Fetch cTrader symbols."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_symbols(limit=5)
        print("FR-BRK-124:", res.status)

    asyncio.run(run())


def fr_brokers_125() -> None:
    """FR-BRK-125: Fetch cTrader symbol info."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_symbol_info("EURUSD")
        print("FR-BRK-125:", res.status)

    asyncio.run(run())


def fr_brokers_126() -> None:
    """FR-BRK-126: Fetch cTrader quote."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_quote("EURUSD")
        print("FR-BRK-126:", res.status)

    asyncio.run(run())


def fr_brokers_127() -> None:
    """FR-BRK-127: Fetch cTrader ticks."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_ticks("EURUSD", limit=5)
        print("FR-BRK-127:", res.status)

    asyncio.run(run())


def fr_brokers_128() -> None:
    """FR-BRK-128: Fetch cTrader historical bars."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_historical_bars("EURUSD", "1m", limit=5)
        print("FR-BRK-128:", res.status)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-124..128 usage function."""
    fr_brokers_124()
    fr_brokers_125()
    fr_brokers_126()
    fr_brokers_127()
    fr_brokers_128()


if __name__ == "__main__":
    main()
