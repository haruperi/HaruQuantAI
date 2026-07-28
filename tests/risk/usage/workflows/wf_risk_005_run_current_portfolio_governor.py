"""WF-RISK-005: run the current-state portfolio Risk governor."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import DecisionState
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-005"
STAGES = (
    "Accept current snapshot, market, regime, complete kill hierarchy, auth, and config.",
    "Validate current evidence and evaluate portfolio-wide limits.",
    "Recommend approve, block, reduction, or review without mutating execution.",
    "Persist the material decision to the Risk audit chain.",
    "Return current-state RiskDecisionPackage to Trading/UI/API.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Current Risk and governance evidence.
    _stage(1)
    config = examples._config()
    governor, _, audit = examples._services(config)
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(mode="python")
    print("Input snapshot:", snapshot.snapshot_id)
    # Stage 2: Execute portfolio compliance validation.
    _stage(2)
    decision = unwrap_risk_response(
        governor.run_portfolio_risk_governor(
            snapshot,
            examples._market(),
            examples._regime(),
            (examples._inactive_state(),),
            examples._auth(config),
            now=examples.NOW,
        ),
        operation="risk_governor.run_portfolio_risk_governor",
    )
    print("Decision:", decision.state)
    # Stage 3: Verify no execution or snapshot mutation.
    _stage(3)
    print("Input unchanged:", before == snapshot.model_dump(mode="python"))
    # Stage 4: Verify durable audit evidence.
    _stage(4)
    print("Audit decision:", audit.records[-1].decision_id)
    # Stage 5 — OUTPUT BOUNDARY: Return advisory current-state decision.
    _stage(5)
    print("Output:", type(decision).__name__, decision.state is DecisionState.APPROVE)


if __name__ == "__main__":
    main()
