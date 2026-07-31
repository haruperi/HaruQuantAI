"""FEAT-BRK-09: genuine bounded execution-history reads."""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import (
    UsageEvidenceError,
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    disconnect_broker,
    get_broker_deal,
    get_broker_value_field,
    list_broker_account_transactions,
    list_broker_deal_history,
    list_broker_order_history,
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


def _range() -> tuple[datetime, datetime]:
    """Return one bounded recent UTC history window."""
    end = datetime.now(UTC)
    return end - timedelta(days=7), end


async def fr_brokers_105_to_108_provider_pagination(adapter: object) -> None:
    """FR-BRK-105..108: Stage 1 & 2 — History Filter and Provider Pagination."""
    _header("Stage 1 & 2: History Filter & Provider Pagination (FR-BRK-105..108)")
    start, end = _range()
    ord_res = await list_broker_order_history(
        adapter, start_time=start, end_time=end, limit=5
    )
    require_success("Result", ord_res)
    print(_format_result(ord_res))
    print(f"Data -> order_history_status='{get_broker_value_field(ord_res, 'status')}'")

    deal_res = await list_broker_deal_history(
        adapter, start_time=start, end_time=end, limit=5
    )
    require_success("Result", deal_res)
    print(_format_result(deal_res))
    print(f"Data -> deal_history_status='{get_broker_value_field(deal_res, 'status')}'")

    get_deal_res = await get_broker_deal(adapter, "0")
    require_error(
        "Result", get_deal_res, "BROKER_DEAL_NOT_FOUND", "BROKER_CAPABILITY_UNSUPPORTED"
    )
    print(_format_result(get_deal_res))
    print(f"Data -> get_deal_status='{get_broker_value_field(get_deal_res, 'status')}'")

    tx_res = await list_broker_account_transactions(
        adapter, start_time=start, end_time=end, limit=5
    )
    require_success("Result", tx_res)
    print(_format_result(tx_res))
    print(
        f"Data -> transaction_history_status='{get_broker_value_field(tx_res, 'status')}'"
    )


async def fr_brokers_109_to_111_canonical_history_pages(disconnected: object) -> None:
    """FR-BRK-109..111: Stage 3 — Canonical History Page Output and Disconnected Safety."""
    _header("Stage 3: Canonical History Pages & Disconnected Safety (FR-BRK-109..111)")
    start, end = _range()
    dis_res = await list_broker_order_history(
        disconnected, start_time=start, end_time=end, limit=5
    )
    require_error("Result", dis_res, "BROKER_NOT_CONNECTED")
    print(_format_result(dis_res))
    print(
        f"Data -> disconnected_order_history_status='{get_broker_value_field(dis_res, 'status')}'"
    )


async def _run() -> None:
    """Execute genuine MT5 history reads and the disconnected safety gate."""
    _feature_header(
        "FEATURE: FEAT-BRK-09 — execution_history/ — Execution History Reads\n\n"
        "Purpose: Provide order, deal, and transaction history reads across MT5 and cTrader.\n\n"
        "Module flow:\n"
        "-> history filter\n"
        "-> provider pagination\n"
        "-> canonical history page"
    )

    try:
        async with real_session("mt5") as adapter:
            # Stage 1 & 2: History filter and provider pagination
            await fr_brokers_105_to_108_provider_pagination(adapter)

        disconnected = create_real_adapter("mt5")
        # Stage 3: Canonical history page output and safety gates
        await fr_brokers_109_to_111_canonical_history_pages(disconnected)

        clean_res = await disconnect_broker(disconnected)
        require_success("Final cleanup", clean_res)
        print(_format_result(clean_res))
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine MT5 history program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
