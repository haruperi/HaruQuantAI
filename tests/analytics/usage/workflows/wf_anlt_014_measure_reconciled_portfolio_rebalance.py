"""WF-ANLT-014: measure reconciled portfolio rebalance execution."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import build_portfolio_rebalance_measurement
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-014"
STAGES = (
    "Accept hash-bound redacted successful Trading reconciliation facts.",
    "Validate contract identity, hashes, plan/allocation pairing, and successful outcomes.",
    "Calculate bounded execution measurement summaries without editing execution truth.",
    "Preserve Trading references and deterministic non-binding lineage.",
    "Return PortfolioRebalanceMeasurementEvidence v1.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Trading supplies redacted reconciled execution truth.
    _stage(1)
    request = examples._measurement_request()
    print("Input:", request.trading_execution_ref, request.plan_id)
    # Stage 2: Public builder validates hash-bound facts.
    _stage(2)
    print("Execution hash:", request.trading_execution_hash)
    # Stage 3: Calculate non-binding measurement evidence.
    _stage(3)
    evidence = examples.unwrap(build_portfolio_rebalance_measurement(request))
    print("Successful actions:", evidence.summary["successful_action_count"])
    # Stage 4: Preserve immutable Trading references.
    _stage(4)
    print(
        "Reference preserved:",
        evidence.trading_execution_ref == request.trading_execution_ref,
    )
    # Stage 5 — OUTPUT BOUNDARY: Return measurement evidence; execution remains unchanged.
    _stage(5)
    print("Output:", type(evidence).__name__, evidence.non_binding)


if __name__ == "__main__":
    main()
