"""Verify Portfolio workflow registry and usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/portfolio/usage/workflows"
README = ROOT / "app/services/portfolio/README.md"
EXPECTED = {
    "WF-PORT-001": "wf_port_001_validate_construction_evidence.py",
    "WF-PORT-PRI": "wf_port_pri_construct_allocation_candidate.py",
    "WF-PORT-003": "wf_port_003_coordinate_simulation_risk_review.py",
    "WF-PORT-SEC": "wf_port_sec_activate_allocation_version.py",
    "WF-PORT-TER": "wf_port_ter_detect_drift_plan_rebalance.py",
    "WF-PORT-006": "wf_port_006_submit_measure_rebalance.py",
    "WF-PORT-007": "wf_port_007_rollback_allocation.py",
    "WF-PORT-008": "wf_port_008_assess_common_mode_exposure.py",
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


def test_portfolio_workflow_registry_has_one_complete_program_each() -> None:
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
        assert f"`tests/portfolio/usage/workflows/{filename}`" in readme
