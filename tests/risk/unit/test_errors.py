"""Unit tests for the Risk boundary error contract."""

from app.services.risk.contracts import RiskDomainError, RiskErrorCode


def test_error_code_catalog() -> None:
    """Keep the approved V1 error-code catalog exhaustive."""
    assert len(RiskErrorCode) == 33
    assert RiskErrorCode.APPROVAL_TOKEN_CONSUMED.value == "APPROVAL_TOKEN_CONSUMED"


def test_domain_error_redacts_details() -> None:
    """Redact secret assignments from boundary-safe details."""
    error = RiskDomainError(RiskErrorCode.INVALID_INPUT, "api_token=secret")
    assert "secret" not in error.details
    assert error.risk_code is RiskErrorCode.INVALID_INPUT
