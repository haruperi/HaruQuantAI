"""WF-PORT-007: roll back through a new governed allocation version."""

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

WORKFLOW_ID = "WF-PORT-007"
STAGES = (
    "Receive approved prior candidate, evidence, review, and rollback version.",
    "Revalidate approvals, Risk authorization, expiry, switch, and revision.",
    "Submit Risk's activation request for the rollback projection.",
    "Atomically activate a new version linked by rollback_of_version.",
    "Return new ActivePortfolioAllocation and redacted audit evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined rollback workflow."""
    service, request, _store, market = construction_workflow()
    candidate, evidence = service.construct(request)
    review = service.coordinate_review(
        candidate, simulation_request(candidate), evidence
    )
    historical = service.activate(
        candidate,
        evidence,
        review,
        approval_attestation=None,
        approval_validation=None,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="wf-port-007-original",
        expected_predecessor=None,
        expected_revision=0,
    )
    rollback_request = request.model_copy(
        update={"portfolio_version": "version-rollback"}
    )
    rollback_candidate, rollback_evidence = service.construct(rollback_request)
    rollback_review = service.coordinate_review(
        rollback_candidate,
        simulation_request(rollback_candidate),
        rollback_evidence,
    )
    print(
        "INPUT BOUNDARY — governed historical version:", historical.allocation_version
    )

    # Stage 1 — Receive the complete prior governed chain.
    _stage(1)
    print("Real market lineage:", market.request_id)

    # Stage 2 — Revalidate all mutable gates and the current revision.
    _stage(2)
    print("Expected predecessor/revision:", historical.allocation_version, 1)

    # Stage 3 — Submit a fresh Risk activation contract.
    _stage(3)
    print("Current Risk authorization:", review.risk_decision.decision_id)

    # Stage 4 — Activate a new immutable rollback-linked version.
    _stage(4)
    rolled_back = service.rollback(
        rollback_candidate,
        rollback_evidence,
        rollback_review,
        rollback_of_version=historical.allocation_version,
        approval_attestation=None,
        approval_validation=None,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="wf-port-007-rollback",
        expected_predecessor=historical.allocation_version,
        expected_revision=1,
    )

    # Stage 5 — Return the new governed state without mutating history.
    _stage(5)
    print("Rollback link:", rolled_back.rollback_of_version)
    print(
        "OUTPUT BOUNDARY — ActivePortfolioAllocation:", rolled_back.allocation_version
    )


if __name__ == "__main__":
    main()
