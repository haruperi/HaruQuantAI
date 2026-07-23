"""FEAT-BRK-02: MetaTrader 5 account and lifecycle capabilities."""

import asyncio

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    create_broker_adapter,
)


def fr_brokers_048() -> None:
    """FR-BRK-048: Explicitly establish and verify transport, auth, account, and
    environment."""
    created = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5))
    print("FR-BRK-048:", created.status)


def fr_brokers_049() -> None:
    """FR-BRK-049: Idempotently close every session, task, handle, and subscription."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.disconnect()
        print("FR-BRK-049:", res.status)

    asyncio.run(run())


def fr_brokers_050() -> None:
    """FR-BRK-050: Recover transport/session up to bound without replaying
    operations."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.reconnect()
        print("FR-BRK-050:", res.status)

    asyncio.run(run())


def fr_brokers_051() -> None:
    """FR-BRK-051: Return verified current connectivity rather than local Boolean
    flag."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.is_connected()
        print("FR-BRK-051:", res.data)

    asyncio.run(run())


def fr_brokers_052() -> None:
    """FR-BRK-052: Return detailed lifecycle, auth, account, permission, and status.
    environment"""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_connection_status()
        print("FR-BRK-052:", res.data.state.value if res.data else None)

    asyncio.run(run())


def fr_brokers_053() -> None:
    """FR-BRK-053: Perform provider-supported liveness probe or return unsupported."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.ping()
        print("FR-BRK-053:", res.status)

    asyncio.run(run())


def fr_brokers_054() -> None:
    """FR-BRK-054: Use provider token/session refresh or fail closed."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.refresh_session()
        print("FR-BRK-054:", res.status)

    asyncio.run(run())


def fr_brokers_055() -> None:
    """FR-BRK-055: Return provider time and clock/latency evidence when available."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_server_time()
        print("FR-BRK-055:", res.status)

    asyncio.run(run())


def fr_brokers_056() -> None:
    """FR-BRK-056: Expose adapter instance latest redacted diagnostic error."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_last_error()
        print("FR-BRK-056:", res.data)

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-048..056 usage function."""
    fr_brokers_048()
    fr_brokers_049()
    fr_brokers_050()
    fr_brokers_051()
    fr_brokers_052()
    fr_brokers_053()
    fr_brokers_054()
    fr_brokers_055()
    fr_brokers_056()


if __name__ == "__main__":
    main()
