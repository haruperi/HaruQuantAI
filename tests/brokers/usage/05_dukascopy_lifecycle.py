"""FEAT-BRK-05: Dukascopy research lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    BrokerPositionFilter,
    create_broker_adapter,
)


def fr_brokers_075() -> None:
    """FR-BRK-075: Return direct provider platform metadata without secrets."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_platform_info()
        print("FR-BRK-075:", res.status)

    asyncio.run(run())


def fr_brokers_076() -> None:
    """FR-BRK-076: Return provider-reported permissions without inferring from SDK."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_permissions()
        print("FR-BRK-076:", res.status)

    asyncio.run(run())


def fr_brokers_077() -> None:
    """FR-BRK-077: Return bounded page of provider-visible accounts."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_accounts()
        print("FR-BRK-077:", res.status)

    asyncio.run(run())


def fr_brokers_078() -> None:
    """FR-BRK-078: Reject in-place account switching as unsupported."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.select_account("acc-1")
        print("FR-BRK-078:", res.status)

    asyncio.run(run())


def fr_brokers_079() -> None:
    """FR-BRK-079: Return provider account info and state."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_account_info()
        print("FR-BRK-079:", res.status)

    asyncio.run(run())


def fr_brokers_080() -> None:
    """FR-BRK-080: Return provider balances without currency conversion."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_balances()
        print("FR-BRK-080:", res.status)

    asyncio.run(run())


def fr_brokers_081() -> None:
    """FR-BRK-081: Return provider-known assets without constructing universe."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.list_assets()
        print("FR-BRK-081:", res.status)

    asyncio.run(run())


def fr_brokers_082() -> None:
    """FR-BRK-082: Return direct provider metadata for one asset or not-found."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_asset_info("EUR")
        print("FR-BRK-082:", res.status)

    asyncio.run(run())


def fr_brokers_083() -> None:
    """FR-BRK-083: Return bounded canonical page of current positions."""
    adapter = create_broker_adapter(BrokerId.DUKASCOPY, config(BrokerId.DUKASCOPY)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_positions(BrokerPositionFilter())
        print("FR-BRK-083:", res.status)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-075..083 usage function."""
    fr_brokers_075()
    fr_brokers_076()
    fr_brokers_077()
    fr_brokers_078()
    fr_brokers_079()
    fr_brokers_080()
    fr_brokers_081()
    fr_brokers_082()
    fr_brokers_083()


if __name__ == "__main__":
    main()
