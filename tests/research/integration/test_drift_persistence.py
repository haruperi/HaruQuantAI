"""Data-backed persistence evidence for FEAT-RES-15."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    build_performance_drift_evidence,
    load_latest_performance_drift_evidence,
    persist_performance_drift_evidence,
)


def test_drift_evidence_round_trips_immutably(tmp_path: Path) -> None:
    """FR-RES-114: append and retrieve canonical drift evidence."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    evidence = build_performance_drift_evidence(
        profile_id="id-" + "a" * 64,
        observed_from_utc=now,
        observed_to_utc=now + timedelta(days=1),
        observed_win_rate=0.4,
        observed_expected_value_r=0.2,
        observed_max_drawdown_r=6.0,
        envelope_win_rate=0.6,
        envelope_expected_value_r=0.8,
        envelope_max_drawdown_r=4.0,
        thresholds={
            "win_rate": 0.25,
            "expected_value": 0.25,
            "drawdown": 0.25,
        },
        generated_at_utc=now + timedelta(days=1),
    )
    settings = build_data_settings(
        database_url="sqlite:///research-drift.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(tmp_path,),
    )
    with data_settings_context(settings):
        persist_performance_drift_evidence(evidence, request_id=generate_id("req"))
        loaded = load_latest_performance_drift_evidence(
            profile_id=str(evidence["profile_id"]), request_id=generate_id("req")
        )
    assert loaded == evidence
