"""Security integration tests for Risk token and kill-switch non-bypass."""

from app.services.risk import (
    check_risk_kill_switch,
    get_decision_state,
    issue_risk_approval_token,
    validate_risk_approval_token,
)

from tests.risk import _support as approval_examples
from tests.risk import _support as decision_examples


def test_token_tamper_scope_and_replay_fail_closed() -> None:
    """Reject signature tamper, expected-scope bypass, and second consumption."""
    service, _, decision, attestation = approval_examples._values(live=True)
    token = approval_examples.unwrap_risk_response(
        issue_risk_approval_token(
            service,
            decision,
            attestation,
            now=approval_examples.NOW,
        ),
        operation="approval_token_service.issue",
    )
    expected = approval_examples._expected(token)
    tampered = token.model_copy(update={"signature": "0" * 64})
    signature_response = validate_risk_approval_token(
        service,
        tampered,
        attestation,
        expected,
        now=approval_examples.NOW,
    )
    assert signature_response.status == "error"
    assert signature_response.error.code == "APPROVAL_TOKEN_INVALID"
    wrong_scope = dict(expected)
    wrong_scope["symbol"] = "GBPUSD"
    scope_response = validate_risk_approval_token(
        service,
        token,
        attestation,
        wrong_scope,
        now=approval_examples.NOW,
    )
    assert scope_response.status == "error"
    assert scope_response.error.code == "APPROVAL_TOKEN_INVALID"
    result = approval_examples.unwrap_risk_response(
        validate_risk_approval_token(
            service,
            token,
            attestation,
            expected,
            now=approval_examples.NOW,
        ),
        operation="approval_token_service.validate_reserve_and_consume",
    )
    assert result.valid is True
    replay_response = validate_risk_approval_token(
        service,
        token,
        attestation,
        expected,
        now=approval_examples.NOW,
    )
    assert replay_response.status == "error"
    assert replay_response.error.code == "APPROVAL_TOKEN_CONSUMED"


def test_active_parent_kill_switch_cannot_be_bypassed() -> None:
    """Block risk increase regardless of inactive child or reconciliation flag."""
    config = decision_examples._config()
    parent = decision_examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    decision = decision_examples.unwrap_risk_response(
        check_risk_kill_switch(
            (parent, decision_examples._inactive_state("symbol")),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            decision_examples._auth(config),
            reconciled=True,
            now=decision_examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    assert decision.state is get_decision_state("BLOCK")
    assert decision.ordered_checks[0].reason_code.value == "KILL_SWITCH_ACTIVE"
