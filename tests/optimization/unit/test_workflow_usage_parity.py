"""Verify Optimization workflow registry and usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/optimization/usage/workflows"
README = ROOT / "app/services/optimization/README.md"
EXPECTED = {
    "WF-OPT-001": "wf_opt_001_package_optimization_robustness_request.py",
    "WF-OPT-002": "wf_opt_002_execute_bounded_parameter_sweep.py",
    "WF-OPT-003": "wf_opt_003_score_rank_assess_overfit_evidence.py",
    "WF-OPT-004": "wf_opt_004_run_walk_forward_validation.py",
    "WF-OPT-005": "wf_opt_005_run_monte_carlo_robustness_analysis.py",
    "WF-OPT-006": "wf_opt_006_build_persist_versioned_evidence_handoffs.py",
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


def test_optimization_workflow_registry_has_one_complete_program_each() -> None:
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
        assert f"`tests/optimization/usage/workflows/{filename}`" in readme
