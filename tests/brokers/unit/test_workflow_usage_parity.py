"""Verify Brokers workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/brokers/usage/workflows"
README = ROOT / "app/services/brokers/README.md"
EXPECTED = {
    "WF-BRK-PRI": "wf_brk_pri_resolve_explicit_adapter.py",
    "WF-BRK-SEC": "wf_brk_sec_connect_authenticate_provider_session.py",
    "WF-BRK-003": "wf_brk_003_acquire_provider_market_data.py",
    "WF-BRK-TER": "wf_brk_ter_submit_one_broker_mutation.py",
    "WF-BRK-005": "wf_brk_005_read_account_execution_state.py",
    "WF-BRK-006": "wf_brk_006_stream_provider_connection_events.py",
    "WF-BRK-007": "wf_brk_007_correlate_ctrader_response.py",
    "WF-BRK-008": "wf_brk_008_handle_unsupported_operation.py",
    "WF-BRK-009": "wf_brk_009_inject_canonical_broker_execution.py",
    "WF-BRK-010": "wf_brk_010_discover_registered_brokers_capabilities.py",
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


def test_broker_workflow_registry_has_one_complete_program_per_workflow() -> None:
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
        assert f"`tests/brokers/usage/workflows/{filename}`" in readme

    mutation_source = (WORKFLOW_DIR / EXPECTED["WF-BRK-TER"]).read_text(
        encoding="utf-8"
    )
    assert "without provider transmission" in mutation_source
