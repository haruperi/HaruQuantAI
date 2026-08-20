"""Unit tests for component states, kernel health, and bounded diagnostics projection.

Traces to: P4-T06, Gate G4
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.kernel.diagnostics import project_diagnostics
from app.kernel.discovery import discover_manifests
from app.kernel.errors import CapabilityReasonCode, CapabilityUnavailable
from app.kernel.health import evaluate_kernel_health, evaluate_profile_readiness
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.profiles import RuntimeProfile
from app.kernel.registry import build_inventory
from app.kernel.resolver import (
    InactiveCapability,
    ResolutionReport,
    ResolvedBinding,
)
from app.kernel.states import ComponentState


def test_exact_component_states() -> None:
    """Verify all exact ComponentState values are present."""
    expected_states = {
        "DISCOVERED",
        "DISABLED",
        "RESOLVING",
        "WAITING_FOR_DEPENDENCY",
        "STARTING",
        "ACTIVE",
        "DEGRADED",
        "DRAINING",
        "STOPPING",
        "STOPPED",
        "FAILED",
        "FAILED_CLEANUP",
        "QUARANTINED",
        "VERSION_INCOMPATIBLE",
    }
    assert {s.value for s in ComponentState} == expected_states


def test_empty_kernel_health() -> None:
    """Verify empty resolution report yields live=True, ready=True, zero counts."""
    report = ResolutionReport(
        bindings=(),
        inactive=(),
        activation_order=(),
        deactivation_order=(),
    )
    health = evaluate_kernel_health(report)
    assert health.live is True
    assert health.ready is True
    assert health.active_count == 0
    assert health.inactive_count == 0


def test_project_diagnostics_structure() -> None:
    """Verify structure and JSON-readiness of projected diagnostics."""
    b = ResolvedBinding(
        capability_id=CapabilityId.parse("indicator.rsi.v1"),
        provider_id=ProviderId.parse("indicator.rsi.default"),
        provider_version=SemanticVersion.parse("1.0.0"),
    )
    i = InactiveCapability(
        capability_id=CapabilityId.parse("indicator.williams_r.v1"),
        detail=CapabilityUnavailable(
            code="CAPABILITY_UNAVAILABLE",
            reason_code=CapabilityReasonCode.DISABLED,
            capability="indicator.williams_r.v1",
            consumer=None,
            provider_id="indicator.williams_r.default",
            provider_state="DISABLED",
            profile=None,
            dependency_chain=("indicator.williams_r.v1",),
            retryable=False,
        ),
    )
    report = ResolutionReport(
        bindings=(b,),
        inactive=(i,),
        activation_order=(b.provider_id,),
        deactivation_order=(b.provider_id,),
    )

    diag = project_diagnostics(report)
    assert "kernel" in diag
    assert "bindings" in diag
    assert "inactive" in diag
    assert diag["truncated"] is False

    kernel_info = diag["kernel"]
    assert isinstance(kernel_info, dict)
    assert kernel_info["active_count"] == 1
    assert kernel_info["inactive_count"] == 1


def test_project_diagnostics_invalid_bound() -> None:
    """Verify maximum_items < 1 raises ValueError."""
    report = ResolutionReport(
        bindings=(),
        inactive=(),
        activation_order=(),
        deactivation_order=(),
    )
    with pytest.raises(ValueError, match="maximum_items must be >= 1"):
        project_diagnostics(report, maximum_items=0)


def test_project_diagnostics_truncation() -> None:
    """Verify maximum_items bound truncates payload and sets truncated=True."""
    bindings = tuple(
        ResolvedBinding(
            capability_id=CapabilityId.parse(f"indicator.rsi_{idx}.v1"),
            provider_id=ProviderId.parse(f"indicator.rsi_{idx}.default"),
            provider_version=SemanticVersion.parse("1.0.0"),
        )
        for idx in range(10)
    )
    report = ResolutionReport(
        bindings=bindings,
        inactive=(),
        activation_order=tuple(b.provider_id for b in bindings),
        deactivation_order=tuple(b.provider_id for b in reversed(bindings)),
    )

    diag = project_diagnostics(report, maximum_items=5)
    assert diag["truncated"] is True
    assert len(diag["bindings"]) == 5  # type: ignore[arg-type]


def test_profile_readiness_evaluation() -> None:
    """Verify evaluation of profile requirements against resolved report."""
    rsi_cap = CapabilityId.parse("indicator.rsi.v1")
    williams_cap = CapabilityId.parse("indicator.williams_r.v1")

    b = ResolvedBinding(
        capability_id=rsi_cap,
        provider_id=ProviderId.parse("indicator.rsi.default"),
        provider_version=SemanticVersion.parse("1.0.0"),
    )
    report = ResolutionReport(
        bindings=(b,),
        inactive=(),
        activation_order=(b.provider_id,),
        deactivation_order=(b.provider_id,),
    )

    requirements = {
        RuntimeProfile.RESEARCH: (rsi_cap,),
        RuntimeProfile.LIVE: (rsi_cap, williams_cap),
    }

    readiness = evaluate_profile_readiness(report, requirements=requirements)
    res_map = {r.profile: r for r in readiness}

    assert res_map[RuntimeProfile.RESEARCH].ready is True
    assert len(res_map[RuntimeProfile.RESEARCH].missing) == 0

    assert res_map[RuntimeProfile.LIVE].ready is False
    assert len(res_map[RuntimeProfile.LIVE].missing) == 1
    assert (
        res_map[RuntimeProfile.LIVE].missing[0].capability == "indicator.williams_r.v1"
    )


def test_gate_g4_missing_services_root_returns_empty_inventory(tmp_path: Path) -> None:
    """Gate G4 test: Discover manifests on a missing/empty services tree and build inventory."""
    missing_dir = tmp_path / "services-missing"
    discovered = discover_manifests(missing_dir)
    assert discovered == ()

    inventory = build_inventory(discovered)
    assert inventory.providers == ()
    assert len(inventory.by_provider) == 0
    assert len(inventory.by_capability) == 0

    report = ResolutionReport(
        bindings=(),
        inactive=(),
        activation_order=(),
        deactivation_order=(),
    )
    health = evaluate_kernel_health(report)
    assert health.live is True
    assert health.ready is True
    assert health.active_count == 0
