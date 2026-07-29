"""WF-BRK-005: read genuine bounded MT5 account and execution state."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers.contracts import BrokerErrorCode, BrokerId
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
    adapter = create_real_adapter(BrokerId.MT5)
    try:
        require_success("MT5 connect", await adapter.connect())

        # Stage 1 — Read account identity, permissions, balances, and assets.
        _stage(1)
        require_success("Platform", await adapter.get_platform_info())
        require_success("Permissions", await adapter.get_permissions())
        require_error(
            "Account list",
            await adapter.list_accounts(limit=5),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )
        require_success("Account", await adapter.get_account_info())
        require_success("Balances", await adapter.get_balances())
        require_error(
            "Assets",
            await adapter.list_assets(limit=5),
            BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
        )

        # Stage 2 — Read bounded positions and pending orders.
        _stage(2)
        require_success("Positions", await adapter.get_positions(limit=5))
        require_success("Orders", await adapter.get_orders(limit=5))

        # Stage 3 — Read bounded order, deal, and transaction history.
        _stage(3)
        end = datetime.now(UTC)
        start = end - timedelta(days=7)
        require_success(
            "Order history",
            await adapter.list_order_history(start=start, end=end, limit=5),
        )
        require_success(
            "Deal history",
            await adapter.list_deal_history(start=start, end=end, limit=5),
        )
        require_success(
            "Transactions",
            await adapter.list_account_transactions(start=start, end=end, limit=5),
        )

        # Stage 4 — Return canonical provider truth with explicit missing-target evidence.
        _stage(4)
        require_error(
            "Missing position",
            await adapter.get_position("0"),
            BrokerErrorCode.BROKER_POSITION_NOT_FOUND,
        )
        require_error(
            "Missing order",
            await adapter.get_order("0"),
            BrokerErrorCode.BROKER_ORDER_NOT_FOUND,
        )
        require_error(
            "Missing deal",
            await adapter.get_deal("0"),
            BrokerErrorCode.BROKER_DEAL_NOT_FOUND,
        )
    finally:
        require_success("MT5 disconnect", await adapter.disconnect())
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
