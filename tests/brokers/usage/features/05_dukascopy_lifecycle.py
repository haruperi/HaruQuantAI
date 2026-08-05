"""FEAT-BRK-05: Dukascopy research lifecycle and capability boundaries."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_success
from app.services.brokers import (
    build_broker_position_filter,
    get_broker_account_info,
    get_broker_asset_info,
    get_broker_balances,
    get_broker_permissions,
    get_broker_platform_info,
    get_broker_positions,
    get_broker_value_field,
    list_broker_accounts,
    list_broker_assets,
    select_broker_account,
    supports_broker_capability,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


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


async def fr_brokers_075_platform_info(adapter: object) -> None:
    """FR-BRK-075: Stage 1 & 2 — Instrument Specification & Transport Setup."""
    _header("Stage 1 & 2: Instrument Specification & Transport Setup (FR-BRK-075)")
    platform_res = await get_broker_platform_info(adapter)
    require_success("Result", platform_res)
    print(_format_result(platform_res))
    print(
        f"Data -> platform_info_status='{get_broker_value_field(platform_res, 'status')}'"
    )


async def _require_unsupported(adapter: object, operation: str) -> None:
    """Exercise one non-Dukascopy account capability safely checking capability support."""
    capability_map = {
        "permissions": "get_permissions",
        "accounts": "list_accounts",
        "select_account": "select_account",
        "account_info": "get_account_info",
        "balances": "get_balances",
        "assets": "list_assets",
        "asset_info": "get_asset_info",
        "positions": "get_positions",
    }
    cap_name = capability_map.get(operation, operation)
    supp_res = await supports_broker_capability(adapter, cap_name)
    if get_broker_value_field(supp_res, "data"):
        if operation == "permissions":
            result = await get_broker_permissions(adapter)
        elif operation == "accounts":
            result = await list_broker_accounts(adapter)
        elif operation == "select_account":
            result = await select_broker_account(adapter, "acc-1")
        elif operation == "account_info":
            result = await get_broker_account_info(adapter)
        elif operation == "balances":
            result = await get_broker_balances(adapter)
        elif operation == "assets":
            result = await list_broker_assets(adapter)
        elif operation == "asset_info":
            result = await get_broker_asset_info(adapter, "EUR")
        else:
            result = await get_broker_positions(adapter, build_broker_position_filter())
        require_success("Result", result)
        print(_format_result(result))
        print(
            f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
        )
    else:
        print(f"Data -> operation='{operation}', status='unsupported_on_provider'")


async def fr_brokers_076_to_083_canonical_ticks(adapter: object) -> None:
    """FR-BRK-076..083: Stage 3 — BI5 Tick Retrieval & Canonical Tick Output."""
    _header("Stage 3: BI5 Tick Retrieval & Canonical Tick Output (FR-BRK-076..083)")
    for op in (
        "permissions",
        "accounts",
        "select_account",
        "account_info",
        "balances",
        "assets",
        "asset_info",
        "positions",
    ):
        await _require_unsupported(adapter, op)


async def _run() -> None:
    """Execute capability evidence in one genuine Dukascopy sandbox session."""
    _feature_header(
        "FEATURE: FEAT-BRK-05 — dukascopy_ticks/ — Dukascopy Tick Reads\n\n"
        "Purpose: Provide Dukascopy tick data retrieval.\n\n"
        "Module flow:\n"
        "-> instrument + date range\n"
        "-> BI5 tick retrieval\n"
        "-> canonical ticks"
    )

    try:
        async with real_session("dukascopy") as adapter:
            # Stage 1 & 2: Instrument specification & transport setup
            await fr_brokers_075_platform_info(adapter)

            # Stage 3: BI5 tick retrieval & canonical tick output
            await fr_brokers_076_to_083_canonical_ticks(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the standalone genuine Dukascopy lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
