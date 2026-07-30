"""WF-BRK-005: read genuine bounded MT5 account and execution state."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_account_info,
    get_broker_balances,
    get_broker_deal,
    get_broker_order,
    get_broker_orders,
    get_broker_permissions,
    get_broker_platform_info,
    get_broker_position,
    get_broker_positions,
    get_broker_value_field,
    list_broker_account_transactions,
    list_broker_accounts,
    list_broker_assets,
    list_broker_deal_history,
    list_broker_order_history,
)
from tests.brokers.usage._support import (
    create_real_adapter,
    require_error,
    require_success,
)

WORKFLOW_ID = "WF-BRK-005"
STAGES = (
    "Read account identity, permissions, balances, and assets.",
    "Read bounded positions and pending orders.",
    "Read bounded order, deal, and transaction history.",
    "Return canonical provider truth with explicit missing-target evidence.",
)


async def run() -> None:
    """Execute all account and execution-state read families."""
    print(f"{WORKFLOW_ID} — Read Account and Execution State")
    print("INPUT BOUNDARY — bounded MT5 account-state request")
    adapter = create_real_adapter("mt5")
    try:
        require_success("MT5 connect", await connect_broker(adapter))

        # Stage 1 — Read account identity, permissions, balances, and assets.
        _stage(1)
        require_success("Platform", await get_broker_platform_info(adapter))
        require_success("Permissions", await get_broker_permissions(adapter))
        acc_list = await list_broker_accounts(adapter, limit=5)
        if get_broker_value_field(acc_list, "status") == "success":
            require_success("Account list", acc_list)
        else:
            require_error("Account list", acc_list, "BROKER_CAPABILITY_UNSUPPORTED")

        require_success("Account", await get_broker_account_info(adapter))
        require_success("Balances", await get_broker_balances(adapter))
        assets_res = await list_broker_assets(adapter, limit=5)
        if get_broker_value_field(assets_res, "status") == "success":
            require_success("Assets", assets_res)
        else:
            require_error("Assets", assets_res, "BROKER_CAPABILITY_UNSUPPORTED")

        # Stage 2 — Read bounded positions and pending orders.
        _stage(2)
        require_success("Positions", await get_broker_positions(adapter))
        require_success("Orders", await get_broker_orders(adapter))

        # Stage 3 — Read bounded order, deal, and transaction history.
        _stage(3)
        end = datetime.now(UTC)
        start = end - timedelta(days=7)
        require_success(
            "Order history",
            await list_broker_order_history(
                adapter,
                start_time=start,
                end_time=end,
                limit=5,
            ),
        )
        require_success(
            "Deal history",
            await list_broker_deal_history(
                adapter,
                start_time=start,
                end_time=end,
                limit=5,
            ),
        )
        require_success(
            "Transactions",
            await list_broker_account_transactions(
                adapter,
                start_time=start,
                end_time=end,
                limit=5,
            ),
        )

        # Stage 4 — Return canonical provider truth with explicit missing-target evidence.
        _stage(4)
        pos_res = await get_broker_position(adapter, "0")
        if get_broker_value_field(pos_res, "status") == "error":
            require_error(
                "Missing position",
                pos_res,
                "BROKER_POSITION_NOT_FOUND",
                "BROKER_CAPABILITY_UNSUPPORTED",
            )
        else:
            require_success("Missing position", pos_res)

        ord_res = await get_broker_order(adapter, "0")
        if get_broker_value_field(ord_res, "status") == "error":
            require_error(
                "Missing order",
                ord_res,
                "BROKER_ORDER_NOT_FOUND",
                "BROKER_CAPABILITY_UNSUPPORTED",
            )
        else:
            require_success("Missing order", ord_res)

        deal_res = await get_broker_deal(adapter, "0")
        if get_broker_value_field(deal_res, "status") == "error":
            require_error(
                "Missing deal",
                deal_res,
                "BROKER_DEAL_NOT_FOUND",
                "BROKER_CAPABILITY_UNSUPPORTED",
            )
        else:
            require_success("Missing deal", deal_res)
    finally:
        require_success("MT5 disconnect", await disconnect_broker(adapter))
    print("OUTPUT BOUNDARY — bounded canonical account/order/position/deal evidence")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
