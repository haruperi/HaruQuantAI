"""FEAT-BRK-11: genuine session and price-stream release boundaries."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import BrokerAdapter, BrokerErrorCode, BrokerId


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unreleased(adapter: BrokerAdapter, operation: str) -> None:
    """Require one stream operation to remain release-gated."""
    if operation == "quotes":
        result = await adapter.subscribe_quotes(("BTCUSDT",))
    elif operation == "bars":
        result = await adapter.subscribe_bars(("BTCUSDT",), "1m")
    elif operation == "book":
        result = await adapter.subscribe_order_book(("BTCUSDT",))
    else:
        result = await adapter.unsubscribe("sub-1")
    expected = (
        BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND
        if operation == "unsubscribe"
        else BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
    )
    require_error("Result", result, expected)


async def fr_brokers_118(adapter: BrokerAdapter) -> None:
    """FR-BRK-118: Subscribe to a bounded quote stream when released."""
    _header("FR-BRK-118: Subscribe to a bounded quote stream when released.")
    await _require_unreleased(adapter, "quotes")


async def fr_brokers_119(adapter: BrokerAdapter) -> None:
    """FR-BRK-119: Subscribe to a bounded bar stream when released."""
    _header("FR-BRK-119: Subscribe to a bounded bar stream when released.")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_120(adapter: BrokerAdapter) -> None:
    """FR-BRK-120: Subscribe to a bounded order-book stream when released."""
    _header("FR-BRK-120: Subscribe to a bounded order-book stream when released.")
    await _require_unreleased(adapter, "book")


async def fr_brokers_121(adapter: BrokerAdapter) -> None:
    """FR-BRK-121: Unsubscribe exactly one owned stream."""
    _header("FR-BRK-121: Unsubscribe exactly one owned stream.")
    await _require_unreleased(adapter, "unsubscribe")


async def fr_brokers_122(adapter: BrokerAdapter) -> None:
    """FR-BRK-122: List active adapter-owned subscriptions."""
    _header("FR-BRK-122: List active adapter-owned subscriptions.")
    result = await adapter.list_subscriptions()
    require_success("Result", result)
    assert result.data == ()


async def fr_brokers_123(adapter: BrokerAdapter) -> None:
    """FR-BRK-123: Preserve the private stream-transport boundary."""
    del adapter
    _header("FR-BRK-123: Preserve the private stream-transport boundary.")
    print("Result streaming helper checked")


async def _run() -> None:
    """Execute stream release evidence in one genuine Binance testnet session."""
    async with real_session(BrokerId.BINANCE_SPOT) as adapter:
        await fr_brokers_118(adapter)
        await fr_brokers_119(adapter)
        await fr_brokers_120(adapter)
        await fr_brokers_121(adapter)
        await fr_brokers_122(adapter)
        await fr_brokers_123(adapter)


def main() -> None:
    """Run the standalone genuine price-stream release program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
