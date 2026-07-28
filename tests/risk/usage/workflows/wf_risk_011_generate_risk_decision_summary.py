"""WF-RISK-011: generate a focused Risk decision summary."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import generate_risk_report
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-011"
STAGES = (
    "Accept completed snapshot, decision, or scenario evidence.",
    "Separate evidence, calculations, assumptions, warnings, and recommendations.",
    "Place the primary block/rejection reason before the verdict.",
    "Claim live approval only when valid decision and token evidence are present.",
    "Return focused Markdown or JSON RiskReport.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Reporting receives one completed Risk decision.
    _stage(1)
    config = examples._config()
    governor, _, _ = examples._services(config)
    active = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "operator safety stop"}
    )
    decision = unwrap_risk_response(
        governor.review_trade_risk(
            examples._proposal(config),
            examples._snapshot(config),
            examples._market(),
            examples._regime(),
            (active,),
            examples._auth(config),
            attestation=examples._attestation(config),
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    print("Input decision:", decision.decision_id)
    # Stage 2: Public report builder separates evidence.
    _stage(2)
    report = unwrap_risk_response(
        generate_risk_report(decision, "markdown", config, now=examples.NOW),
        operation="generate_risk_report",
    )
    print("Evidence lines:", len(report.evidence))
    # Stage 3: Primary failure precedes verdict.
    _stage(3)
    print("Decision order:", report.decision[:2])
    # Stage 4: No token means no approval claim.
    _stage(4)
    print("Approval claimed:", report.approval_claimed)
    # Stage 5 — OUTPUT BOUNDARY: Return typed RiskReport.
    _stage(5)
    print("Output:", type(report).__name__, report.format)


if __name__ == "__main__":
    main()
