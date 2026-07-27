"""WF-RISK-004: review a proposed trade using fixed Risk precedence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import DecisionState
from tests.risk.usage.workflows._support import examples

WORKFLOW_ID = "WF-RISK-004"
STAGES = (
    "Accept exact TradeIntent lineage, current evidence, auth, config, and full kill-switch hierarchy.",
    "Validate identity/config, kill switch, freshness, and required evidence in fixed precedence.",
    "Evaluate ordered hard limits, policy restrictions, concurrency, and approval eligibility.",
    "Build and durably audit the complete RiskDecisionPackage.",
    "Return RiskDecision v1 to Trading or Simulation without execution side effects.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Strategy/Data/governance evidence enters Risk.
    _stage(1)
    config = examples._config()
    governor, _, audit = examples._services(config)
    active = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    print("Input kill state:", active.state)
    # Stage 2: Fixed precedence starts with kill/freshness validation.
    _stage(2)
    print("Proposal intent:", examples._proposal(config).intent.intent_id)
    # Stage 3: Governor evaluates every applicable limit.
    _stage(3)
    decision = governor.review_trade_risk(
        examples._proposal(config),
        examples._snapshot(config),
        examples._market(),
        examples._regime(),
        (active,),
        examples._auth(config),
        attestation=examples._attestation(config),
        now=examples.NOW,
    )
    print("Verdict:", decision.state)
    # Stage 4: Verify auditable ordered failure evidence.
    _stage(4)
    print(
        "Primary failure:",
        decision.primary_failure_limit,
        "audit:",
        audit.records[-1].event_type,
    )
    # Stage 5 — OUTPUT BOUNDARY: Return RiskDecisionPackage only.
    _stage(5)
    print("Output:", type(decision).__name__, decision.state is DecisionState.BLOCK)


if __name__ == "__main__":
    main()
