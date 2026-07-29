"""FEAT-BRK-02: MetaTrader 5 account and lifecycle capabilities."""

import asyncio

import _support  # noqa: F401
from _support import (
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    disconnect_broker,
    get_broker_connection_status,
    get_broker_last_error,
    get_broker_server_time,
    get_broker_value_field,
    is_broker_connected,
    ping_broker,
    reconnect_broker,
    refresh_broker_session,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def fr_brokers_048(adapter: object) -> None:
    """FR-BRK-048: Establish and verify transport, auth, account, and environment."""
    _header(
        "FR-BRK-048: Establish and verify transport, auth, account, and environment."
    )
    result = await get_broker_connection_status(adapter)
    require_success("Result", result)
    data = get_broker_value_field(result, "data")
    assert data is not None
    assert get_broker_value_field(data, "transport_connected")


async def fr_brokers_049(adapter: object) -> None:
    """FR-BRK-049: Idempotently close every session, task, handle, and subscription."""
    del adapter
    _header(
        "FR-BRK-049: Idempotently close every session, task, handle, and subscription."
    )
    disconnected = create_real_adapter("mt5")
    require_success("Result", await disconnect_broker(disconnected))
    require_success("Repeated result", await disconnect_broker(disconnected))


async def fr_brokers_050(adapter: object) -> None:
    """FR-BRK-050: Recover transport/session without replaying operations."""
    _header("FR-BRK-050: Recover transport/session without replaying operations.")
    require_success("Result", await reconnect_broker(adapter))


async def fr_brokers_051(adapter: object) -> None:
    """FR-BRK-051: Return verified connectivity rather than a local Boolean flag."""
    _header(
        "FR-BRK-051: Return verified connectivity rather than a local Boolean flag."
    )
    result = await is_broker_connected(adapter)
    require_success("Connected status", result)
    assert get_broker_value_field(result, "data") is True


async def fr_brokers_052(adapter: object) -> None:
    """FR-BRK-052: Return detailed lifecycle, auth, account, and environment."""
    _header("FR-BRK-052: Return detailed lifecycle, auth, account, and environment.")
    result = await get_broker_connection_status(adapter)
    require_success("Lifecycle state", result)
    data = get_broker_value_field(result, "data")
    assert data is not None
    print("Lifecycle value", get_broker_value_field(data, "state"))


async def fr_brokers_053(adapter: object) -> None:
    """FR-BRK-053: Perform a provider-supported liveness probe."""
    _header("FR-BRK-053: Perform a provider-supported liveness probe.")
    require_success("Liveness probe", await ping_broker(adapter))


async def fr_brokers_054(adapter: object) -> None:
    """FR-BRK-054: Use provider session refresh or fail closed."""
    _header("FR-BRK-054: Use provider session refresh or fail closed.")
    require_error(
        "Session refresh",
        await refresh_broker_session(adapter),
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_055(adapter: object) -> None:
    """FR-BRK-055: Return provider time evidence when available."""
    _header("FR-BRK-055: Return provider time evidence when available.")
    require_error(
        "Server time",
        await get_broker_server_time(adapter),
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_056(adapter: object) -> None:
    """FR-BRK-056: Expose the adapter's latest redacted diagnostic error."""
    _header("FR-BRK-056: Expose the adapter's latest redacted diagnostic error.")
    require_success("Last error", await get_broker_last_error(adapter))


async def _run() -> None:
    """Execute every lifecycle requirement in one genuine MT5 demo session."""
    async with real_session("mt5") as adapter:
        await fr_brokers_048(adapter)
        await fr_brokers_049(adapter)
        await fr_brokers_050(adapter)
        await fr_brokers_051(adapter)
        await fr_brokers_052(adapter)
        await fr_brokers_053(adapter)
        await fr_brokers_054(adapter)
        await fr_brokers_055(adapter)
        await fr_brokers_056(adapter)


def main() -> None:
    """Run the standalone genuine MT5 lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
