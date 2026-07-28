"""Security integration tests for Risk token and kill-switch non-bypass."""

import pytest
from app.services.risk import (
    DecisionState,
    RiskDomainError,
    RiskErrorCode,
    check_risk_kill_switch,
)

from tests.risk import _support as approval_examples
from tests.risk import _support as decision_examples


def test_token_tamper_scope_and_replay_fail_closed() -> None:
    """Reject signature tamper, expected-scope bypass, and second consumption."""
    service, _, decision, attestation = approval_examples._values(live=True)
    token = approval_examples.unwrap_risk_response(
        service.issue(decision, attestation, now=approval_examples.NOW),
        operation="approval_token_service.issue",
    )
    expected = approval_examples._expected(token)
    tampered = token.model_copy(update={"signature": "0" * 64})
    with pytest.raises(RiskDomainError) as signature_error:
        approval_examples.unwrap_risk_response(
            service.validate_reserve_and_consume(
                tampered, attestation, expected, now=approval_examples.NOW
            ),
            operation="approval_token_service.validate_reserve_and_consume",
        )
    assert signature_error.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_INVALID
    wrong_scope = dict(expected)
    wrong_scope["symbol"] = "GBPUSD"
    with pytest.raises(RiskDomainError) as scope_error:
        approval_examples.unwrap_risk_response(
            service.validate_reserve_and_consume(
                token, attestation, wrong_scope, now=approval_examples.NOW
            ),
            operation="approval_token_service.validate_reserve_and_consume",
        )
    assert scope_error.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_INVALID
    result = approval_examples.unwrap_risk_response(
        service.validate_reserve_and_consume(
            token, attestation, expected, now=approval_examples.NOW
        ),
        operation="approval_token_service.validate_reserve_and_consume",
    )
    assert result.valid is True
    with pytest.raises(RiskDomainError) as replay_error:
        approval_examples.unwrap_risk_response(
            service.validate_reserve_and_consume(
                token, attestation, expected, now=approval_examples.NOW
            ),
            operation="approval_token_service.validate_reserve_and_consume",
        )
    assert replay_error.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_CONSUMED


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
    assert decision.state is DecisionState.BLOCK
    assert decision.ordered_checks[0].reason_code is RiskErrorCode.KILL_SWITCH_ACTIVE
