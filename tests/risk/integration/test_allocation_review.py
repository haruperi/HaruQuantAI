"""Integration test for allocation review and Risk-budget activation."""

from app.services.risk import (
    activate_allocation_budget,
    create_allocation_budget_activation_request,
    create_kill_switch_state,
    create_risk_audit_chain,
    get_decision_state,
    review_allocation_proposal,
)
from app.utils import canonical_json

from tests.risk import _support as examples
from tests.risk.integration.test_strategy_admission import _AuditStore


def test_allocation_review_and_activation_end_to_end() -> None:
    """Persist, audit, CAS-activate, and re-verify one exact allocation budget."""
    config = examples._config()
    audit_store = _AuditStore()
    audit = create_risk_audit_chain(
        config,
        audit_store,
        lambda: examples.NOW,
        canonical_json,
    )
    allocation_store = examples._AllocationStore()
    decision = examples.unwrap_risk_response(
        review_allocation_proposal(
            examples._allocation_request(config),
            examples._snapshot(config),
            examples._market(),
            config,
            allocation_store,
            audit,
            now=examples.NOW,
        ),
        operation="review_allocation_proposal",
    )
    assert decision.state is get_decision_state("APPROVE")
    active = examples.unwrap_risk_response(
        activate_allocation_budget(
            create_allocation_budget_activation_request(
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
                create_kill_switch_state(
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
        ),
        operation="activate_allocation_budget",
    )
    assert active.active is True
    assert allocation_store.active == active
    assert len(audit_store.records) == 2
    assert (
        examples.unwrap_risk_response(
            audit.verify(tuple(audit_store.records)),
            operation="risk_audit_chain.verify",
        )
        is True
    )
