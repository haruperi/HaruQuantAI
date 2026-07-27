"""Verify Simulator workflow registry and usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/simulator/usage/workflows"
README = ROOT / "app/services/simulator/README.md"
EXPECTED = {
    "WF-SIM-001": "wf_sim_001_official_fx_backtest.py",
    "WF-SIM-002": "wf_sim_002_simulation_trader_operations.py",
    "WF-SIM-003": "wf_sim_003_optimization_candidate_execution.py",
    "WF-SIM-004": "wf_sim_004_severe_data_quality_blocked_run.py",
    "WF-SIM-005": "wf_sim_005_deterministic_replay.py",
    "WF-SIM-006": "wf_sim_006_registered_strategy_security_rejection.py",
    "WF-SIM-007": "wf_sim_007_non_canonical_fast_research.py",
    "WF-SIM-009": "wf_sim_009_portfolio_backtest.py",
    "WF-SIM-010": "wf_sim_010_tick_series_acquisition.py",
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


def test_simulator_workflow_registry_has_one_complete_program_each() -> None:
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
        assert f"`tests/simulator/usage/workflows/{filename}`" in readme
    assert "WF-SIM-008" not in EXPECTED
