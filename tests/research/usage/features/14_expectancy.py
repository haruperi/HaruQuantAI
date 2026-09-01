"""Standalone usage evidence for FEAT-RES-14."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    apply_expectancy_transition,
    build_approved_expectancy_profile,
    build_expectancy_profile,
    build_risk_expectancy_provider,
    build_strategy_expectancy_provider,
    evaluate_expectancy_eligibility,
    get_min_reward_risk_override,
    is_governance_transition_permitted,
    load_eligible_expectancy_profile,
    load_expectancy_profile,
    parse_approved_expectancy_profile,
    persist_expectancy_profile,
    transition_expectancy_governance,
)


def main() -> None:
    """Exercise every approved expectancy public operation."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    draft = build_expectancy_profile(
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
    assert is_governance_transition_permitted("draft", "under_review")
    reviewed = transition_expectancy_governance(
        draft,
        target_state="under_review",
        reviewer="reviewer",
        decision="review",
        reason="EVIDENCE_READY",
        now_utc=now,
    )
    approved = transition_expectancy_governance(
        reviewed,
        target_state="approved",
        reviewer="reviewer",
        decision="approve",
        reason="EVIDENCE_ACCEPTED",
        now_utc=now,
    )
    parsed = parse_approved_expectancy_profile(approved)
    rebuild_values = {
        key: parsed[key]
        for key in (
            "profile_id",
            "exact_version",
            "hypothesis",
            "strategy_ref",
            "instruments",
            "regimes",
            "sessions",
            "sample_from_utc",
            "sample_to_utc",
            "sample_size",
            "out_of_sample_status",
            "win_rate",
            "avg_win_r",
            "avg_loss_r",
            "expected_value_r",
            "max_drawdown_r",
            "min_reward_risk",
            "governance_state",
            "approved_at_utc",
            "next_review_at_utc",
            "expires_at_utc",
            "superseded_by",
            "evidence_ref",
        )
    }
    for timestamp_key in (
        "sample_from_utc",
        "sample_to_utc",
        "approved_at_utc",
        "next_review_at_utc",
        "expires_at_utc",
    ):
        timestamp_value = rebuild_values[timestamp_key]
        if isinstance(timestamp_value, str):
            rebuild_values[timestamp_key] = datetime.fromisoformat(timestamp_value)
    rebuilt = build_approved_expectancy_profile(**rebuild_values)
    assert (
        evaluate_expectancy_eligibility(
            rebuilt,
            strategy_ref="strategy-demo",
            instrument="EURUSD",
            regime="trend",
            session="london",
            now_utc=now,
        )
        == "ELIGIBLE"
    )
    assert get_min_reward_risk_override(
        rebuilt, strategy_ref="strategy-demo", now_utc=now
    )
    build_strategy_expectancy_provider(
        profile_loader=lambda _key: rebuilt, now_provider=lambda: now
    )
    build_risk_expectancy_provider(
        profile_loader=lambda _key: rebuilt, now_provider=lambda: now
    )
    with TemporaryDirectory(prefix="research-expectancy-") as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///research.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(root,),
        )
        with data_settings_context(settings):
            persist_expectancy_profile(
                draft,
                reviewer="reviewer",
                decision="draft",
                reason="EVIDENCE_RECORDED",
                request_id=generate_id("req"),
            )
            apply_expectancy_transition(
                profile_id=str(draft["profile_id"]),
                source_state="draft",
                governance_state="under_review",
                reviewer="reviewer",
                decision="review",
                reason="EVIDENCE_READY",
                superseded_by="",
                request_id=generate_id("req"),
            )
            assert load_expectancy_profile(
                profile_id=str(draft["profile_id"]), request_id=generate_id("req")
            )
            load_eligible_expectancy_profile(
                strategy_ref="strategy-demo", request_id=generate_id("req")
            )
    print("SUCCESS: FEAT-RES-14 expectancy governance completed")


if __name__ == "__main__":
    main()
