"""Unit tests for local utilities exceptions and payload validation."""

import pytest
from app.utils.standard import ConfigurationError
from app.utils.standard import SecurityError
from app.utils.standard import ValidationError
from app.utils.standard import (
    DataError,
    Error,
    ExternalServiceError,
    exception_to_error_payload,
    normalize_error_code,
    validate_error_payload,
)


def test_shared_exceptions_have_deterministic_attributes() -> None:
    cases = [
        (Error("unknown", code="UNKNOWN_ERROR"), "UNKNOWN_ERROR"),
        (ValidationError("bad input", code="VALIDATION_FAILED"), "VALIDATION_FAILED"),
        (ConfigurationError("missing config", code="SERVICE_UNAVAILABLE"), "SERVICE_UNAVAILABLE"),
        (SecurityError("blocked", code="PERMISSION_DENIED"), "PERMISSION_DENIED"),
        (DataError("not found", code="DATA_NOT_FOUND"), "DATA_NOT_FOUND"),
        (ExternalServiceError("down", code="SERVICE_UNAVAILABLE"), "SERVICE_UNAVAILABLE"),
    ]

    for error, expected_code in cases:
        assert error.code == expected_code
        assert str(error)


def test_normalize_error_code_is_safe_for_unknown_or_empty_codes() -> None:
    assert normalize_error_code("INVALID_EVENT") == "INVALID_EVENT"
    assert (normalize_code_default := normalize_error_code(None, default="TOOL_EXECUTION_FAILED")) == "TOOL_EXECUTION_FAILED"


def test_exception_to_error_payload_never_returns_raw_exception_objects() -> None:
    exception = RuntimeError("boom")

    payload = exception_to_error_payload(exception)

    assert payload == {"code": "TOOL_EXECUTION_FAILED", "details": "RuntimeError: boom"}
    assert isinstance(payload["details"], str)


def test_validate_error_payload_normalizes_and_rejects_malformed_payloads() -> None:
    assert validate_error_payload(
        {"code": "INVALID_INPUT", "details": "field is required"},
    ) == {"code": "INVALID_INPUT", "details": "field is required"}

    # Expect ValidationError on invalid payload keys or types
    with pytest.raises(ValidationError, match="error must contain exactly code and details"):
        validate_error_payload({"code": "INVALID_INPUT", "details": "field is required", "extra": "field"})

    with pytest.raises(ValidationError, match="details"):
        validate_error_payload({"code": "INVALID_INPUT", "details": ""})
