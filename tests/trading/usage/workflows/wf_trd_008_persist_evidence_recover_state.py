"""WF-TRD-008: persist execution evidence and recover state."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    apply_execution_event,
    create_trading_event,
    get_trading_migrations,
    reserve_idempotency,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-008"
STAGES = (
    "Accept versioned Trading event and injected state store.",
    "Expose the authoritative Trading migration manifest.",
    "Reserve idempotency before any send-attempt transition.",
    "Apply event atomically and reconstruct the projection.",
    "Return recovered projection with unresolved attempts explicitly retry-locked.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Versioned event enters injected Trading state port.
    _stage(1)
    store = examples.MemoryStore()
    event = create_trading_event(
        event_id="attempt-001",
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        occurred_at=examples.NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        payload={"client_order_id": "client-001"},
    )
    print("Input event:", event.event_type)
    # Stage 2: Read authoritative migrations.
    _stage(2)
    migrations = get_trading_migrations()
    assert migrations.data is not None
    print("Migrations:", len(migrations.data), migrations.data[0])
    # Stage 3: Reserve idempotency before send.
    _stage(3)
    request = examples.live_gate_request()
    reservation_response = reserve_idempotency(
        request,
        store,
        reservation_time=event.occurred_at,
        retention_seconds=600,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert reservation_response.data is not None
    print(
        "Reservation:",
        reservation_response.data.status,
        reservation_response.data.material_hash,
    )
    # Stage 4: Apply and reconstruct.
    _stage(4)
    projection_response = apply_execution_event(event, store)
    assert projection_response.data is not None
    projection = projection_response.data
    print("Projection version:", projection.version)
    # Stage 5 — OUTPUT BOUNDARY: Return retry-locked recovered state.
    _stage(5)
    print("Output:", type(projection).__name__, projection.unresolved_attempt_ids)


if __name__ == "__main__":
    main()
