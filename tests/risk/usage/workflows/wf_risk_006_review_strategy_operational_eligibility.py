"""WF-RISK-006: review Strategy operational eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.kernel.serialization import canonical_json
from app.services.risk import (
    create_risk_audit_chain,
    create_strategy_operational_eligibility_request,
    review_strategy_admission,
    verify_risk_audit_chain,
)
from tests.risk.integration.test_strategy_admission import _AuditStore
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-006"
STAGES = (
    "Accept eligibility request, exact registration, Data evidence, policy, route, and auth context.",
    "Validate immutable identity plus fresh operational evidence.",
    "Approve, condition, expire, suspend, or reject use without altering Strategy registry.",
    "Persist decision and sealed audit evidence through injected stores.",
    "Return StrategyOperationalEligibilityDecision v1.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Registered Strategy asks Risk for operational eligibility.
    _stage(1)
    config = examples._config()
    request = create_strategy_operational_eligibility_request(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        runtime_profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        registration_ref=examples.HASH_B,
        evidence_refs={"market": examples.MARKET_REQUEST_ID},
        approval_refs=(),
        requested_scope={"symbol": "EURUSD"},
        requested_at=examples.NOW,
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    print("Input:", request.strategy_id, request.execution_route)
    # Stage 2: Prepare current immutable evidence.
    _stage(2)
    audit_store = _AuditStore()
    audit = create_risk_audit_chain(
        config, audit_store, lambda: examples.NOW, canonical_json
    )
    eligibility_store = examples._EligibilityStore()
    # Stage 3: Execute the public admission review.
    _stage(3)
    decision = unwrap_risk_response(
        review_strategy_admission(
            request,
            examples._registration(),
            examples._market(),
            config,
            eligibility_store,
            audit,
            now=examples.NOW,
        ),
        operation="review_strategy_admission",
    )
    print("Decision:", decision.state)
    # Stage 4: Verify persisted sealed evidence.
    _stage(4)
    print(
        "Audit valid:",
        unwrap_risk_response(
            verify_risk_audit_chain(audit, tuple(audit_store.records)),
            operation="verify_risk_audit_chain",
        ),
    )
    # Stage 5 — OUTPUT BOUNDARY: Return typed eligibility decision.
    _stage(5)
    print("Output:", type(decision).__name__, decision.decision_id)


if __name__ == "__main__":
    main()
