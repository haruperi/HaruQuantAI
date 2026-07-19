"""Workflow integration test for fixed-precedence proposed-trade review."""

from app.services.risk.contracts import DecisionState

from tests.risk.usage import test_usage_decisions as examples
from tests.risk.usage import test_usage_policy as policy_examples


def test_trade_review_uses_fixed_precedence_and_fails_closed() -> None:
    """Block active kill state before otherwise healthy policy and approval."""
    config = examples._config()
    governor, _, audit = examples._services(config)
    active = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    decision = governor.review_trade_risk(
        examples._proposal(config),
        examples._snapshot(config),
        policy_examples._market(),
        examples._regime(),
        (active,),
        examples._auth(config),
        attestation=examples._attestation(config),
        now=examples.NOW,
    )
    assert decision.state is DecisionState.BLOCK
    assert decision.primary_failure_limit == "kill_switch"
    assert decision.token is None
    assert audit.records[-1].event_type == "risk.governor.decision"
