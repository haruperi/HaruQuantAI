"""Verify Data workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/data/usage/workflows"
README = ROOT / "app/services/data/README.md"
EXPECTED = {
    "WF-DATA-PRI": "wf_data_pri_historical_bars_ticks_spreads.py",
    "WF-DATA-SEC": "wf_data_sec_internal_analytical_data_access.py",
    "WF-DATA-003": "wf_data_003_local_dataset_load_save.py",
    "WF-DATA-004": "wf_data_004_resample_align_aggregate.py",
    "WF-DATA-005": "wf_data_005_synthetic_generation.py",
    "WF-DATA-TER": "wf_data_ter_update_job_historical_backfill.py",
    "WF-DATA-008": "wf_data_008_internal_realtime_feed_status.py",
    "WF-DATA-009": "wf_data_009_symbol_discovery_metadata_availability.py",
    "WF-DATA-010": "wf_data_010_current_hours_sessions_volume.py",
    "WF-DATA-011": "wf_data_011_source_readiness_promotion.py",
    "WF-DATA-012": "wf_data_012_simulation_data_modelling_boundary.py",
    "WF-DATA-013": "wf_data_013_account_snapshot_service.py",
    "WF-DATA-014": "wf_data_014_risk_market_context_evidence.py",
    "WF-DATA-015": "wf_data_015_fx_conversion_evidence.py",
    "WF-DATA-016": "wf_data_016_tick_series_generation_real_evidence.py",
    "WF-DATA-017": "wf_data_017_external_artifact_import.py",
    "WF-DATA-018": "wf_data_018_venue_authoritative_market_hours.py",
    "WF-DATA-019": "wf_data_019_analytical_named_session_classification.py",
    "WF-DATA-022": "wf_data_022_data_audit_trail.py",
    "WF-DATA-023": "wf_data_023_versioned_cache_lifecycle.py",
    "WF-DATA-024": "wf_data_024_quality_inspection_remediation.py",
}


def _assignment(path: Path, name: str) -> Any:
    """Return one literal module assignment."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is missing from {path.name}")


def test_data_workflow_registry_has_one_complete_program_per_active_workflow() -> None:
    """Require exact README, runner, stage, and boundary parity."""
    readme = README.read_text(encoding="utf-8")
    actual = {path.name for path in WORKFLOW_DIR.glob("wf_*.py")}
    assert actual == set(EXPECTED.values())
    assert tuple(EXPECTED.values()) == _assignment(
        WORKFLOW_DIR / "run_all.py", "WORKFLOWS"
    )

    for workflow_id, filename in EXPECTED.items():
        path = WORKFLOW_DIR / filename
        source = path.read_text(encoding="utf-8")
        stages = _assignment(path, "STAGES")
        assert _assignment(path, "WORKFLOW_ID") == workflow_id
        assert source.count("# Stage ") == len(stages)
        assert "'=' * 88" in source
        assert "INPUT BOUNDARY" in source
        assert "OUTPUT BOUNDARY" in source
        assert "def main() -> None:" in source
        assert 'if __name__ == "__main__":' in source
        assert f"`{workflow_id}`" in readme
        assert f"`tests/data/usage/workflows/{filename}`" in readme

    assert "WF-DATA-006" not in {
        _assignment(WORKFLOW_DIR / filename, "WORKFLOW_ID")
        for filename in EXPECTED.values()
    }
