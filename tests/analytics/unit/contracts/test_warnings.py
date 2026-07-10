"""Unit tests for analytics warnings and quality-flag catalogs and builders."""

from __future__ import annotations

import pytest
from app.services.analytics.contracts import (
    QUALITY_FLAG_CATALOG,
    WARNING_CATALOG,
    ExplainabilityOutput,
    build_quality_flag,
    build_warning,
    redact_sensitive_info,
)
from app.services.analytics.errors import AnalyticsValidationError as ValidationError


def test_catalogs_presence() -> None:
    """Test warning and quality flag catalogs are populated."""
    assert len(WARNING_CATALOG) > 0
    assert len(QUALITY_FLAG_CATALOG) > 0
    assert "LOW_SAMPLE_SIZE" in WARNING_CATALOG
    assert "LOW_PROFIT_FACTOR" in QUALITY_FLAG_CATALOG


def test_build_warning_success() -> None:
    """Test successful construction of an AnalyticsWarning."""
    warn = build_warning(
        code="LOW_SAMPLE_SIZE",
        source_context="Test context message",
        detail={"trade_count": 10, "min_trades": 30},
    )
    assert warn.code == "LOW_SAMPLE_SIZE"
    assert warn.severity == "warning"
    assert warn.affected_section == "trade_metrics"
    assert warn.source_context == "Test context message"
    assert warn.detail == {"trade_count": 10, "min_trades": 30}


def test_build_warning_invalid_code() -> None:
    """Test building a warning with an uncataloged code raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        build_warning("FABRICATED_CODE")
    assert "Unknown warning catalog code" in str(exc_info.value)


def test_build_warning_unbounded_detail() -> None:
    """Test detail dictionary violating bounded keys raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        build_warning(
            code="LOW_SAMPLE_SIZE",
            detail={"trade_count": 10, "unallowed_extra_key": "some_value"},
        )
    assert "is not allowed for warning" in str(exc_info.value)


def test_build_quality_flag_success() -> None:
    """Test successful construction of a QualityFlag scorecard entry."""
    flag = build_quality_flag(
        code="LOW_PROFIT_FACTOR",
        source_context="Scorecard check",
        detail={"profit_factor": 1.1, "threshold": 1.2},
    )
    assert flag.code == "LOW_PROFIT_FACTOR"
    assert flag.severity == "warning"
    assert flag.affected_section == "scorecard"
    assert flag.detail == {"profit_factor": 1.1, "threshold": 1.2}


def test_build_quality_flag_invalid_code() -> None:
    """Test building a quality flag with an uncataloged code raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        build_quality_flag("FABRICATED_CODE")
    assert "Unknown quality flag catalog code" in str(exc_info.value)


def test_build_quality_flag_unbounded_detail() -> None:
    """Test detail dictionary violating bounded keys raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        build_quality_flag(
            code="LOW_PROFIT_FACTOR",
            detail={"profit_factor": 1.1, "unallowed_extra_key": "some_value"},
        )
    assert "is not allowed for quality flag" in str(exc_info.value)


def test_sensitive_info_redaction() -> None:
    """Test recursion and value/key redaction rules (ANL-NFR-276)."""
    # Key-based redaction
    payload = {
        "api_key": "secret-api-key-12345",
        "secret_token": "token-12345",
        "password": "mypassword",
        "public_data": {
            "normal_key": "normal_val",
            "auth_key": "nested-sensitive-val",
        },
    }
    redacted = redact_sensitive_info(payload)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["secret_token"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["public_data"]["normal_key"] == "normal_val"
    assert redacted["public_data"]["auth_key"] == "[REDACTED]"

    # Value-based regex redaction (JWT format and 32-char hex string)
    jwt_val = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
    hex_val = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    assert redact_sensitive_info(jwt_val) == "[REDACTED]"
    assert redact_sensitive_info(hex_val) == "[REDACTED]"

    # Context string containing inline sensitive patterns
    sensitive_context = "connection failed for account_id: 998877"
    assert redact_sensitive_info(sensitive_context) == "[REDACTED]"


def test_build_warning_redacts_details() -> None:
    """Test build_warning applies redaction rules to input details."""
    warn = build_warning(
        code="DEGRADED_CONFIDENCE",
        source_context="api_key: secret-key",
        detail={
            "metric_name": "r_multiple",
            "fallback_reason": "account_id: 123456",
        },
    )
    assert warn.source_context == "[REDACTED]"
    assert warn.detail["fallback_reason"] == "[REDACTED]"


def test_explainability_output() -> None:
    """Test explainability output dataclass attributes (ANL-NFR-280)."""
    exp = ExplainabilityOutput(
        explained_pnl=500.0,
        unexplained_pnl=50.0,
        explained_variance_percentage=85.5,
        sample_count=100,
        driver_stability="high",
    )
    assert exp.explained_pnl == 500.0
    assert exp.unexplained_pnl == 50.0
    assert exp.explained_variance_percentage == 85.5
    assert exp.sample_count == 100
    assert exp.driver_stability == "high"
