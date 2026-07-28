"""WF-PORT-SEC: activate one governed Portfolio allocation."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.portfolio.usage.workflows._support import (
    NOW,
    construction_workflow,
    simulation_request,
)

WORKFLOW_ID = "WF-PORT-SEC"
STAGES = (
    "Re-read candidate and expected current allocation revision.",
    "Revalidate eligibility, Simulation, Risk, expiry, approval, and kill switch.",
    "Submit AllocationBudgetActivationRequest to Risk.",
    "Atomically activate one Portfolio allocation version.",
    "Emit redacted audit evidence and return ActivePortfolioAllocation.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined allocation-activation workflow."""
    service, request, store, market = construction_workflow()
    candidate, evidence = service.construct(request)
    review = service.coordinate_review(
        candidate, simulation_request(candidate), evidence
    )
    print("INPUT BOUNDARY — all current activation gates:", candidate.result_id)

    # Stage 1 — Re-read the expected empty active revision.
    _stage(1)
    print("Expected predecessor/revision:", None, 0)

    # Stage 2 — Revalidate every mutable gate.
    _stage(2)
    print("Real Data evidence still bound:", market.request_id)

    # Stage 3 — Submit Risk's activation contract.
    _stage(3)
    print("Risk decision:", review.risk_decision.decision_id)

    # Stage 4 — Execute the atomic activation workflow.
    _stage(4)
    active = service.activate(
        candidate,
        evidence,
        review,
        approval_attestation=None,
        approval_validation=None,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="wf-port-004-activation",
        expected_predecessor=None,
        expected_revision=0,
    )

    # Stage 5 — Return governed state with audit lineage.
    _stage(5)
    assert store.active_scopes
    print("OUTPUT BOUNDARY — ActivePortfolioAllocation:", active.allocation_version)


if __name__ == "__main__":
    main()
