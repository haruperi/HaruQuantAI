"""FEAT-BRK-06: Yahoo research lifecycle and capability boundaries."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error
from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderFilter,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unsupported(adapter: BrokerAdapter, operation: str) -> None:
    """Require one non-Yahoo execution capability to remain unsupported."""
    if operation == "position":
        result = await adapter.get_position("p1")
    elif operation == "orders":
        result = await adapter.get_orders(BrokerOrderFilter())
    elif operation == "order":
        result = await adapter.get_order("o1")
    elif operation == "order_history":
        result = await adapter.list_order_history()
    elif operation == "deal_history":
        result = await adapter.list_deal_history()
    elif operation == "deal":
        result = await adapter.get_deal("d1")
    else:
        result = await adapter.list_account_transactions()
    require_error(
        "Result",
        result,
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_084(adapter: BrokerAdapter) -> None:
    """FR-BRK-084: Return one position or deterministic unsupported."""
    _header("FR-BRK-084: Return one position or deterministic unsupported.")
    await _require_unsupported(adapter, "position")


async def fr_brokers_085(adapter: BrokerAdapter) -> None:
    """FR-BRK-085: Return bounded orders or deterministic unsupported."""
    _header("FR-BRK-085: Return bounded orders or deterministic unsupported.")
    await _require_unsupported(adapter, "orders")


async def fr_brokers_086(adapter: BrokerAdapter) -> None:
    """FR-BRK-086: Return one order or deterministic unsupported."""
    _header("FR-BRK-086: Return one order or deterministic unsupported.")
    await _require_unsupported(adapter, "order")


async def fr_brokers_087(adapter: BrokerAdapter) -> None:
    """FR-BRK-087: Return order history or deterministic unsupported."""
    _header("FR-BRK-087: Return order history or deterministic unsupported.")
    await _require_unsupported(adapter, "order_history")


async def fr_brokers_088(adapter: BrokerAdapter) -> None:
    """FR-BRK-088: Return deal history or deterministic unsupported."""
    _header("FR-BRK-088: Return deal history or deterministic unsupported.")
    await _require_unsupported(adapter, "deal_history")


async def fr_brokers_089(adapter: BrokerAdapter) -> None:
    """FR-BRK-089: Return one deal or deterministic unsupported."""
    _header("FR-BRK-089: Return one deal or deterministic unsupported.")
    await _require_unsupported(adapter, "deal")


async def fr_brokers_090(adapter: BrokerAdapter) -> None:
    """FR-BRK-090: Return transactions or deterministic unsupported."""
    _header("FR-BRK-090: Return transactions or deterministic unsupported.")
    await _require_unsupported(adapter, "transactions")


async def _run() -> None:
    """Execute capability evidence after a genuine Yahoo sandbox probe."""
    async with real_session(BrokerId.YAHOO) as adapter:
        await fr_brokers_084(adapter)
        await fr_brokers_085(adapter)
        await fr_brokers_086(adapter)
        await fr_brokers_087(adapter)
        await fr_brokers_088(adapter)
        await fr_brokers_089(adapter)
        await fr_brokers_090(adapter)


def main() -> None:
    """Run the standalone genuine Yahoo lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
