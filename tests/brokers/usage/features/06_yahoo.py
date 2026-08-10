"""FEAT-BRK-06: Yahoo direct broker channel."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import real_session, require_success
from app.services.brokers import (
    build_broker_order_filter,
    get_broker_deal,
    get_broker_order,
    get_broker_orders,
    get_broker_position,
    get_broker_value_field,
    list_broker_account_transactions,
    list_broker_deal_history,
    list_broker_order_history,
    supports_broker_capability,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


async def _require_unsupported(adapter: object, operation: str) -> None:
    """Exercise one non-Yahoo execution capability safely checking capability support."""
    capability_map = {
        "position": "get_position",
        "orders": "get_orders",
        "order": "get_order",
        "order_history": "list_order_history",
        "deal_history": "list_deal_history",
        "deal": "get_deal",
        "transactions": "list_account_transactions",
    }
    cap_name = capability_map.get(operation, operation)
    supp_res = await supports_broker_capability(adapter, cap_name)
    if get_broker_value_field(supp_res, "data"):
        if operation == "position":
            result = await get_broker_position(adapter, "p1")
        elif operation == "orders":
            result = await get_broker_orders(adapter, build_broker_order_filter())
        elif operation == "order":
            result = await get_broker_order(adapter, "o1")
        elif operation == "order_history":
            result = await list_broker_order_history(adapter)
        elif operation == "deal_history":
            result = await list_broker_deal_history(adapter)
        elif operation == "deal":
            result = await get_broker_deal(adapter, "d1")
        else:
            result = await list_broker_account_transactions(adapter)
        require_success("Result", result)
        print(_format_result(result))
        print(
            f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
        )
    else:
        print(f"Data -> operation='{operation}', status='unsupported_on_provider'")


async def fr_brokers_084(adapter: object) -> None:
    """FR-BRK-084: Return one position or deterministic unsupported."""
    _header("FR-BRK-084: Return one position or deterministic unsupported.")
    await _require_unsupported(adapter, "position")


async def fr_brokers_085(adapter: object) -> None:
    """FR-BRK-085: Return bounded orders or deterministic unsupported."""
    _header("FR-BRK-085: Return bounded orders or deterministic unsupported.")
    await _require_unsupported(adapter, "orders")


async def fr_brokers_086(adapter: object) -> None:
    """FR-BRK-086: Return one order or deterministic unsupported."""
    _header("FR-BRK-086: Return one order or deterministic unsupported.")
    await _require_unsupported(adapter, "order")


async def fr_brokers_087(adapter: object) -> None:
    """FR-BRK-087: Return order history or deterministic unsupported."""
    _header("FR-BRK-087: Return order history or deterministic unsupported.")
    await _require_unsupported(adapter, "order_history")


async def fr_brokers_088(adapter: object) -> None:
    """FR-BRK-088: Return deal history or deterministic unsupported."""
    _header("FR-BRK-088: Return deal history or deterministic unsupported.")
    await _require_unsupported(adapter, "deal_history")


async def fr_brokers_089(adapter: object) -> None:
    """FR-BRK-089: Return one deal or deterministic unsupported."""
    _header("FR-BRK-089: Return one deal or deterministic unsupported.")
    await _require_unsupported(adapter, "deal")


async def fr_brokers_090(adapter: object) -> None:
    """FR-BRK-090: Return transactions or deterministic unsupported."""
    _header("FR-BRK-090: Return transactions or deterministic unsupported.")
    await _require_unsupported(adapter, "transactions")


async def _run() -> None:
    """Execute capability evidence after a genuine Yahoo sandbox probe."""
    async with real_session("yahoo") as adapter:
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
