"""Unit tests for Trading errors and redaction."""

# ruff: noqa: INP001

import pytest
from app.services.trading.contracts import (
    TradingError,
    map_trading_error,
    redact_trading_payload,
)


def test_trading_error_rejects_unknown_code() -> None:
    """TradingError accepts only registered finite codes."""
    with pytest.raises(ValueError, match="registered Trading error code"):
        TradingError("NOT_REGISTERED", "invalid code")


def test_map_trading_error_redacts_provider_exception() -> None:
    """Raw provider exception content never enters the canonical envelope."""
    raw_secret = "provider password=hunter2"
    envelope = map_trading_error(
        ConnectionError(raw_secret),
        {
            "operation": "submit_order",
            "provider_id": "paper-provider",
            "request_id": "req-001",
            "correlation_id": "corr-001",
            "api_key": "top-secret",
        },
    )
    serialized = envelope.model_dump_json()
    assert envelope.status == "unknown_outcome"
    assert raw_secret not in serialized
    assert "top-secret" not in serialized
    classifications = (
        (ValueError("unsafe detail"), "VALIDATION_FAILED", "error"),
        (PermissionError("unsafe detail"), "PERMISSION_DENIED", "error"),
        (OSError("unsafe detail"), "PERSISTENCE_FAILED", "error"),
        (RuntimeError("unsafe detail"), "UNKNOWN_ERROR", "error"),
        (
            TradingError("UNKNOWN_OUTCOME", "Authority state is unknown"),
            "UNKNOWN_OUTCOME",
            "unknown_outcome",
        ),
    )
    for error, code, status in classifications:
        classified = map_trading_error(error, {"operation": "unit_test"})
        assert classified.status == status
        assert classified.errors[0]["code"] == code


def test_redaction_is_recursive_and_case_insensitive() -> None:
    """Sensitive keys are redacted recursively without case dependence."""
    payload = {
        "outer": {
            "Api_Key": "secret-one",
            "items": [{"PASSWORD": "secret-two"}],
        }
    }
    redacted = redact_trading_payload(payload)
    rendered = str(redacted)
    assert "secret-one" not in rendered
    assert "secret-two" not in rendered
    assert rendered.count("[REDACTED]") == 2
