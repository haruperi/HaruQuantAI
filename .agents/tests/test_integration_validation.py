"""Local integration-candidate gate regression tests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _workflow() -> ModuleType:
    """Return the workflow engine loaded by the orchestrator fixture."""
    return sys.modules["workflow_engine"]


def _prepare_reviewed_state(
    workflow: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Populate the exact reviewed candidate identity expected by the gate."""
    state["reviewed_head"] = state["baseline"]
    state["reviewed_worktree_hash"] = workflow._worktree_fingerprint(cfg["repo"])


def _write_report(
    command: list[str],
    *,
    base: str,
    head: str,
    complete: bool = True,
) -> None:
    """Write a synthetic diagnostic report at the controller-selected path."""
    report = Path(command[command.index("--report") + 1])
    log_dir = Path(command[command.index("--log-dir") + 1])
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "python-coverage.log"
    log.write_text("passed\n", encoding="utf-8")
    report.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_kind": "diagnostic-not-reusable-validation-receipt",
                "explain_only": False,
                "decision": {
                    "requested_profile": "integration",
                    "selected_families": ["python"],
                    "candidate": {
                        "base_commit": base,
                        "head_commit": head,
                    },
                },
                "steps": [
                    {
                        "step_id": "python-coverage",
                        "name": "coverage",
                        "command": ["pytest"],
                        "working_directory": ".",
                    }
                ],
                "results": (
                    [
                        {
                            "step_id": "python-coverage",
                            "name": "coverage",
                            "command": ["pytest"],
                            "working_directory": ".",
                            "duration_seconds": 1.0,
                            "exit_code": 0,
                            "log_path": str(log),
                            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                        }
                    ]
                    if complete
                    else []
                ),
            }
        ),
        encoding="utf-8",
    )


def test_local_gate_records_exact_successful_candidate(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful evidence binds the baseline, HEAD, worktree and report."""
    workflow = _workflow()
    _prepare_reviewed_state(workflow, cfg, state)

    def execute(command: list[str], _repo: Path) -> int:
        _write_report(command, base=state["baseline"], head=state["reviewed_head"])
        return 0

    monkeypatch.setattr(workflow, "_execute_integration_command", execute)

    evidence = workflow._run_local_integration_gate(cfg, state)

    assert evidence["status"] == "PASSED"
    assert evidence["base_commit"] == state["baseline"]
    assert evidence["reviewed_head"] == state["reviewed_head"]
    assert evidence["reviewed_worktree_sha256"] == state["reviewed_worktree_hash"]
    assert evidence["selected_families"] == ["python"]
    assert len(evidence["report_sha256"]) == 64
    assert len(evidence["receipt_sha256"]) == 64


def test_receipt_survives_reasoning_handoff_without_command_rerun(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer journal bytes do not invalidate unchanged product evidence."""
    workflow = _workflow()
    state["reviewed_head"] = state["baseline"]
    state["reviewed_candidate_hash"] = workflow.candidate_fingerprint(cfg["repo"])
    calls = 0

    def execute(command: list[str], _repo: Path) -> int:
        nonlocal calls
        calls += 1
        _write_report(command, base=state["baseline"], head=state["reviewed_head"])
        return 0

    monkeypatch.setattr(workflow, "_execute_integration_command", execute)
    state["integration_validation"] = workflow._run_local_integration_gate(cfg, state)
    cfg["journals"]["reviewer"].write_text("reviewed\n", encoding="utf-8")

    workflow._ensure_local_integration_gate_unchanged(state, cfg["repo"])

    assert calls == 1


def test_failed_command_cannot_satisfy_local_gate(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed prerequisite prevents commit authorization evidence."""
    workflow = _workflow()
    _prepare_reviewed_state(workflow, cfg, state)
    monkeypatch.setattr(workflow, "_execute_integration_command", lambda *_args: 9)

    with pytest.raises(orc.OrchestratorError, match="exit code 9"):
        workflow._run_local_integration_gate(cfg, state)


def test_missing_result_cannot_be_reported_as_success(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A skipped planned check invalidates an otherwise zero exit status."""
    workflow = _workflow()
    _prepare_reviewed_state(workflow, cfg, state)

    def execute(command: list[str], _repo: Path) -> int:
        _write_report(
            command,
            base=state["baseline"],
            head=state["reviewed_head"],
            complete=False,
        )
        return 0

    monkeypatch.setattr(workflow, "_execute_integration_command", execute)

    with pytest.raises(orc.OrchestratorError, match="missing or skipped"):
        workflow._run_local_integration_gate(cfg, state)


def test_stale_report_identity_is_rejected(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Success for another base cannot approve the current candidate."""
    workflow = _workflow()
    _prepare_reviewed_state(workflow, cfg, state)

    def execute(command: list[str], _repo: Path) -> int:
        _write_report(command, base="0" * 40, head=state["reviewed_head"])
        return 0

    monkeypatch.setattr(workflow, "_execute_integration_command", execute)

    with pytest.raises(orc.OrchestratorError, match="stale base"):
        workflow._run_local_integration_gate(cfg, state)


def test_gate_rejects_validation_that_mutates_reviewed_worktree(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check execution cannot silently change the reviewed candidate."""
    workflow = _workflow()
    _prepare_reviewed_state(workflow, cfg, state)

    def execute(command: list[str], repo: Path) -> int:
        _write_report(command, base=state["baseline"], head=state["reviewed_head"])
        (repo / "mutated.txt").write_text("changed\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(workflow, "_execute_integration_command", execute)

    with pytest.raises(orc.OrchestratorError, match="changed reviewed candidate"):
        workflow._run_local_integration_gate(cfg, state)


def test_closeout_cannot_start_without_passed_local_gate(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """No direct close-out path can bypass integration qualification."""
    workflow = _workflow()

    with pytest.raises(orc.OrchestratorError, match="no passed local integration"):
        workflow._handle_closeout(cfg, state)
