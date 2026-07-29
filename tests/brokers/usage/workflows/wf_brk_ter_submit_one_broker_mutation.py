"""WF-BRK-TER: prove the current fail-closed broker mutation workflow."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    cancel_broker_order,
    check_broker_order,
    close_broker_position,
    connect_broker,
    disconnect_broker,
    get_broker_connection_status,
    get_broker_value_field,
    modify_broker_order,
    modify_broker_position,
    place_broker_order,
    replace_broker_order,
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


def _order() -> object:
    """Return one complete request that is never transmitted."""
    return build_broker_order_request("EURUSD", "BUY", "MARKET", "0.01", "lots", "demo")


async def run() -> None:
    """Execute current mutation gates without creating provider state."""
    print(f"{WORKFLOW_ID} — Submit One Broker Mutation")
    print("INPUT BOUNDARY — complete approved demo mutation request")

    # Stage 1 — Verify the genuine MT5 target is a non-production demo session.
    _stage(1)
    verified = create_real_adapter("mt5")
    try:
        require_success("MT5 connect", await connect_broker(verified))
        require_success(
            "Demo account status", await get_broker_connection_status(verified)
        )
    finally:
        require_success(
            "MT5 verification disconnect", await disconnect_broker(verified)
        )

    # Stage 2 — Construct one complete caller-owned mutation request.
    _stage(2)
    request = _order()
    assert get_broker_value_field(request, "environment") == "demo"
    adapter = create_real_adapter("mt5")

    # Stage 3 — Call every released mutation boundary without retry.
    _stage(3)
    require_error(
        "Check order",
        await check_broker_order(adapter, request),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )
    require_error(
        "Place order",
        await place_broker_order(adapter, request),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )
    require_error(
        "Modify order",
        await modify_broker_order(
            adapter,
            build_broker_order_modification_request(
                "workflow-order", limit_price="1.0"
            ),
        ),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )
    require_error(
        "Cancel order",
        await cancel_broker_order(adapter, "workflow-order"),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )
    require_error(
        "Modify position",
        await modify_broker_position(
            adapter,
            build_broker_position_modification_request(
                "workflow-position", stop_loss="1.0"
            ),
        ),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )
    require_error(
        "Close position",
        await close_broker_position(
            adapter,
            build_broker_position_close_request("workflow-position", "0.01", "lots"),
        ),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )
    require_error(
        "Replace order",
        await replace_broker_order(
            adapter,
            build_broker_order_modification_request(
                "workflow-order", limit_price="1.0"
            ),
        ),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )

    # Stage 4 — Return deterministic unavailable evidence without provider transmission.
    _stage(4)
    require_success("Final cleanup", await disconnect_broker(adapter))
    print("OUTPUT BOUNDARY — verified mutation-blocking evidence")
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
