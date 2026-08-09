"""Unit evidence for FEAT-RES-15 performance drift."""

from datetime import UTC, datetime, timedelta

from app.services.research import (
    build_expectancy_profile,
    monitor_performance_drift,
    propose_drift_suspension,
    transition_expectancy_governance,
)


def test_threshold_breach_proposes_advisory_suspension() -> None:
    """FR-RES-112/113: material drift produces advisory suspension evidence."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    profile = build_expectancy_profile(
        exact_version="1",
        hypothesis="edge",
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
    for state in ("under_review", "approved"):
        profile = transition_expectancy_governance(
            profile,
            target_state=state,
            reviewer="reviewer",
            decision=state,
            reason="EVIDENCE_ACCEPTED",
            now_utc=now,
        )
    evidence = monitor_performance_drift(
        approved_profile=profile,
        observed_from_utc=now,
        observed_to_utc=now + timedelta(days=7),
        observed_win_rate=0.2,
        observed_expected_value_r=0.1,
        observed_max_drawdown_r=8.0,
        generated_at_utc=now + timedelta(days=7),
    )
    proposal = propose_drift_suspension(evidence)
    assert evidence["suspension_proposed"] is True
    assert proposal["proposal"] == "suspend"
    assert proposal["advisory_only"] is True
