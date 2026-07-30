"""WF-TRD-005: classify and resolve an unknown route outcome."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    build_broker_state_unknown_event,
    classify_authority_response,
    emit_runtime_event,
    resolve_unknown_outcome,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-005"
STAGES = (
    "Accept a conservatively classified unknown ExecutionReceipt.",
    "Persist retry lock and obtain authority snapshots.",
    "Compare authority truth and retain unresolved conflict scope.",
    "Build and emit one critical BROKER_STATE_UNKNOWN OperationalEvent after persistence.",
    "Return AuthorityResolution with retry locked until authority truth resolves.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Timeout/malformed authority response is already unknown.
    _stage(1)
    raw_response = {
        "receipt_id": "receipt-001",
        "intent_id": "intent-001",
        "client_order_id": "client-order-001",
        "route": "sim",
        "authority": "simulator",
        "status": "success",
        "requested_quantity": "1.00",
        "filled_quantity": "0",
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "authority_timestamp": examples.NOW.isoformat(),
        "received_at": examples.NOW.isoformat(),
        "timed_out": True,
    }
    receipt_response = classify_authority_response(
        raw_response,
        {
            "malformed_response_policy": "unknown_outcome",
            "mutation_retry_policy": "reconcile_before_retry",
        },
    )
    assert receipt_response.status == "success"
    assert receipt_response.data is not None
    receipt = receipt_response.data
    print("Input:", receipt.response_classification, receipt.reconciliation_required)
    # Stage 2: Persist lock before authority comparison.
    _stage(2)
    store = examples.AuthorityStore(
        examples.authority_projection(orders={"order-internal": {"state": "pending"}})
    )
    resolution_response = resolve_unknown_outcome(
        receipt, store, lambda _route: examples.authority_snapshot()
    )
    assert resolution_response.status == "success"
    assert resolution_response.data is not None
    resolution = resolution_response.data
    print("Transition:", resolution.transition)
    # Stage 3: Keep unresolved scope explicit.
    _stage(3)
    print(
        "Retry allowed:",
        resolution.retry_allowed,
        "scope:",
        resolution.remaining_unresolved_scope,
    )
    # Stage 4: Build and emit the critical event after durable transition.
    _stage(4)
    event_response = build_broker_state_unknown_event(
        receipt,
        incident_id=resolution.incident_reference,
        unresolved_scope=resolution.remaining_unresolved_scope,
        occurred_at=examples.authority_snapshot().observed_at,
        workflow_id=store.events[-1].workflow_id,
    )
    assert event_response.status == "success"
    assert event_response.data is not None
    event = event_response.data
    published = []
    emitted = emit_runtime_event(event, published.append)
    assert emitted.status == "success"
    print("Event:", published[0].event_type, published[0].severity)
    # Stage 5 — OUTPUT BOUNDARY: Return locked resolution and incident evidence.
    _stage(5)
    print("Output:", type(resolution).__name__, resolution.transition)


if __name__ == "__main__":
    main()
