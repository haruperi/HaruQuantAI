"""WF-RISK-007: review and activate an allocation Risk budget."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import (
    AllocationBudgetActivationRequest,
    KillSwitchState,
    RiskAuditChain,
    activate_allocation_budget,
    review_allocation_proposal,
)
from app.utils import canonical_json
from tests.risk.integration.test_strategy_admission import _AuditStore
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-007"
STAGES = (
    "Accept self-contained allocation projection and current eligibility/account/market/Analytics evidence.",
    "Review allocation limits and persist AllocationRiskDecision.",
    "Accept exact activation request plus current kill-switch hierarchy.",
    "CAS-activate the authoritative Risk-budget projection and audit it.",
    "Return active budget evidence without constructing weights or executing rebalance orders.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Portfolio submits its immutable allocation projection.
    _stage(1)
    config = examples._config()
    audit_store = _AuditStore()
    audit = RiskAuditChain(config, audit_store, lambda: examples.NOW, canonical_json)
    store = examples._AllocationStore()
    request = examples._allocation_request(config)
    print("Input:", request.portfolio_id, request.portfolio_version)
    # Stage 2: Review and persist Risk-owned allocation truth.
    _stage(2)
    decision = unwrap_risk_response(
        review_allocation_proposal(
            request,
            examples._snapshot(config),
            examples._market(),
            config,
            store,
            audit,
            now=examples.NOW,
        ),
        operation="review_allocation_proposal",
    )
    print("Review:", decision.state)
    # Stage 3: Bind activation to exact decision.
    _stage(3)
    activation = AllocationBudgetActivationRequest(
        portfolio_id="portfolio-1",
        allocation_version="allocation-v1",
        decision_id=decision.decision_id,
        scope={"portfolio_id": "portfolio-1"},
        effective_at=examples.NOW,
        predecessor_version=None,
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    states = (
        KillSwitchState(
            state_id="kill-global",
            scope_level="global",
            scope={},
            state="inactive",
            reason="clear",
            version=1,
            updated_at=examples.NOW,
        ),
    )
    # Stage 4: Activate through public CAS boundary.
    _stage(4)
    active = unwrap_risk_response(
        activate_allocation_budget(
            activation, decision, states, config, store, audit, now=examples.NOW
        ),
        operation="activate_allocation_budget",
    )
    print(
        "Active/audit:",
        active.active,
        unwrap_risk_response(
            audit.verify(tuple(audit_store.records)), operation="risk_audit.verify"
        ),
    )
    # Stage 5 — OUTPUT BOUNDARY: Return authoritative Risk budget projection.
    _stage(5)
    print("Output:", type(active).__name__, active.decision_id)


if __name__ == "__main__":
    main()
