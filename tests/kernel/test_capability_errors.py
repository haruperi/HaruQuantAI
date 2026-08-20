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
    capability_unavailable_payload,
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
    # Empty chain
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

    # Mismatched end
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
