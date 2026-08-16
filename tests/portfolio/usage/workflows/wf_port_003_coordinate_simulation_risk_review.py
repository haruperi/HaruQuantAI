"""WF-PORT-003: coordinate Simulation and Risk review."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import execute_portfolio_handle_operation
from tests.portfolio.usage.workflows._support import (
    construction_workflow,
    simulation_request,
)

WORKFLOW_ID = "WF-PORT-003"
STAGES = (
    "Receive candidate, validated evidence, and PortfolioBacktestRequest.",
    "Revalidate Simulation request against candidate and evidence lineage.",
    "Submit the receiver-owned request and verify Simulation result.",
    "Build and submit the receiver-owned Risk review request.",
    "Return PortfolioReviewResult with trace and audit evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined review-coordination workflow."""
    service, request, _store, market = construction_workflow()
    candidate, evidence = execute_portfolio_handle_operation(
        service, "construct", request
    )
    receiver_request = simulation_request(candidate)
    print(
        "INPUT BOUNDARY — candidate/evidence/Simulation request:", candidate.result_id
    )

    # Stage 1 — Receive all three immutable typed boundaries.
    _stage(1)
    print("Real market lineage:", market.request_id)

    # Stage 2 — Bind every receiver field to the candidate.
    _stage(2)
    print("Simulation construction version:", receiver_request.construction_version)

    # Stage 3 — Submit to the Simulation receiver.
    _stage(3)
    print("Simulation route:", receiver_request.execution_route)

    # Stage 4 — Submit the derived Risk-owned review request.
    _stage(4)
    review = execute_portfolio_handle_operation(
        service,
        "coordinate_review",
        candidate,
        receiver_request,
        evidence,
    )

    # Stage 5 — Return current Simulation and Risk truth.
    _stage(5)
    print("Simulation status:", review.simulation.status)
    print("OUTPUT BOUNDARY — PortfolioReviewResult:", review.risk_decision.state.value)


if __name__ == "__main__":
    main()
