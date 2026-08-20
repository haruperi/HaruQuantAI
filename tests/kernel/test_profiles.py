"""Unit tests for runtime profile readiness evaluation and fail-closed safety behaviors.

Traces to: P7-T02, Gate G7
"""

from __future__ import annotations

from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
)
from app.kernel.health import evaluate_kernel_health
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.profiles import (
    RuntimeProfile,
    evaluate_profile_readiness,
)
from app.kernel.resolver import (
    InactiveCapability,
    ResolutionReport,
    ResolvedBinding,
)


def _build_dummy_report(
    *,
    bound: tuple[str, ...] = (),
    inactive: tuple[tuple[str, str, str], ...] = (),
) -> ResolutionReport:
    """Helper to build a mock ResolutionReport."""
    bindings = tuple(
        ResolvedBinding(
            capability_id=CapabilityId.parse(c),
            provider_id=ProviderId.parse("test.provider.default"),
            provider_version=SemanticVersion.parse("1.0.0"),
        )
        for c in bound
    )
    inactives = tuple(
        InactiveCapability(
            capability_id=CapabilityId.parse(c),
            detail=CapabilityUnavailable(
                code="CAPABILITY_UNAVAILABLE",
                reason_code=CapabilityReasonCode.DISABLED,
                capability=c,
                consumer=None,
                provider_id=pid,
                provider_state=state,
                profile=None,
                dependency_chain=(c,),
                retryable=False,
            ),
        )
        for c, pid, state in inactive
    )
    return ResolutionReport(
        bindings=bindings,
        inactive=inactives,
        activation_order=(),
        deactivation_order=(),
    )


def test_evaluate_profile_readiness_all_ready() -> None:
    """Verify all declared profiles evaluate to ready when all required capabilities are bound."""
    c_feed = CapabilityId.parse("data.feed.v1")
    c_order = CapabilityId.parse("execution.order.v1")

    report = _build_dummy_report(bound=("data.feed.v1", "execution.order.v1"))
    reqs = {
        RuntimeProfile.RESEARCH: (c_feed,),
        RuntimeProfile.SIMULATION: (c_feed,),
        RuntimeProfile.DEMO: (c_feed, c_order),
        RuntimeProfile.LIVE: (c_feed, c_order),
    }

    readiness = evaluate_profile_readiness(report, requirements=reqs)
    assert len(readiness) == 4
    for r in readiness:
        assert r.ready is True
        assert r.missing == ()


def test_evaluate_profile_readiness_all_four_profiles_in_sorted_order() -> None:
    """Verify all 4 runtime profiles are returned in sorted enum order."""
    report = _build_dummy_report()
    readiness = evaluate_profile_readiness(report, requirements={})
    assert [r.profile for r in readiness] == [
        RuntimeProfile.DEMO,
        RuntimeProfile.LIVE,
        RuntimeProfile.RESEARCH,
        RuntimeProfile.SIMULATION,
    ]


def test_evaluate_profile_readiness_research_optional_loss() -> None:
    """Verify research profile is ready when its required capabilities are bound even if others are missing."""
    c_feed = CapabilityId.parse("data.feed.v1")
    c_live_exec = CapabilityId.parse("execution.live.v1")

    report = _build_dummy_report(
        bound=("data.feed.v1",),
        inactive=(("execution.live.v1", "exec.live.p1", "DISABLED"),),
    )
    reqs = {
        RuntimeProfile.RESEARCH: (c_feed,),
        RuntimeProfile.LIVE: (c_feed, c_live_exec),
    }

    readiness = evaluate_profile_readiness(report, requirements=reqs)
    r_map = {r.profile: r for r in readiness}

    assert r_map[RuntimeProfile.RESEARCH].ready is True
    assert r_map[RuntimeProfile.LIVE].ready is False
    assert len(r_map[RuntimeProfile.LIVE].missing) == 1
    assert r_map[RuntimeProfile.LIVE].missing[0].capability == "execution.live.v1"
    assert (
        r_map[RuntimeProfile.LIVE].missing[0].reason_code
        == CapabilityReasonCode.PROFILE_REQUIREMENT_UNSATISFIED
    )


def test_evaluate_profile_readiness_demo_safety_loss() -> None:
    """Verify demo profile marks ready=False when a required safety capability is missing."""
    c_safety = CapabilityId.parse("risk.kill_switch.v1")
    report = _build_dummy_report(bound=())  # kill switch not bound

    reqs = {RuntimeProfile.DEMO: (c_safety,)}
    readiness = evaluate_profile_readiness(report, requirements=reqs)
    r_map = {r.profile: r for r in readiness}

    assert r_map[RuntimeProfile.DEMO].ready is False
    assert len(r_map[RuntimeProfile.DEMO].missing) == 1
    assert r_map[RuntimeProfile.DEMO].missing[0].capability == "risk.kill_switch.v1"
    assert r_map[RuntimeProfile.DEMO].missing[0].consumer == "demo.profile"
    assert r_map[RuntimeProfile.DEMO].missing[0].dependency_chain == (
        "demo.profile",
        "risk.kill_switch.v1",
    )


def test_evaluate_profile_readiness_live_safety_loss() -> None:
    """Verify live profile fails closed when a safety capability is uninstalled."""
    c_guard = CapabilityId.parse("risk.drawdown_guard.v1")
    report = _build_dummy_report(bound=())

    reqs = {RuntimeProfile.LIVE: (c_guard,)}
    readiness = evaluate_profile_readiness(report, requirements=reqs)
    r_map = {r.profile: r for r in readiness}

    assert r_map[RuntimeProfile.LIVE].ready is False
    assert r_map[RuntimeProfile.LIVE].missing[0].provider_state == "NOT_INSTALLED"


def test_evaluate_profile_readiness_preserves_kernel_liveness() -> None:
    """Verify evaluating an unready profile does NOT modify kernel health/liveness."""
    c_missing = CapabilityId.parse("execution.broker.v1")
    report = _build_dummy_report(bound=("data.feed.v1",))

    kernel_health = evaluate_kernel_health(report)
    assert kernel_health.live is True
    assert kernel_health.ready is True

    reqs = {RuntimeProfile.LIVE: (c_missing,)}
    readiness = evaluate_profile_readiness(report, requirements=reqs)
    r_map = {r.profile: r for r in readiness}
    assert r_map[RuntimeProfile.LIVE].ready is False

    # Kernel health remains alive and ready
    assert kernel_health.live is True
    assert kernel_health.ready is True


def test_evaluate_profile_readiness_selects_no_fallback_provider() -> None:
    """Verify readiness evaluation is a pure inspection function and binds no fallback providers."""
    c_live_exec = CapabilityId.parse("execution.live.v1")
    report = _build_dummy_report(bound=())

    reqs = {RuntimeProfile.LIVE: (c_live_exec,)}
    readiness = evaluate_profile_readiness(report, requirements=reqs)
    assert len(report.bindings) == 0
    assert readiness[1].profile == RuntimeProfile.LIVE
    assert readiness[1].ready is False
