"""Data-backed persistence evidence for FEAT-RES-16."""

from datetime import UTC, datetime
from pathlib import Path

from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    build_reasoned_stress_shock,
    build_stress_scenario_evidence,
    load_latest_stress_scenario_evidence,
    persist_stress_scenario_evidence,
)


def test_stress_evidence_round_trips_immutably(tmp_path: Path) -> None:
    """FR-RES-119: append and retrieve canonical stress evidence."""
    evidence = build_stress_scenario_evidence(
        scenario_id="scenario-demo",
        hypothesis="network interruption",
        shocks=(
            build_reasoned_stress_shock(
                shock_type="connectivity",
                magnitude=30.0,
                assumption_ref="assumption-network-1",
                rationale="Recovery objective boundary",
            ),
        ),
        generated_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )
    settings = build_data_settings(
        database_url="sqlite:///research-stress.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(tmp_path,),
    )
    with data_settings_context(settings):
        persist_stress_scenario_evidence(evidence, request_id=generate_id("req"))
        loaded = load_latest_stress_scenario_evidence(
            scenario_id="scenario-demo", request_id=generate_id("req")
        )
    assert loaded == evidence
