"""Unit tests for capability profile readiness runtime gate validation.

Traces to: P7-T03, Gate G7
"""

from __future__ import annotations

import pytest
from app import (
    validate_runtime_capability_readiness,
    validate_runtime_configuration,
)
from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    CapabilityUnavailableError,
)
from app.kernel.profiles import ProfileReadiness, RuntimeProfile


def test_validate_runtime_capability_readiness_matches_legacy_on_compatible_ready() -> (
    None
):
    """Verify validate_runtime_capability_readiness returns identical success response as legacy validator when ready."""
    readiness = (
        ProfileReadiness(profile=RuntimeProfile.RESEARCH, ready=True, missing=()),
        ProfileReadiness(profile=RuntimeProfile.SIMULATION, ready=True, missing=()),
        ProfileReadiness(profile=RuntimeProfile.DEMO, ready=True, missing=()),
        ProfileReadiness(profile=RuntimeProfile.LIVE, ready=True, missing=()),
    )

    legacy_resp = validate_runtime_configuration(
        runtime_profile="research", execution_route="none"
    )
    new_resp = validate_runtime_capability_readiness(
        runtime_profile="research",
        execution_route="none",
        readiness=readiness,
    )

    assert getattr(new_resp, "status", None) == getattr(legacy_resp, "status", None)
    assert getattr(new_resp, "message", None) == getattr(legacy_resp, "message", None)


def test_validate_runtime_capability_readiness_preserves_legacy_route_error() -> None:
    """Verify route/profile incompatibility check runs first and returns legacy error response before readiness check."""
    # Even with empty readiness, incompatible route returns standard error response
    resp = validate_runtime_capability_readiness(
        runtime_profile="live",
        execution_route="none",  # invalid: live requires 'live'
        readiness=(),
    )
    assert getattr(resp, "status", None) == "error"
    err = getattr(resp, "error", None)
    assert err is not None
    assert getattr(err, "code", None) == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"


def test_validate_runtime_capability_readiness_raises_value_error_on_missing_profile() -> (
    None
):
    """Verify missing runtime profile in readiness tuple raises ValueError."""
    readiness = (
        ProfileReadiness(profile=RuntimeProfile.RESEARCH, ready=True, missing=()),
    )

    with pytest.raises(
        ValueError, match=r"profile readiness missing or duplicated: live"
    ):
        validate_runtime_capability_readiness(
            runtime_profile="live",
            execution_route="live",
            readiness=readiness,
        )


def test_validate_runtime_capability_readiness_raises_value_error_on_duplicate_profile() -> (
    None
):
    """Verify duplicate runtime profile in readiness tuple raises ValueError."""
    readiness = (
        ProfileReadiness(profile=RuntimeProfile.LIVE, ready=True, missing=()),
        ProfileReadiness(profile=RuntimeProfile.LIVE, ready=True, missing=()),
    )

    with pytest.raises(
        ValueError, match=r"profile readiness missing or duplicated: live"
    ):
        validate_runtime_capability_readiness(
            runtime_profile="live",
            execution_route="live",
            readiness=readiness,
        )


def test_validate_runtime_capability_readiness_raises_capability_unavailable_on_unready_profile() -> (
    None
):
    """Verify unready profile raises CapabilityUnavailableError with the structured evidence."""
    missing_detail = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.PROFILE_REQUIREMENT_UNSATISFIED,
        capability="risk.kill_switch.v1",
        consumer="live.profile",
        provider_id=None,
        provider_state="NOT_INSTALLED",
        profile="live",
        dependency_chain=("live.profile", "risk.kill_switch.v1"),
        retryable=False,
    )

    readiness = (
        ProfileReadiness(
            profile=RuntimeProfile.LIVE,
            ready=False,
            missing=(missing_detail,),
        ),
    )

    with pytest.raises(CapabilityUnavailableError) as exc_info:
        validate_runtime_capability_readiness(
            runtime_profile="live",
            execution_route="live",
            readiness=readiness,
        )

    assert exc_info.value.detail == missing_detail
    assert (
        str(exc_info.value)
        == "capability risk.kill_switch.v1 unavailable (PROFILE_REQUIREMENT_UNSATISFIED)"
    )


def test_validate_runtime_capability_readiness_sorts_missing_capabilities_deterministically() -> (
    None
):
    """Verify when multiple capabilities are missing, the exception is raised for the first alphabetically."""
    m_z = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.NOT_INSTALLED,
        capability="z.cap.v1",
        consumer="live.profile",
        provider_id=None,
        provider_state="NOT_INSTALLED",
        profile="live",
        dependency_chain=("live.profile", "z.cap.v1"),
        retryable=False,
    )
    m_a = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.NOT_INSTALLED,
        capability="a.cap.v1",
        consumer="live.profile",
        provider_id=None,
        provider_state="NOT_INSTALLED",
        profile="live",
        dependency_chain=("live.profile", "a.cap.v1"),
        retryable=False,
    )

    readiness = (
        ProfileReadiness(
            profile=RuntimeProfile.LIVE,
            ready=False,
            missing=(m_z, m_a),
        ),
    )

    with pytest.raises(CapabilityUnavailableError) as exc_info:
        validate_runtime_capability_readiness(
            runtime_profile="live",
            execution_route="live",
            readiness=readiness,
        )

    # Must raise for 'a.cap.v1' (sorted first)
    assert exc_info.value.detail.capability == "a.cap.v1"


def test_gate_g7_normalizes_missing_capability_at_kernel_runtime_boundary() -> None:
    """Gate G7: End-to-end normalization of capability unavailability at runtime boundary."""
    missing = CapabilityUnavailable(
        code="CAPABILITY_UNAVAILABLE",
        reason_code=CapabilityReasonCode.PROFILE_REQUIREMENT_UNSATISFIED,
        capability="execution.broker.v1",
        consumer="demo.profile",
        provider_id="execution.broker.mt5",
        provider_state="DISABLED",
        profile="demo",
        dependency_chain=("demo.profile", "execution.broker.v1"),
        retryable=False,
    )
    readiness = (
        ProfileReadiness(
            profile=RuntimeProfile.DEMO,
            ready=False,
            missing=(missing,),
        ),
    )

    with pytest.raises(CapabilityUnavailableError) as exc_info:
        validate_runtime_capability_readiness(
            runtime_profile="demo",
            execution_route="demo",
            readiness=readiness,
        )

    assert exc_info.value.detail.reason_code == "PROFILE_REQUIREMENT_UNSATISFIED"
    assert exc_info.value.detail.provider_state == "DISABLED"
