"""Unit evidence for FEAT-RES-14 expectancy governance."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.research import (
    build_expectancy_profile,
    evaluate_expectancy_eligibility,
    get_min_reward_risk_override,
    parse_approved_expectancy_profile,
    transition_expectancy_governance,
)


def _approved_profile() -> dict[str, object]:
    """Build a bounded approved expectancy fixture."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    profile = build_expectancy_profile(
        exact_version="1",
        hypothesis="bounded edge",
        strategy_ref="strategy-demo",
        instruments=("EURUSD",),
        regimes=("trend",),
        sessions=("london",),
        sample_from_utc=now - timedelta(days=30),
        sample_to_utc=now - timedelta(days=1),
        sample_size=100,
        out_of_sample_status="walk_forward",
        win_rate=0.6,
        avg_win_r=2.0,
        avg_loss_r=1.0,
        expected_value_r=0.8,
        max_drawdown_r=4.0,
        min_reward_risk=1.5,
        evidence_ref="artifact-demo",
    )
    profile = transition_expectancy_governance(
        profile,
        target_state="under_review",
        reviewer="reviewer",
        decision="review",
        reason="EVIDENCE_READY",
        now_utc=now,
    )
    return transition_expectancy_governance(
        profile,
        target_state="approved",
        reviewer="reviewer",
        decision="approve",
        reason="EVIDENCE_ACCEPTED",
        now_utc=now,
    )


def test_expectancy_exact_eligibility_and_decimal_override() -> None:
    """FR-RES-107/109: approved scope matches exactly and Risk gets Decimal."""
    profile = _approved_profile()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    assert parse_approved_expectancy_profile(profile) == profile
    assert (
        evaluate_expectancy_eligibility(
            profile,
            strategy_ref="strategy-demo",
            instrument="EURUSD",
            regime="trend",
            session="london",
            now_utc=now,
        )
        == "ELIGIBLE"
    )
    assert get_min_reward_risk_override(
        profile, strategy_ref="strategy-demo", now_utc=now
    ) == Decimal("1.5")
