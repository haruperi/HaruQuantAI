"""Workflow integration test for durable live approval-token consumption."""

from app.services.risk import (
    issue_risk_approval_token,
    validate_risk_approval_token,
)

from tests.risk import _support as examples


def test_live_token_is_consumed_once_durably() -> None:
    """Persist issuance and permit exactly one live workflow consumption."""
    service, store, decision, attestation = examples._values(live=True)
    token = examples.unwrap_risk_response(
        issue_risk_approval_token(
            service,
            decision,
            attestation,
            now=examples.NOW,
        ),
        operation="approval_token_service.issue",
    )
    expected = examples._expected(token)
    result = examples.unwrap_risk_response(
        validate_risk_approval_token(
            service,
            token,
            attestation,
            expected,
            now=examples.NOW,
        ),
        operation="approval_token_service.validate_reserve_and_consume",
    )
    assert result.valid is True
    assert result.consumed is True
    assert token.token_id in store.consumed
    replay = validate_risk_approval_token(
        service,
        token,
        attestation,
        expected,
        now=examples.NOW,
    )
    assert replay.status == "error"
    assert replay.error.code == "APPROVAL_TOKEN_CONSUMED"
