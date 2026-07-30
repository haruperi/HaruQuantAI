"""WF-RISK-014: revalidate prior Risk evidence before reuse."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import revalidate_risk_decision, review_trade_risk
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-014"
STAGES = (
    "Accept prior decision/token plus current proposal, evidence, config, and injected time.",
    "Recompute immutable proposal and evidence bindings.",
    "Check expiry, skew, staleness, config, reconciliation, revocation, and consumption.",
    "Invalidate reuse on any material change.",
    "Return reusable/refresh-required/blocked truth without downstream mutation.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented fail-closed workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller presents a prior decision and changed proposal.
    _stage(1)
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal, snapshot = examples._proposal(config), examples._snapshot(config)
    decision = unwrap_risk_response(
        review_trade_risk(
            governor,
            proposal,
            snapshot,
            examples._market(),
            examples._regime(),
            (examples._inactive_state(),),
            examples._auth(config),
            attestation=examples._attestation(config),
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    changed = proposal.model_copy(update={"requested_size": Decimal(2)})
    print("Input sizes:", proposal.requested_size, changed.requested_size)
    # Stage 2: Public revalidator recomputes binding material.
    _stage(2)
    print("Prior decision:", decision.decision_id)
    # Stage 3: All reuse validity dimensions are checked.
    _stage(3)
    response = revalidate_risk_decision(
        decision, changed, snapshot, config, now=examples.NOW
    )
    if response.status != "error" or response.error is None:
        raise RuntimeError("Materially changed proposal was unexpectedly reusable")
    print("Revalidation:", response.error.code)
    # Stage 4: Material change requires a fresh decision.
    _stage(4)
    print("Reuse invalidated:", True)
    # Stage 5 — OUTPUT BOUNDARY: Return blocked/refresh-required truth.
    _stage(5)
    print("Output:", type(response).__name__, response.error.code)


if __name__ == "__main__":
    main()
