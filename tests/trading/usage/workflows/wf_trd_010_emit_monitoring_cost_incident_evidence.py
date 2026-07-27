"""WF-TRD-010: enforce budget and emit operational incident evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    BudgetGate,
    OperationalEvent,
    TradingError,
    emit_runtime_event,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-010"
STAGES = (
    "Accept runtime health, staleness, timeout, latency, cost, budget, and incident facts.",
    "Validate Risk-owned allocation budget before send.",
    "Build redacted Trading-owned OperationalEvent evidence.",
    "Deliver event and surface an incident if the sink fails.",
    "Return visible monitoring/incident truth without hiding execution state.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented fail-visible workflow."""
    # Stage 1 — INPUT BOUNDARY: Runtime supplies budget/operational facts.
    _stage(1)
    request = examples.monitoring_request()
    print("Input:", request.request_id, "actions:", len(request.actions))
    # Stage 2: BudgetGate fails closed on explicit denial.
    _stage(2)
    denied = type(examples.monitoring_verdict(request)).model_validate(
        {
            **examples.monitoring_verdict(request).model_dump(mode="python"),
            "allowed": False,
            "reasons": ("blocked",),
        }
    )
    try:
        BudgetGate.validate(
            request, examples.monitoring_allocation(), denied, now=examples.NOW
        )
    except TradingError as error:
        print("Budget:", error.code)
    # Stage 3: Build redacted operational event.
    _stage(3)
    event = OperationalEvent(
        event_id="event-001",
        event_type="COST_OBSERVED",
        severity="warning",
        occurred_at=examples.NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        facts={"cost": "1.25"},
        source_refs={"receipt": "receipt-001"},
    )
    print("Event:", event.event_type)
    # Stage 4: Sink failure remains visible.
    _stage(4)
    delivered = []

    def sink(value):
        delivered.append(value)
        raise RuntimeError("sink unavailable")

    try:
        emit_runtime_event(event, sink)
    except TradingError as delivery:
        print("Delivery:", delivery.code)
    # Stage 5 — OUTPUT BOUNDARY: Return attempted event plus incident evidence.
    _stage(5)
    print("Output events:", tuple(value.event_type for value in delivered))


if __name__ == "__main__":
    main()
