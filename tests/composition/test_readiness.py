"""Tests for profile readiness checking."""

from app.composition.readiness import check_profile_readiness


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


def test_live_profile_readiness() -> None:
    """Test live profile requires broker execution, market data, risk, and clock."""
    live_caps = [
        "broker.market-data@1",
        "broker.execution@1",
        "risk.approval@1",
        "data.historical-bars@1",
        "system.clock@1",
    ]
    is_ready, missing = check_profile_readiness("live", live_caps)
    assert is_ready
    assert missing == ()

    # If missing risk approval
    incomplete_caps = [c for c in live_caps if c != "risk.approval@1"]
    is_ready_incomplete, missing_incomplete = check_profile_readiness(
        "live", incomplete_caps
    )
    assert not is_ready_incomplete
    assert "risk.approval@1" in missing_incomplete


def test_unknown_profile_defaults_ready() -> None:
    """Test unknown profile has no required capabilities and is considered ready."""
    is_ready, missing = check_profile_readiness("custom-offline", [])
    assert is_ready
    assert missing == ()
