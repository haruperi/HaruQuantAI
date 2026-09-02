"""Unit tests for capability failure reason codes, structured error payloads, and projections.

Traces to: P7-T01, Gate G7
"""

from __future__ import annotations

import json

import pytest
from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    CapabilityUnavailableError,
    ConfigurationError,
    ExternalServiceError,
    HaruQuantError,
    SecurityError,
    ValidationError,
    capability_unavailable_payload,
    create_validation_error,
    get_common_error_catalog,
    map_exception,
    normalize_error_code,
    validate_error_catalog,
)


def test_capability_reason_code_has_all_13_exact_members() -> None:
    """Verify CapabilityReasonCode enum defines exactly the 13 declared standard members."""
    expected_members = {
        "NOT_INSTALLED",
        "DISABLED",
        "VERSION_INCOMPATIBLE",
        "DEPENDENCY_UNAVAILABLE",
        "PROVIDER_AMBIGUOUS",
        "CONFIG_INVALID",
        "ACTIVATION_FAILED",
        "UNHEALTHY",
        "DRAINING",
        "LOST_DURING_OPERATION",
        "PROFILE_REQUIREMENT_UNSATISFIED",
        "POLICY_BLOCKED",
        "CLEANUP_FAILED",
    }
    actual_members = {code.value for code in CapabilityReasonCode}
    assert actual_members == expected_members
    assert len(CapabilityReasonCode) == 13


def test_haruquant_error_token_validation() -> None:
    """Verify HaruQuantError validates code and detail tokens."""
    err = HaruQuantError("VALID_CODE", "VALID_DETAIL")
    assert err.code == "VALID_CODE"
    assert err.detail == "VALID_DETAIL"
    assert str(err) == "VALID_CODE:VALID_DETAIL"

    # Derived error classes
    assert isinstance(ConfigurationError("CONFIG_CODE"), HaruQuantError)
    assert isinstance(ValidationError("VAL_CODE"), HaruQuantError)
    assert isinstance(SecurityError("SEC_CODE"), HaruQuantError)
    assert isinstance(ExternalServiceError("EXT_CODE"), HaruQuantError)

    # Invalid code token
    with pytest.raises(ValueError, match="code must be an uppercase symbolic token"):
        HaruQuantError("invalid-code")

    # Invalid detail token
    with pytest.raises(ValueError, match="detail must be an uppercase symbolic token"):
        HaruQuantError("VALID_CODE", "invalid-detail")


def test_capability_unavailable_payload_contains_all_9_fields_and_preserves_nulls() -> (
    None
):
    """Verify projection contains all 9 fields with exact keys, types, and explicit nulls."""
    detail = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.NOT_INSTALLED,
        capability="indicator.rsi.v1",
        consumer=None,
        provider_id=None,
        provider_state=None,
        profile="research",
        dependency_chain=("indicator.rsi.v1",),
        retryable=False,
    )

    payload = capability_unavailable_payload(detail)

    assert payload == {
        "code": "CAPABILITY_UNAVAILABLE",
        "reason_code": "NOT_INSTALLED",
        "capability": "indicator.rsi.v1",
        "consumer": None,
        "provider_id": None,
        "provider_state": None,
        "profile": "research",
        "dependency_chain": ["indicator.rsi.v1"],
        "retryable": False,
    }


def test_capability_unavailable_payload_converts_dependency_chain_to_list() -> None:
    """Verify dependency_chain tuple is serialized to a standard Python list."""
    detail = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.DEPENDENCY_UNAVAILABLE,
        capability="data.market.v1",
        consumer="indicator.rsi.v1",
        provider_id="data.market.default",
        provider_state="FAILED",
        profile="simulation",
        dependency_chain=("indicator.rsi.v1", "data.market.v1"),
        retryable=True,
    )

    payload = capability_unavailable_payload(detail)
    assert isinstance(payload["dependency_chain"], list)
    assert payload["dependency_chain"] == ["indicator.rsi.v1", "data.market.v1"]
    assert payload["retryable"] is True


def test_capability_unavailable_payload_raises_value_error_if_chain_does_not_end_with_capability() -> (
    None
):
    """Verify dependency_chain validation enforces chain terminates with target capability."""
    detail_empty = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.NOT_INSTALLED,
        capability="indicator.rsi.v1",
        consumer=None,
        provider_id=None,
        provider_state=None,
        profile=None,
        dependency_chain=(),
        retryable=False,
    )
    with pytest.raises(ValueError, match=r"dependency_chain must end with capability"):
        capability_unavailable_payload(detail_empty)

    detail_mismatch = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.NOT_INSTALLED,
        capability="indicator.rsi.v1",
        consumer=None,
        provider_id=None,
        provider_state=None,
        profile=None,
        dependency_chain=("other.cap.v1",),
        retryable=False,
    )
    with pytest.raises(ValueError, match=r"dependency_chain must end with capability"):
        capability_unavailable_payload(detail_mismatch)


def test_capability_unavailable_payload_is_json_serializable() -> None:
    """Verify projected payload dumps directly to valid JSON string without custom encoders."""
    detail = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.POLICY_BLOCKED,
        capability="execution.order.v1",
        consumer="strategy.momentum.v1",
        provider_id="execution.live.default",
        provider_state="ACTIVE",
        profile="live",
        dependency_chain=("strategy.momentum.v1", "execution.order.v1"),
        retryable=False,
    )

    payload = capability_unavailable_payload(detail)
    serialized = json.dumps(payload)
    parsed = json.loads(serialized)

    assert parsed == payload


def test_capability_unavailable_error_message_is_exact() -> None:
    """Verify CapabilityUnavailableError formatting matches specification."""
    detail = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.VERSION_INCOMPATIBLE,
        capability="data.feed.v2",
        consumer=None,
        provider_id=None,
        provider_state=None,
        profile=None,
        dependency_chain=("data.feed.v2",),
        retryable=False,
    )

    err = CapabilityUnavailableError(detail)
    assert str(err) == "capability data.feed.v2 unavailable (VERSION_INCOMPATIBLE)"
    assert err.detail == detail

    # Test initialization with plain string
    err_str = CapabilityUnavailableError("data.feed.v2")
    assert "capability data.feed.v2 unavailable (NOT_INSTALLED)" in str(err_str)
    assert err_str.detail.capability == "data.feed.v2"


def test_error_utility_functions() -> None:
    """Verify create_validation_error, normalize_error_code, and error catalogs."""
    val_err = create_validation_error("VALIDATION_ERROR", details={"field": "symbol"})
    assert isinstance(val_err, ValidationError)
    assert val_err.details == {"field": "symbol"}

    assert normalize_error_code("  not-found  ") == "NOT_FOUND"
    assert normalize_error_code("invalid param") == "INVALID_PARAM"

    assert validate_error_catalog({"KEY": "desc"}) is True
    assert validate_error_catalog({}) is False
    assert validate_error_catalog("not_a_dict") is True

    cat = get_common_error_catalog()
    assert "VALIDATION_FAILED" in cat
    assert "CAPABILITY_UNAVAILABLE" in cat


def test_map_exception() -> None:
    """Verify map_exception converts exceptions to standardized dictionary."""
    hq_err = ValidationError("INVALID_SYMBOL", "NOT_FOUND")
    assert map_exception(hq_err) == {"code": "INVALID_SYMBOL", "detail": "NOT_FOUND"}

    val_err = ValueError("bad value")
    assert map_exception(val_err) == {
        "code": "VALIDATION_FAILED",
        "detail": "INVALID_ARGUMENT",
    }

    perm_err = PermissionError("access denied")
    assert map_exception(perm_err) == {
        "code": "SECURITY_ERROR",
        "detail": "PERMISSION_DENIED",
    }

    timeout_err = TimeoutError("timed out")
    assert map_exception(timeout_err) == {
        "code": "EXTERNAL_SERVICE_ERROR",
        "detail": "TIMEOUT",
    }

    generic_err = RuntimeError("unknown")
    assert map_exception(generic_err) == {
        "code": "INTERNAL_ERROR",
        "detail": "UNSPECIFIED",
    }
