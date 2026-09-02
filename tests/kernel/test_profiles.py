"""Unit tests for kernel profiles and profile readiness evaluation."""

from __future__ import annotations

from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.profiles import (
    RuntimeProfile,
    evaluate_profile_readiness,
)
from app.kernel.resolver import ResolutionReport, ResolvedBinding


def test_runtime_profile_members() -> None:
    """Verify standard runtime profiles exist."""
    assert RuntimeProfile.OFFLINE == "offline"
    assert RuntimeProfile.RESEARCH == "research"
    assert RuntimeProfile.SIMULATION == "simulation"
    assert RuntimeProfile.BACKTEST == "backtest"
    assert RuntimeProfile.DEMO == "demo"
    assert RuntimeProfile.LIVE == "live"


def test_evaluate_profile_readiness_all_satisfied() -> None:
    """Verify readiness returns ready=True when all requirements are bound."""
    cap1 = CapabilityId.parse("data.market.v1")
    cap2 = CapabilityId.parse("indicator.rsi.v1")

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=cap1,
                provider_id=ProviderId.parse("data.market.default"),
                provider_version=SemanticVersion(1, 0, 0),
            ),
            ResolvedBinding(
                capability_id=cap2,
                provider_id=ProviderId.parse("indicator.rsi.default"),
                provider_version=SemanticVersion(1, 0, 0),
            ),
        ),
        inactive=(),
        activation_order=(),
        deactivation_order=(),
    )

    reqs = {
        RuntimeProfile.RESEARCH: (cap1, cap2),
    }

    readiness = evaluate_profile_readiness(report, requirements=reqs)
    assert len(readiness) == 1
    assert readiness[0].profile == RuntimeProfile.RESEARCH
    assert readiness[0].ready is True
    assert len(readiness[0].missing) == 0


def test_evaluate_profile_readiness_missing_capabilities() -> None:
    """Verify readiness returns ready=False with structured missing records."""
    cap1 = CapabilityId.parse("data.market.v1")
    cap2 = CapabilityId.parse("execution.order.v1")

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=cap1,
                provider_id=ProviderId.parse("data.market.default"),
                provider_version=SemanticVersion(1, 0, 0),
            ),
        ),
        inactive=(),
        activation_order=(),
        deactivation_order=(),
    )

    reqs = {
        RuntimeProfile.LIVE: (cap1, cap2),
    }

    readiness = evaluate_profile_readiness(report, requirements=reqs)
    assert len(readiness) == 1
    assert readiness[0].profile == RuntimeProfile.LIVE
    assert readiness[0].ready is False
    assert len(readiness[0].missing) == 1
    missing_item = readiness[0].missing[0]
    assert missing_item.capability == "execution.order.v1"
    assert missing_item.code == "CAPABILITY_UNAVAILABLE"
    assert missing_item.profile == "live"
