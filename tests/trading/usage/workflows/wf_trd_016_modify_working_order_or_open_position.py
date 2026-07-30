"""WF-TRD-016: modify governed working-order and position state."""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import modify_order, modify_position
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-016"
STAGES = (
    "Accept approved modification requests bound to current Trading state.",
    "Validate optimistic version, instrument evidence, and mutable-field authority.",
    "Dispatch one working-order modification through the selected Simulation route.",
    "Dispatch one approved stop-loss modification without changing exposure.",
    "Return exact receipts and persisted projections without blind retry.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the governed modification workflow."""
    # Stage 1 — INPUT BOUNDARY: exact current order and position targets.
    _stage(1)
    order_store = examples.execution_store()
    order_request = examples.trading_request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    print(
        "Order input:",
        order_request.target_broker_order_id,
        "version:",
        order_request.expected_version,
    )
    # Stage 2: Policy and exact Risk-approved quantity stay bound.
    _stage(2)
    print(
        "Approved quantity:",
        order_request.quantity,
        "idempotency:",
        order_request.idempotency_key,
    )
    # Stage 3: Execute exactly one simulated order modification.
    _stage(3)
    order_result = await modify_order(
        order_request,
        examples.trading_dependencies(store=order_store),
    )
    assert order_result.data is not None
    print(
        "Order receipt:",
        order_result.data.receipt_id,
        order_result.data.status,
        order_result.data.requested_quantity,
    )
    # Stage 4: Modify only the Risk-authorized stop-loss field.
    _stage(4)
    position_store = examples.execution_store()
    position_request = examples.trading_request(
        action="modify_position",
        order_type="LIMIT",
        position_id="position-001",
        target_broker_position_id="position-001",
        expected_version=1,
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0000"),
    )
    position_result = await modify_position(
        position_request,
        examples.trading_dependencies(
            store=position_store,
            action_policy=examples.action_policy(
                "modify_position",
                mutable_fields="stop_loss",
            ),
        ),
    )
    assert position_result.data is not None
    print(
        "Position receipt:",
        position_result.data.receipt_id,
        position_result.data.status,
        "stop_loss:",
        position_request.stop_loss,
    )
    # Stage 5 — OUTPUT BOUNDARY: exact persisted receipt truth.
    _stage(5)
    print(
        "Output:",
        order_result.status,
        position_result.status,
        "order events:",
        tuple(event.event_type for event in order_store.events),
        "position events:",
        tuple(event.event_type for event in position_store.events),
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
