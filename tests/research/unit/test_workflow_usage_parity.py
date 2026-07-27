"""Verify Research workflow registry and usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/research/usage/workflows"
README = ROOT / "app/services/research/README.md"
EXPECTED = {
    "WF-RES-001": "wf_res_001_prepare_research_dataset.py",
    "WF-RES-002": "wf_res_002_build_core_metric_profile.py",
    "WF-RES-003": "wf_res_003_build_leakage_safe_feature_frame_time_splits.py",
    "WF-RES-004": "wf_res_004_analyze_session_seasonality_opportunity.py",
    "WF-RES-005": "wf_res_005_run_edge_study_null_evidence.py",
    "WF-RES-006": "wf_res_006_build_market_structure_profile.py",
    "WF-RES-007": "wf_res_007_forward_validate_calibrate_market_structure.py",
    "WF-RES-008": "wf_res_008_run_unsupervised_market_structure_research.py",
    "WF-RES-009": "wf_res_009_build_research_scorecard_profile_snapshot.py",
    "WF-RES-010": "wf_res_010_render_persist_research_artifact.py",
    "WF-RES-011": "wf_res_011_run_complete_edge_lab_profile.py",
}


def _assignment(path: Path, name: str) -> Any:
    """Return one literal module assignment."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is missing from {path.name}")


def test_research_workflow_registry_has_one_complete_program_each() -> None:
    """Require exact README, runner, stage, and boundary parity."""
    readme = README.read_text(encoding="utf-8")
    assert {path.name for path in WORKFLOW_DIR.glob("wf_*.py")} == set(
        EXPECTED.values()
    )
    assert tuple(EXPECTED.values()) == _assignment(
        WORKFLOW_DIR / "run_all.py", "WORKFLOWS"
    )
    for workflow_id, filename in EXPECTED.items():
        path = WORKFLOW_DIR / filename
        source = path.read_text(encoding="utf-8")
        assert _assignment(path, "WORKFLOW_ID") == workflow_id
        assert source.count("# Stage ") == len(_assignment(path, "STAGES"))
        assert "'=' * 88" in source
        assert "INPUT BOUNDARY" in source
        assert "OUTPUT BOUNDARY" in source
        assert 'if __name__ == "__main__":' in source
        assert f"`tests/research/usage/workflows/{filename}`" in readme
