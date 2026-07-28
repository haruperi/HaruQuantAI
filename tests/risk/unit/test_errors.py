"""Unit tests for the Risk boundary error contract."""

import pytest
from app.services.risk.contracts import RiskDomainError, RiskErrorCode
from app.services.risk.contracts.catalog import RISK_ERROR_CATALOG


def test_error_code_catalog() -> None:
    """Keep the approved V1 error-code catalog exhaustive."""
    assert len(RiskErrorCode) == 33
    assert RiskErrorCode.APPROVAL_TOKEN_CONSUMED.value == "APPROVAL_TOKEN_CONSUMED"
    assert set(RISK_ERROR_CATALOG) == {code.value for code in RiskErrorCode}
    with pytest.raises(TypeError):
        RISK_ERROR_CATALOG[RiskErrorCode.UNKNOWN_ERROR.value] = RISK_ERROR_CATALOG[
            RiskErrorCode.UNKNOWN_ERROR.value
        ]


def test_domain_error_redacts_details() -> None:
    """Redact secret assignments from boundary-safe details."""
    error = RiskDomainError(RiskErrorCode.INVALID_INPUT, "api_token=secret")
    assert "secret" not in error.details
    assert error.risk_code is RiskErrorCode.INVALID_INPUT
