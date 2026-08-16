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
    raw_secret = "provider password=hunter2"  # pragma: allowlist secret
    envelope = map_trading_error(
        ConnectionError(raw_secret),
        {
            "operation": "submit_order",
            "provider_id": "demo-provider",
            "request_id": "req-001",
            "correlation_id": "corr-001",
            "api_key": "top-secret",  # pragma: allowlist secret
        },
    )
    serialized = envelope.model_dump_json()
    assert envelope.status == "error"
    assert envelope.error is not None
    assert envelope.error.code == "UNKNOWN_OUTCOME"
    assert raw_secret not in serialized
    assert "top-secret" not in serialized
    classifications = (
        (ValueError("unsafe detail"), "VALIDATION_FAILED"),
        (PermissionError("unsafe detail"), "PERMISSION_DENIED"),
        (OSError("unsafe detail"), "PERSISTENCE_FAILED"),
        (RuntimeError("unsafe detail"), "UNKNOWN_ERROR"),
        (
            TradingError("UNKNOWN_OUTCOME", "Authority state is unknown"),
            "UNKNOWN_OUTCOME",
        ),
    )
    for error, code in classifications:
        classified = map_trading_error(error, {"operation": "unit_test"})
        assert classified.status == "error"
        assert classified.error is not None
        assert classified.error.code == code


def test_redaction_is_recursive_and_case_insensitive() -> None:
    """Sensitive keys are redacted recursively without case dependence."""
    payload = {
        "outer": {
            "Api_Key": "secret-one",  # pragma: allowlist secret
            "items": [  # pragma: allowlist secret
                {"PASSWORD": "secret-two"},  # pragma: allowlist secret
            ],
        }
    }
    redacted = redact_trading_payload(payload)
    rendered = str(redacted.data)
    assert "secret-one" not in rendered
    assert "secret-two" not in rendered
    assert rendered.count("[REDACTED]") == 2


def test_redaction_removes_embedded_secret_text() -> None:
    """Secret assignments embedded in free text are removed recursively."""
    redacted = redact_trading_payload(
        {
            "message": "provider failed: password=hunter2 api_key=abcd",
            "nested": ["token=very-secret"],
        }
    )
    rendered = str(redacted.data)
    assert "hunter2" not in rendered
    assert "abcd" not in rendered
    assert "very-secret" not in rendered
