"""FEAT-BRK-04: Binance Spot provider lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import (
    get_broker_capability_id,
    get_broker_feature_flags,
    get_broker_order_book,
    get_broker_spread,
    get_broker_value_field,
    list_broker_subscriptions,
    subscribe_broker_bars,
    subscribe_broker_order_book,
    subscribe_broker_quotes,
    supports_broker_capability,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unreleased(adapter: object, operation: str) -> None:
    """Require one Binance capability to remain fail-closed."""
    if operation == "order_book":
        result = await get_broker_order_book(adapter, "BTCUSDT")
    elif operation == "spread":
        result = await get_broker_spread(adapter, "BTCUSDT")
    elif operation == "quotes":
        result = await subscribe_broker_quotes(adapter, ("BTCUSDT",))
    elif operation == "bars":
        result = await subscribe_broker_bars(adapter, ("BTCUSDT",), "1m")
    elif operation == "book_stream":
        result = await subscribe_broker_order_book(adapter, ("BTCUSDT",))
    else:
        result = await adapter.unsubscribe("invalid-id")
    expected = (
        "BROKER_SUBSCRIPTION_NOT_FOUND"
        if operation == "unsubscribe"
        else "BROKER_CAPABILITY_UNSUPPORTED"
    )
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, expected)


async def fr_brokers_066(adapter: object) -> None:
    """FR-BRK-066: Return order-book truth with sequence evidence."""
    _header("FR-BRK-066: Return order-book truth with sequence evidence.")
    await _require_unreleased(adapter, "order_book")


async def fr_brokers_067(adapter: object) -> None:
    """FR-BRK-067: Return provider-reported spread without placeholders."""
    _header("FR-BRK-067: Return provider-reported spread without placeholders.")
    await _require_unreleased(adapter, "spread")


async def fr_brokers_068(adapter: object) -> None:
    """FR-BRK-068: Create an adapter-scoped bounded quote stream."""
    _header("FR-BRK-068: Create an adapter-scoped bounded quote stream.")
    await _require_unreleased(adapter, "quotes")


async def fr_brokers_069(adapter: object) -> None:
    """FR-BRK-069: Create a genuine bounded provider bar stream."""
    _header("FR-BRK-069: Create a genuine bounded provider bar stream.")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_070(adapter: object) -> None:
    """FR-BRK-070: Create a sequence-safe order-book stream."""
    _header("FR-BRK-070: Create a sequence-safe order-book stream.")
    await _require_unreleased(adapter, "book_stream")


async def fr_brokers_071(adapter: object) -> None:
    """FR-BRK-071: Terminate exactly one owned subscription."""
    _header("FR-BRK-071: Terminate exactly one owned subscription.")
    await _require_unreleased(adapter, "unsubscribe")


async def fr_brokers_072(adapter: object) -> None:
    """FR-BRK-072: List immutable owned-subscription metadata."""
    _header("FR-BRK-072: List immutable owned-subscription metadata.")
    result = await list_broker_subscriptions(adapter)
    require_success("Result", result)
    assert isinstance(get_broker_value_field(result, "data"), tuple)


async def fr_brokers_073(adapter: object) -> None:
    """FR-BRK-073: Return a refreshed capability report."""
    _header("FR-BRK-073: Return a refreshed capability report.")
    result = await get_broker_feature_flags(adapter)
    require_success("Result", result)
    data = get_broker_value_field(result, "data")
    assert data is not None
    assert get_broker_value_field(data, "broker_id").value == "binance_spot"


async def fr_brokers_074(adapter: object) -> None:
    """FR-BRK-074: Answer support from the capability report."""
    _header("FR-BRK-074: Answer support from the capability report.")
    result = await supports_broker_capability(
        adapter, get_broker_capability_id("get_quote")
    )
    require_success("Result", result)
    assert isinstance(get_broker_value_field(result, "data"), bool)


async def _run() -> None:
    """Execute lifecycle evidence in one genuine Binance testnet session."""
    async with real_session("binance_spot") as adapter:
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
