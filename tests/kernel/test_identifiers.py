"""Unit tests for microkernel identifiers, semantic versions, and runtime profiles.

Traces to: P4-T01, Gate G4
"""

from __future__ import annotations

import sys

import pytest
from app import kernel
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.profiles import RuntimeProfile


def test_valid_identifiers_round_trip() -> None:
    """Verify parsing and stringification round-trips for valid identifiers."""
    cap = CapabilityId.parse("indicator.rsi.v1")
    assert cap.domain == "indicator"
    assert cap.capability == "rsi"
    assert cap.major == 1
    assert str(cap) == "indicator.rsi.v1"

    prov = ProviderId.parse("indicator.rsi.default")
    assert prov.domain == "indicator"
    assert prov.capability == "rsi"
    assert prov.implementation == "default"
    assert str(prov) == "indicator.rsi.default"

    ver = SemanticVersion.parse("1.2.3")
    assert ver.major == 1
    assert ver.minor == 2
    assert ver.patch == 3
    assert str(ver) == "1.2.3"


def test_invalid_capability_ids() -> None:
    """Verify invalid capability identifiers fail closed with exact error message."""
    invalid_cases = [
        "Indicator.rsi.v1",
        "indicator-rsi.v1",
        "indicator.rsi.v0",
        "indicator.rsi.1",
        "indicator.rsi.v-1",
        "indicator.rsi",
        "indicator.rsi.v1.extra",
        "",
        123,  # type: ignore[arg-type]
    ]
    for case in invalid_cases:
        with pytest.raises(ValueError, match=f"invalid capability id: {case!r}"):
            CapabilityId.parse(case)  # type: ignore[arg-type]


def test_invalid_provider_ids() -> None:
    """Verify invalid provider identifiers fail closed with exact error message."""
    invalid_cases = [
        "Indicator.rsi.default",
        "indicator-rsi.default",
        "indicator.rsi.default-variant",
        "indicator.rsi",
        "indicator.rsi.default.extra",
        "",
        456,  # type: ignore[arg-type]
    ]
    for case in invalid_cases:
        with pytest.raises(ValueError, match=f"invalid provider id: {case!r}"):
            ProviderId.parse(case)  # type: ignore[arg-type]


def test_invalid_semantic_versions() -> None:
    """Verify invalid semantic versions fail closed with exact error message."""
    invalid_cases = [
        "v1.0.0",
        "1.0",
        "1.0.0.0",
        "1.0.0-beta",
        "-1.0.0",
        "1.a.0",
        "",
        789,  # type: ignore[arg-type]
    ]
    for case in invalid_cases:
        with pytest.raises(ValueError, match=f"invalid semantic version: {case!r}"):
            SemanticVersion.parse(case)  # type: ignore[arg-type]


def test_identifiers_are_orderable() -> None:
    """Verify CapabilityId, ProviderId, and SemanticVersion are properly orderable."""
    c1 = CapabilityId.parse("analytics.metrics.v1")
    c2 = CapabilityId.parse("indicator.rsi.v1")
    c3 = CapabilityId.parse("indicator.rsi.v2")
    assert sorted([c3, c1, c2]) == [c1, c2, c3]

    p1 = ProviderId.parse("analytics.metrics.custom")
    p2 = ProviderId.parse("analytics.metrics.default")
    p3 = ProviderId.parse("indicator.rsi.default")
    assert sorted([p3, p2, p1]) == [p1, p2, p3]

    v1 = SemanticVersion.parse("0.9.9")
    v2 = SemanticVersion.parse("1.0.0")
    v3 = SemanticVersion.parse("1.2.0")
    v4 = SemanticVersion.parse("1.2.1")
    assert sorted([v4, v2, v1, v3]) == [v1, v2, v3, v4]


def test_runtime_profiles_are_exact() -> None:
    """Verify exact enumeration values for RuntimeProfile."""
    assert RuntimeProfile.RESEARCH == "research"
    assert RuntimeProfile.SIMULATION == "simulation"
    assert RuntimeProfile.DEMO == "demo"
    assert RuntimeProfile.LIVE == "live"
    assert len(RuntimeProfile) == 4


def test_kernel_lazy_exports_and_imports_without_services() -> None:
    """Verify kernel exports lazy symbols and does not import business services."""
    assert "CapabilityId" in dir(kernel)
    assert kernel.CapabilityId is CapabilityId
    assert kernel.RuntimeProfile is RuntimeProfile

    for mod_name in sys.modules:
        assert not mod_name.startswith("app.services"), (
            f"Forbidden business domain imported: {mod_name}"
        )
        assert not mod_name.startswith("app.agentic"), (
            f"Forbidden agentic domain imported: {mod_name}"
        )
