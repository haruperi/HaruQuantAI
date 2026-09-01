"""Data-backed persistence evidence for FEAT-RES-14."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    apply_expectancy_transition,
    build_expectancy_profile,
    load_expectancy_profile,
    persist_expectancy_profile,
)


def test_expectancy_projection_and_transition_history_are_atomic(
    tmp_path: Path,
) -> None:
    """FR-RES-110: persist a profile and guarded lifecycle transitions."""
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
    settings = build_data_settings(
        database_url="sqlite:///research-expectancy.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(tmp_path,),
    )
    request_id = generate_id("req")
    with data_settings_context(settings):
        persist_expectancy_profile(
            profile,
            reviewer="reviewer",
            decision="draft",
            reason="EVIDENCE_RECORDED",
            request_id=request_id,
        )
        applied = apply_expectancy_transition(
            profile_id=str(profile["profile_id"]),
            source_state="draft",
            governance_state="under_review",
            reviewer="reviewer",
            decision="review",
            reason="EVIDENCE_READY",
            superseded_by="",
            request_id=generate_id("req"),
        )
        loaded = load_expectancy_profile(
            profile_id=str(profile["profile_id"]), request_id=generate_id("req")
        )
    assert applied["governance_state"] == "under_review"
    assert loaded is not None
    assert loaded["governance_state"] == "under_review"
