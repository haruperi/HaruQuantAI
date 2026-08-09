"""Verify Utils workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/utils/usage/workflows"
README = ROOT / "app/utils/README.md"
EXPECTED = {
    "WF-UTL-PRI": "wf_utl_pri_structured_logging_and_redaction.py",
    "WF-UTL-SEC": "wf_utl_sec_shared_settings_bootstrap.py",
    "WF-UTL-TER": "wf_utl_ter_audit_event_construction.py",
    "WF-UTL-004": "wf_utl_004_standard_operation_response_envelope.py",
    "WF-UTL-005": "wf_utl_005_error_normalization_and_routing.py",
    "WF-UTL-006": "wf_utl_006_trace_identity_and_utc_time.py",
    "WF-UTL-007": "wf_utl_007_canonical_serialization_and_digest.py",
    "WF-UTL-008": "wf_utl_008_operational_contract_envelope.py",
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


def test_utils_workflow_registry_has_one_complete_program_per_workflow() -> None:
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
        assert f"`tests/utils/usage/workflows/{filename}`" in readme
