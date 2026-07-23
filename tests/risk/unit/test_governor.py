"""Unit tests for fixed-precedence canonical Risk governor behavior."""

from unittest.mock import patch

import pytest
from app.services.risk.contracts import DecisionState, RiskDomainError, RiskErrorCode
from app.services.risk.governor import RiskGovernor

from tests.risk import _support as examples
from tests.risk import _support as policy_examples


def test_governor_requires_live_dependencies() -> None:
    """Reject live capacity-guard ownership without its atomic dependency."""
    config = examples._config().model_copy(
        update={"profile": "live", "double_spend_owner": "capacity_guard"}
    )
    _, approvals, audit = examples._services(examples._config())
    with pytest.raises(RiskDomainError) as captured:
        RiskGovernor(config, approvals, audit, lambda: examples.NOW)
    assert captured.value.risk_code is RiskErrorCode.INVALID_RISK_CONFIG


def test_trade_review_truth_table_and_precedence() -> None:
    """Apply kill-switch before policy and require approval after passing checks."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    pending = governor.review_trade_risk(
        proposal,
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (examples._inactive_state(),),
        examples._auth(config),
        now=examples.NOW,
    )
    assert pending.state is DecisionState.NEEDS_APPROVAL
    active = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "operator stop"}
    )
    blocked = governor.review_trade_risk(
        proposal,
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (active,),
        examples._auth(config),
        attestation=examples._attestation(config),
        now=examples.NOW,
    )
    assert blocked.state is DecisionState.BLOCK
    assert blocked.ordered_checks[0].limit_id == "kill_switch"
    assert blocked.primary_failure_limit == "kill_switch"


def test_portfolio_governor_no_execution_mutation() -> None:
    """Return current compliance while preserving every supplied input."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(mode="python")
    decision = governor.run_portfolio_risk_governor(
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (examples._inactive_state(),),
        examples._auth(config),
        now=examples.NOW,
    )
    assert decision.state is DecisionState.APPROVE
    assert snapshot.model_dump(mode="python") == before
    assert decision.recommendations == ("no_remediation_required",)


def test_governor_logs_structured_material_decision_evidence() -> None:
    """Log trace, verdict, reason, latency, evidence, and config context."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    with patch("app.services.risk.governor.orchestration.logger") as mocked_logger:
        decision = governor.review_trade_risk(
            examples._proposal(config),
            examples._snapshot(config),
            policy_examples._market(),
            examples._regime(),
            (examples._inactive_state(),),
            examples._auth(config),
            now=examples.NOW,
        )
    context = mocked_logger.bind.call_args.kwargs
    assert context["request_id"] == decision.request_id
    assert context["workflow_id"] == decision.workflow_id
    assert context["correlation_id"] == decision.correlation_id
    assert context["verdict"] == decision.state.value
    assert "reason_codes" in context
    assert context["latency_ms"] >= 0
    assert context["evidence_refs"] == dict(decision.evidence_refs)
    assert context["config_hash"] == decision.config_hash
    mocked_logger.bind.return_value.info.assert_called_once_with(
        "Completed canonical trade Risk decision"
    )
