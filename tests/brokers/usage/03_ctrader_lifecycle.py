"""FEAT-BRK-03: cTrader provider lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_057() -> None:
    """FR-BRK-057: Yield one canonical event per validated lifecycle transition."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None
    print("FR-BRK-057: connection_events", hasattr(adapter, "connection_events"))


def fr_brokers_058() -> None:
    """FR-BRK-058: Return bounded page of exact provider-native symbols."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_symbols(limit=5)
        print("FR-BRK-058:", res.status)

    asyncio.run(run())


def fr_brokers_059() -> None:
    """FR-BRK-059: Return direct provider specifications and trading flags for
    symbol."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_symbol_info("EURUSD")
        print("FR-BRK-059:", res.status)

    asyncio.run(run())


def fr_brokers_060() -> None:
    """FR-BRK-060: Perform provider watch-list selection or return unsupported."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.select_symbol("EURUSD")
        print("FR-BRK-060:", res.status)

    asyncio.run(run())


def fr_brokers_061() -> None:
    """FR-BRK-061: Return provider-reported market state without deriving calendars."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_market_status("EURUSD")
        print("FR-BRK-061:", res.status)

    asyncio.run(run())


def fr_brokers_062() -> None:
    """FR-BRK-062: Return provider-supplied trading windows within optional bounds."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_trading_sessions("EURUSD")
        print("FR-BRK-062:", res.status)

    asyncio.run(run())


def fr_brokers_063() -> None:
    """FR-BRK-063: Return latest genuine provider quote without fallback price."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_quote("EURUSD")
        print("FR-BRK-063:", res.status)

    asyncio.run(run())


def fr_brokers_064() -> None:
    """FR-BRK-064: Return bounded genuine provider ticks or unsupported."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_ticks("EURUSD", limit=5)
        print("FR-BRK-064:", res.status)

    asyncio.run(run())


def fr_brokers_065() -> None:
    """FR-BRK-065: Return bounded provider bars using structural timeframe
    translation."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_historical_bars("EURUSD", "1m", limit=5)
        print("FR-BRK-065:", res.status)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-057..065 usage function."""
    fr_brokers_057()
    fr_brokers_058()
    fr_brokers_059()
    fr_brokers_060()
    fr_brokers_061()
    fr_brokers_062()
    fr_brokers_063()
    fr_brokers_064()
    fr_brokers_065()


if __name__ == "__main__":
    main()
