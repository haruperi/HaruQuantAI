"""WF-BRK-TER: prove the current fail-closed broker mutation workflow."""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
)
from tests.brokers.usage._support import (
    create_real_adapter,
    require_error,
    require_success,
)

WORKFLOW_ID = "WF-BRK-TER"
STAGES = (
    "Verify the genuine MT5 target is a non-production demo session.",
    "Construct one complete caller-owned mutation request.",
    "Call every released mutation boundary without retry.",
    "Return deterministic unavailable evidence without provider transmission.",
)


def _order() -> BrokerOrderRequest:
    """Return one complete request that is never transmitted."""
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )


async def run() -> None:
    """Execute current mutation gates without creating provider state."""
    print(f"{WORKFLOW_ID} — Submit One Broker Mutation")
    print("INPUT BOUNDARY — complete approved demo mutation request")

    # Stage 1 — Verify the genuine MT5 target is a non-production demo session.
    _stage(1)
    verified = create_real_adapter(BrokerId.MT5)
    try:
        require_success("MT5 connect", await verified.connect())
        require_success("Demo account status", await verified.get_connection_status())
    finally:
        require_success("MT5 verification disconnect", await verified.disconnect())

    # Stage 2 — Construct one complete caller-owned mutation request.
    _stage(2)
    request = _order()
    assert request.environment == BrokerEnvironment.DEMO
    adapter = create_real_adapter(BrokerId.MT5)

    # Stage 3 — Call every released mutation boundary without retry.
    _stage(3)
    require_error(
        "Check order",
        await adapter.check_order(request),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )
    require_error(
        "Place order",
        await adapter.place_order(request),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )
    require_error(
        "Modify order",
        await adapter.modify_order(
            BrokerOrderModificationRequest(
                order_id="workflow-order", limit_price=Decimal(1)
            )
        ),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )
    require_error(
        "Cancel order",
        await adapter.cancel_order("workflow-order"),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )
    require_error(
        "Modify position",
        await adapter.modify_position(
            BrokerPositionModificationRequest(
                position_id="workflow-position", stop_loss=Decimal(1)
            )
        ),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )
    require_error(
        "Close position",
        await adapter.close_position(
            BrokerPositionCloseRequest(
                position_id="workflow-position",
                quantity=Decimal("0.01"),
                quantity_unit="lots",
            )
        ),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )
    require_error(
        "Replace order",
        await adapter.replace_order("workflow-order", request),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )

    # Stage 4 — Return deterministic unavailable evidence without provider transmission.
    _stage(4)
    require_success("Disconnected cleanup", await adapter.disconnect())
    print("No broker mutation was transmitted")
    print("OUTPUT BOUNDARY — canonical unavailable results for Trading reconciliation")


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
