"""Run every active Data workflow example in an isolated process."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOWS = (
    "wf_data_pri_historical_bars_ticks_spreads.py",
    "wf_data_sec_internal_analytical_data_access.py",
    "wf_data_003_local_dataset_load_save.py",
    "wf_data_004_resample_align_aggregate.py",
    "wf_data_005_synthetic_generation.py",
    "wf_data_ter_update_job_historical_backfill.py",
    "wf_data_008_internal_realtime_feed_status.py",
    "wf_data_009_symbol_discovery_metadata_availability.py",
    "wf_data_010_current_hours_sessions_volume.py",
    "wf_data_011_source_readiness_promotion.py",
    "wf_data_012_simulation_data_modelling_boundary.py",
    "wf_data_013_account_snapshot_service.py",
    "wf_data_014_risk_market_context_evidence.py",
    "wf_data_015_fx_conversion_evidence.py",
    "wf_data_016_tick_series_generation_real_evidence.py",
    "wf_data_017_external_artifact_import.py",
    "wf_data_018_venue_authoritative_market_hours.py",
    "wf_data_019_analytical_named_session_classification.py",
    "wf_data_022_data_audit_trail.py",
    "wf_data_023_versioned_cache_lifecycle.py",
    "wf_data_024_quality_inspection_remediation.py",
)


def main() -> None:
    """Execute all Data workflows and report every result."""
    directory = Path(__file__).resolve().parent
    failures: list[str] = []
    for filename in WORKFLOWS:
        print(f"\nRUNNING {filename}", flush=True)
        completed = subprocess.run(  # noqa: S603 - fixed local workflow scripts.
            [sys.executable, str(directory / filename)],
            check=False,
        )
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"{status} {filename}", flush=True)
        if completed.returncode:
            failures.append(filename)
    print(
        f"\nData workflows: {len(WORKFLOWS) - len(failures)} passed, "
        f"{len(failures)} failed"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
