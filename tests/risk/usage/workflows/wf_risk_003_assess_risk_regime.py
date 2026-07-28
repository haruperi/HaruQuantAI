"""WF-RISK-003: assess current Risk regime from supplied evidence."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import assess_risk_regime
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-003"
STAGES = (
    "Accept portfolio and external volatility, liquidity, correlation, crisis, news, and session evidence.",
    "Validate required point-in-time evidence without fetching or extrapolating.",
    "Classify configured regime dimensions deterministically.",
    "Apply tightening modifiers and record transition evidence.",
    "Return RegimeAssessment or fail closed on required unknown evidence.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Data and governance owners supply typed evidence.
    _stage(1)
    config = examples._config().model_copy(update={"regime_assessment_enabled": True})
    market = examples._market().model_copy(update={"volatility": Decimal("0.03")})
    snapshot = examples._snapshot(config)
    print("Input volatility:", market.volatility)
    # Stage 2: Confirm point-in-time coverage.
    _stage(2)
    print("Evidence time:", market.as_of)
    # Stage 3: Run the public classifier.
    _stage(3)
    assessment = unwrap_risk_response(
        assess_risk_regime(snapshot, market, config, now=examples.NOW),
        operation="assess_risk_regime",
    )
    print("States:", dict(assessment.states))
    # Stage 4: Preserve modifiers and transitions.
    _stage(4)
    print(
        "Modifiers:", dict(assessment.modifiers), "transitions:", assessment.transitions
    )
    # Stage 5 — OUTPUT BOUNDARY: Return typed RegimeAssessment.
    _stage(5)
    print("Output:", type(assessment).__name__)


if __name__ == "__main__":
    main()
