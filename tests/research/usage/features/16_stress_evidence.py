"""Standalone usage evidence for FEAT-RES-16."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context
from app.services.research import (
    build_reasoned_stress_shock,
    build_registered_stress_scenario,
    build_stress_calibration_provider,
    build_stress_scenario_evidence,
    derive_historical_stress_shock,
    get_stress_scenario_catalog,
    load_latest_stress_scenario_evidence,
    parse_stress_scenario_evidence,
    persist_stress_scenario_evidence,
    validate_shock_basis,
)


def main() -> None:
    """Exercise every stress-evidence public operation."""
    shocks = (
        derive_historical_stress_shock(
            shock_type="price",
            observations=(100.0, 85.0),
            event_ref="event-2020",
            rationale="Observed close-to-trough move",
        ),
        build_reasoned_stress_shock(
            shock_type="connectivity",
            magnitude=30.0,
            assumption_ref="assumption-network-1",
            rationale="Recovery objective boundary",
        ),
    )
    assert validate_shock_basis(shocks) == ()
    assert len(get_stress_scenario_catalog()) == 5
    registered = build_registered_stress_scenario(
        scenario_key="broad_market_dislocation",
        hypothesis="approved catalogue demonstration",
        generated_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert registered["advisory_only"] is True
    evidence = build_stress_scenario_evidence(
        scenario_id="scenario-demo",
        hypothesis="combined disruption",
        shocks=shocks,
        generated_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert parse_stress_scenario_evidence(evidence) == evidence
    assert build_stress_calibration_provider(evidence)
    with TemporaryDirectory(prefix="research-stress-") as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///research.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(root,),
        )
        with data_settings_context(settings):
            persist_stress_scenario_evidence(evidence, request_id=generate_id("req"))
            assert load_latest_stress_scenario_evidence(
                scenario_id="scenario-demo", request_id=generate_id("req")
            )
    print("SUCCESS: FEAT-RES-16 stress evidence completed")


if __name__ == "__main__":
    main()
