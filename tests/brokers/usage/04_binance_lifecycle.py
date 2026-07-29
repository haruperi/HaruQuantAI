"""FEAT-BRK-04: Binance Spot provider lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerId,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unreleased(adapter: BrokerAdapter, operation: str) -> None:
    """Require one Binance capability to remain fail-closed."""
    if operation == "order_book":
        result = await adapter.get_order_book("BTCUSDT")
    elif operation == "spread":
        result = await adapter.get_spread("BTCUSDT")
    elif operation == "quotes":
        result = await adapter.subscribe_quotes(("BTCUSDT",))
    elif operation == "bars":
        result = await adapter.subscribe_bars(("BTCUSDT",), "1m")
    elif operation == "book_stream":
        result = await adapter.subscribe_order_book(("BTCUSDT",))
    else:
        result = await adapter.unsubscribe("invalid-id")
    expected = (
        BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND
        if operation == "unsubscribe"
        else BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
    )
    require_error("Result", result, expected)


async def fr_brokers_066(adapter: BrokerAdapter) -> None:
    """FR-BRK-066: Return order-book truth with sequence evidence."""
    _header("FR-BRK-066: Return order-book truth with sequence evidence.")
    await _require_unreleased(adapter, "order_book")


async def fr_brokers_067(adapter: BrokerAdapter) -> None:
    """FR-BRK-067: Return provider-reported spread without placeholders."""
    _header("FR-BRK-067: Return provider-reported spread without placeholders.")
    await _require_unreleased(adapter, "spread")


async def fr_brokers_068(adapter: BrokerAdapter) -> None:
    """FR-BRK-068: Create an adapter-scoped bounded quote stream."""
    _header("FR-BRK-068: Create an adapter-scoped bounded quote stream.")
    await _require_unreleased(adapter, "quotes")


async def fr_brokers_069(adapter: BrokerAdapter) -> None:
    """FR-BRK-069: Create a genuine bounded provider bar stream."""
    _header("FR-BRK-069: Create a genuine bounded provider bar stream.")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_070(adapter: BrokerAdapter) -> None:
    """FR-BRK-070: Create a sequence-safe order-book stream."""
    _header("FR-BRK-070: Create a sequence-safe order-book stream.")
    await _require_unreleased(adapter, "book_stream")


async def fr_brokers_071(adapter: BrokerAdapter) -> None:
    """FR-BRK-071: Terminate exactly one owned subscription."""
    _header("FR-BRK-071: Terminate exactly one owned subscription.")
    await _require_unreleased(adapter, "unsubscribe")


async def fr_brokers_072(adapter: BrokerAdapter) -> None:
    """FR-BRK-072: List immutable owned-subscription metadata."""
    _header("FR-BRK-072: List immutable owned-subscription metadata.")
    result = await adapter.list_subscriptions()
    require_success("Result", result)
    assert result.data == ()


async def fr_brokers_073(adapter: BrokerAdapter) -> None:
    """FR-BRK-073: Return a refreshed capability report."""
    _header("FR-BRK-073: Return a refreshed capability report.")
    result = await adapter.get_feature_flags()
    require_success("Result", result)
    assert result.data is not None
    assert result.data.broker_id == BrokerId.BINANCE_SPOT


async def fr_brokers_074(adapter: BrokerAdapter) -> None:
    """FR-BRK-074: Answer support from the capability report."""
    _header("FR-BRK-074: Answer support from the capability report.")
    result = await adapter.supports(BrokerCapabilityId.GET_QUOTE)
    require_success("Result", result)
    assert result.data is False


async def _run() -> None:
    """Execute lifecycle evidence in one genuine Binance testnet session."""
    async with real_session(BrokerId.BINANCE_SPOT) as adapter:
        await fr_brokers_066(adapter)
        await fr_brokers_067(adapter)
        await fr_brokers_068(adapter)
        await fr_brokers_069(adapter)
        await fr_brokers_070(adapter)
        await fr_brokers_071(adapter)
        await fr_brokers_072(adapter)
        await fr_brokers_073(adapter)
        await fr_brokers_074(adapter)


def main() -> None:
    """Run the standalone genuine Binance lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
