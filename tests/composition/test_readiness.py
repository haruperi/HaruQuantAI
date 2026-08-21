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


def test_live_readiness_requires_all_safety_capabilities() -> None:
    """Characterization test: Live readiness must fail if ANY required trading safety capability is missing."""
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


def test_unknown_profile_fails_or_raises() -> None:
    """Characterization test: unknown profile should not silently report ready."""
    # Under fail-closed design, an unrecognized profile must not be marked ready with 0 requirements
    is_ready, _ = check_profile_readiness("non_existent_profile", [])
    assert not is_ready, "Unknown profile should not report ready by default"
