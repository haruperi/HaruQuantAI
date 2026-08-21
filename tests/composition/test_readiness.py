"""Tests for deployment profile readiness checking."""

import pytest

from app.composition.readiness import check_profile_readiness


def test_research_profile_readiness() -> None:
    is_ready, missing = check_profile_readiness("research", ["system.clock@1"])
    assert not is_ready
    assert "data.historical-bars@1" in missing

    is_ready_now, missing_now = check_profile_readiness(
        "research", ["data.historical-bars@1", "system.clock@1"]
    )
    assert is_ready_now
    assert missing_now == ()


def test_backtest_profile_readiness() -> None:
    is_ready, missing = check_profile_readiness("backtest", ["data.historical-bars@1"])
    assert not is_ready
    assert "system.clock@1" in missing

    is_ready_now, missing_now = check_profile_readiness(
        "backtest", ["data.historical-bars@1", "system.clock@1"]
    )
    assert is_ready_now
    assert missing_now == ()


def test_live_profile_readiness_requires_complete_safety_boundary() -> None:
    live_caps = [
        "system.clock@1",
        "broker.market-data@1",
        "broker.execution@1",
        "data.realtime-ticks@1",
        "portfolio.positions@1",
        "risk.approval@1",
        "trading.execution@1",
    ]
    is_ready, missing = check_profile_readiness("live", live_caps)
    assert is_ready
    assert missing == ()

    for required_capability in live_caps:
        incomplete = [cap for cap in live_caps if cap != required_capability]
        is_ready_incomplete, missing_incomplete = check_profile_readiness(
            "live",
            incomplete,
        )
        assert not is_ready_incomplete
        assert required_capability in missing_incomplete


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown readiness profile"):
        check_profile_readiness("custom-offline", [])
