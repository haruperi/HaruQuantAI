"""Verify Analytics workflow registry and standalone usage-program parity."""

# ruff: noqa: INP001

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/analytics/usage/workflows"
README = ROOT / "app/services/analytics/README.md"
EXPECTED = {
    "WF-ANLT-001": "wf_anlt_001_build_canonical_performance_report.py",
    "WF-ANLT-002": "wf_anlt_002_calculate_grouped_analytics_evidence.py",
    "WF-ANLT-003": "wf_anlt_003_benchmark_relative_analysis.py",
    "WF-ANLT-005": "wf_anlt_005_build_dashboard_payload.py",
    "WF-ANLT-006": "wf_anlt_006_adapt_upstream_result.py",
    "WF-ANLT-007": "wf_anlt_007_run_statistical_validation.py",
    "WF-ANLT-008": "wf_anlt_008_serialize_hash_report.py",
    "WF-ANLT-009": "wf_anlt_009_build_portfolio_performance_report.py",
    "WF-ANLT-010": "wf_anlt_010_compare_performance_reports.py",
    "WF-ANLT-013": "wf_anlt_013_build_portfolio_allocation_evidence.py",
    "WF-ANLT-014": "wf_anlt_014_measure_reconciled_portfolio_rebalance.py",
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


def test_analytics_workflow_registry_has_one_complete_program_per_workflow() -> None:
    """Require exact README, runner, separator, stage, and boundary parity."""
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
        assert f"`tests/analytics/usage/workflows/{filename}`" in readme
    assert "WF-ANLT-004" not in {
        _assignment(WORKFLOW_DIR / filename, "WORKFLOW_ID")
        for filename in EXPECTED.values()
    }
