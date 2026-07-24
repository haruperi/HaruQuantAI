"""Integration test for allocation review and Risk-budget activation."""

from app.services.risk import (
    AllocationBudgetActivationRequest,
    DecisionState,
    KillSwitchState,
    RiskAuditChain,
    activate_allocation_budget,
    review_allocation_proposal,
)
from app.utils import canonical_json

from tests.risk import _support as examples
from tests.risk.integration.test_strategy_admission import _AuditStore


def test_allocation_review_and_activation_end_to_end() -> None:
    """Persist, audit, CAS-activate, and re-verify one exact allocation budget."""
    config = examples._config()
    audit_store = _AuditStore()
    audit = RiskAuditChain(config, audit_store, lambda: examples.NOW, canonical_json)
    allocation_store = examples._AllocationStore()
    decision = review_allocation_proposal(
        examples._allocation_request(config),
        examples._snapshot(config),
        examples._market(),
        config,
        allocation_store,
        audit,
        now=examples.NOW,
    )
    assert decision.state is DecisionState.APPROVE
    active = activate_allocation_budget(
        AllocationBudgetActivationRequest(
            portfolio_id="portfolio-1",
            allocation_version="allocation-v1",
            decision_id=decision.decision_id,
            scope={"portfolio_id": "portfolio-1"},
            effective_at=examples.NOW,
            predecessor_version=None,
            request_id=examples.REQUEST_ID,
            workflow_id=examples.WORKFLOW_ID,
            correlation_id=examples.CORRELATION_ID,
        ),
        decision,
        (
            KillSwitchState(
                state_id="kill-global",
                scope_level="global",
                scope={},
                state="inactive",
                reason="clear",
                version=1,
                updated_at=examples.NOW,
            ),
        ),
        config,
        allocation_store,
        audit,
        now=examples.NOW,
    )
    assert active.active is True
    assert allocation_store.active == active
    assert len(audit_store.records) == 2
    assert audit.verify(tuple(audit_store.records)) is True
