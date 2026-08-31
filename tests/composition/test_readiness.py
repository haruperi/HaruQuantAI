"""Tests for deployment profile readiness evaluation."""

import pytest
from app.composition.readiness import (
    PROFILES,
    DeploymentProfile,
    check_profile_readiness,
)


def test_deployment_profile_model() -> None:
    """Test DeploymentProfile model attributes and registry."""
    assert "research" in PROFILES
    assert "live" in PROFILES
    assert "backtest" in PROFILES
    assert "offline" in PROFILES

    live_prof = PROFILES["live"]
    assert isinstance(live_prof, DeploymentProfile)
    assert live_prof.is_critical is True
    assert "trading.execution@1" in live_prof.required_capabilities


def test_research_profile_readiness() -> None:
    """Test research profile readiness requires data.historical-bars@1."""
    # When missing historical bars
    is_ready, missing = check_profile_readiness("research", ["system.clock@1"])
    assert not is_ready
    assert "data.historical-bars@1" in missing

    # When present
    is_ready_now, missing_now = check_profile_readiness(
        "research", ["data.historical-bars@1", "system.clock@1"]
    )
    assert is_ready_now
    assert missing_now == ()


def test_backtest_profile_readiness() -> None:
    """Test backtest profile requires historical bars and system clock."""
    is_ready, missing = check_profile_readiness("backtest", ["data.historical-bars@1"])
    assert not is_ready
    assert "system.clock@1" in missing

    is_ready_now, missing_now = check_profile_readiness(
        "backtest", ["data.historical-bars@1", "system.clock@1"]
    )
    assert is_ready_now
    assert missing_now == ()


def test_offline_profile_readiness() -> None:
    """Test explicit offline profile has zero required capabilities and is considered ready."""
    is_ready, missing = check_profile_readiness("offline", [])
    assert is_ready
    assert missing == ()


def test_live_readiness_requires_all_safety_capabilities() -> None:
    """Test Live readiness fails if ANY required trading safety capability is missing."""
    all_safety_caps = [
        "system.clock@1",
        "broker.market-data@1",
        "broker.execution@1",
        "data.realtime-ticks@1",
        "portfolio.positions@1",
        "risk.approval@1",
        "trading.execution@1",
    ]

    # When all safety capabilities are present, Live is ready
    is_ready, missing = check_profile_readiness("live", all_safety_caps)
    assert is_ready
    assert missing == ()

    # Parametric check: removing any single safety capability must result in readiness failure
    for missing_cap in all_safety_caps:
        subset = [c for c in all_safety_caps if c != missing_cap]
        ready, missing_list = check_profile_readiness("live", subset)
        assert not ready, f"Live profile should not be ready when missing {missing_cap}"
        assert missing_cap in missing_list


@pytest.mark.parametrize(
    "unknown_profile", ["custom-offline", "unknown_profile", "invalid"]
)
def test_unknown_profile_fails_readiness(unknown_profile: str) -> None:
    """Test unknown profile fail-closed behavior."""
    is_ready, missing = check_profile_readiness(unknown_profile, [])
    assert not is_ready
    assert any("UNKNOWN_PROFILE" in m for m in missing)
