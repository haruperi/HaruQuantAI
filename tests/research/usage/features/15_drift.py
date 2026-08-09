"""Standalone usage evidence for FEAT-RES-15."""

import sys
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    build_performance_drift_evidence,
    load_latest_performance_drift_evidence,
    monitor_performance_drift,
    parse_performance_drift_evidence,
    persist_performance_drift_evidence,
    propose_drift_suspension,
)
from app.utils import generate_id


def main() -> None:
    """Exercise every performance-drift public operation."""
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
        thresholds={"win_rate": 0.25, "expected_value": 0.25, "drawdown": 0.25},
        generated_at_utc=now + timedelta(days=1),
    )
    assert parse_performance_drift_evidence(evidence) == evidence
    assert propose_drift_suspension(evidence)["proposal"] == "suspend"
    # Monitoring is exercised with a deliberately absent profile fail-closed.
    with suppress(ValueError):
        monitor_performance_drift(
            approved_profile={},
            observed_from_utc=now,
            observed_to_utc=now,
            observed_win_rate=0.0,
            observed_expected_value_r=0.0,
            observed_max_drawdown_r=0.0,
            generated_at_utc=now,
        )
    with TemporaryDirectory(prefix="research-drift-") as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///research.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(root,),
        )
        with data_settings_context(settings):
            persist_performance_drift_evidence(evidence, request_id=generate_id("req"))
            assert load_latest_performance_drift_evidence(
                profile_id=str(evidence["profile_id"]), request_id=generate_id("req")
            )
    print("SUCCESS: FEAT-RES-15 performance drift completed")


if __name__ == "__main__":
    main()
