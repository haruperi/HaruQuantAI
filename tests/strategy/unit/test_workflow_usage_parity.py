"""Verify Strategy workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/strategy/usage/workflows"
README = ROOT / "app/services/strategy/README.md"
EXPECTED = {
    "WF-STR-001": "wf_str_001_validate_reference_configuration.py",
    "WF-STR-PRI": "wf_str_pri_generate_vectorized_decisions.py",
    "WF-STR-003": "wf_str_003_run_stateful_event_hook.py",
    "WF-STR-SEC": "wf_str_sec_build_hand_off_trade_intent.py",
    "WF-STR-005": "wf_str_005_create_replay_manifest_checkpoint.py",
    "WF-STR-006": "wf_str_006_export_structured_diagnostics.py",
    "WF-STR-007": "wf_str_007_supply_demo_live_decisions.py",
    "WF-STR-TER": "wf_str_ter_register_immutable_strategy_version.py",
    "WF-STR-009": "wf_str_009_reject_arbitrary_strategy_code.py",
    "WF-STR-010": "wf_str_010_evaluate_recovered_concrete_signals.py",
    "WF-STR-011": "wf_str_011_adopt_approved_optimization_parameters.py",
    "WF-STR-012": "wf_str_012_evaluate_signals_for_research.py",
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


def test_strategy_workflow_registry_has_one_complete_program_per_workflow() -> None:
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
        assert f"`tests/strategy/usage/workflows/{filename}`" in readme
