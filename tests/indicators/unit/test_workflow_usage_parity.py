"""Verify Indicators workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/indicators/usage/workflows"
README = ROOT / "app/services/indicators/README.md"
EXPECTED = {
    "WF-INDI-001": "wf_indi_001_core_batch_indicator_calculation.py",
    "WF-INDI-002": "wf_indi_002_decision_time_consumption.py",
    "WF-INDI-003": "wf_indi_003_warmup_coordination.py",
    "WF-INDI-004": "wf_indi_004_availability_aware_multi_timeframe_calculation.py",
    "WF-INDI-005": "wf_indi_005_static_registry_discovery_validation.py",
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


def test_indicator_workflow_registry_has_one_complete_program_per_workflow() -> None:
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
        assert f"`tests/indicators/usage/workflows/{filename}`" in readme
