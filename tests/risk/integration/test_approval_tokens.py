"""Workflow integration test for durable live approval-token consumption."""

import pytest
from app.services.risk import RiskDomainError, RiskErrorCode

from tests.risk import _support as examples


def test_live_token_is_consumed_once_durably() -> None:
    """Persist issuance and permit exactly one live workflow consumption."""
    service, store, decision, attestation = examples._values(live=True)
    token = examples.unwrap_risk_response(
        service.issue(decision, attestation, now=examples.NOW),
        operation="approval_token_service.issue",
    )
    expected = examples._expected(token)
    result = examples.unwrap_risk_response(
        service.validate_reserve_and_consume(
            token, attestation, expected, now=examples.NOW
        ),
        operation="approval_token_service.validate_reserve_and_consume",
    )
    assert result.valid is True
    assert result.consumed is True
    assert token.token_id in store.consumed
    with pytest.raises(RiskDomainError) as captured:
        examples.unwrap_risk_response(
            service.validate_reserve_and_consume(
                token, attestation, expected, now=examples.NOW
            ),
            operation="approval_token_service.validate_reserve_and_consume",
        )
    assert captured.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_CONSUMED
