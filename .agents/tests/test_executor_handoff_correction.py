"""Regression tests for same-session Executor terminal-handoff correction."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

EXECUTOR_SESSION = "executor-exact"


def _prepare(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> bytes:
    state["branch"] = "main"
    state["phase"] = "executor"
    state["approved_write_paths"] = ["demo.txt"]
    state["approved_plan_hash"] = "a" * 64
    (repo / "demo.txt").write_text("implementation\n", encoding="utf-8")
    (repo / ".agents/task/planner.md").write_text(
        "approved planner evidence\n", encoding="utf-8"
    )
    (repo / ".agents/task/executor.md").write_text(
        "# Report 1\nImplementation complete; terminal handoff missing.\n",
        encoding="utf-8",
    )
    (repo / ".agents/task/next-agent.md").write_text(
        "incomplete reviewer prompt\n", encoding="utf-8"
    )
    ledger = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sessions": {
                    "PLANNER": {"session_id": "planner-exact"},
                    "EXECUTOR": {"session_id": EXECUTOR_SESSION},
                },
            }
        ),
        encoding="utf-8",
    )
    return (repo / "demo.txt").read_bytes()


def test_materializes_exact_same_session_correction_without_product_mutation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    product_before = _prepare(orc, cfg, state, repo)
    fingerprint = orc._worktree_fingerprint(repo)

    orc.materialize_executor_handoff_correction(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_executor_session_id=EXECUTOR_SESSION,
        expected_worktree_fingerprint=fingerprint,
    )

    assert state["phase"] == "executor"
    assert state["iteration"] == 1
    assert state["approved_write_paths"] == []
    assert state["executor_handoff_correction"]["approved_write_paths"] == ["demo.txt"]
    assert (
        state["executor_handoff_correction"]["executor_session_id"] == EXECUTOR_SESSION
    )
    assert (repo / "demo.txt").read_bytes() == product_before
    artifact = orc.parse_next_agent(repo / ".agents/task/next-agent.md")
    assert artifact.metadata["source_role"] == "ORCHESTRATOR"
    assert artifact.metadata["target_role"] == "EXECUTOR"
    assert artifact.metadata["handoff"] == "EXECUTOR_HANDOFF_CORRECTION"
    assert "HANDOFF-ONLY CORRECTION" in artifact.body


def test_correction_fails_closed_for_reviewer_session(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    ledger_path = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["sessions"]["REVIEWER"] = {"session_id": "unexpected"}
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(orc.OrchestratorError, match="at or beyond"):
        orc.materialize_executor_handoff_correction(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_executor_session_id=EXECUTOR_SESSION,
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )


def test_correction_fails_closed_for_unauthorized_product_path(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    (repo / "outside.txt").write_text("outside\n", encoding="utf-8")
    with pytest.raises(orc.OrchestratorError, match="outside approved scope"):
        orc.materialize_executor_handoff_correction(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_executor_session_id=EXECUTOR_SESSION,
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )


def test_correction_preserves_existing_valid_handoff_at_later_iteration(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    state["iteration"] = 2
    journal = repo / ".agents/task/executor.md"
    journal.write_text(
        journal.read_text(encoding="utf-8")
        + "\nSTOPPED : EXECUTOR\nACTIVATING : REVIEWER\n"
        "HANDOFF : READY_FOR_REVIEW\n",
        encoding="utf-8",
    )
    before = journal.read_bytes()

    orc.materialize_executor_handoff_correction(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_executor_session_id=EXECUTOR_SESSION,
        expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
    )

    assert state["iteration"] == 2
    assert journal.read_bytes() == before
    artifact = orc.parse_next_agent(repo / ".agents/task/next-agent.md")
    assert artifact.metadata["iteration"] == 2
    assert "preserve the existing valid READY_FOR_REVIEW" in artifact.body


def test_correction_preserves_prior_iteration_reviewer_session(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    state["iteration"] = 2
    ledger_path = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["sessions"]["REVIEWER"] = {
        "session_id": "reviewer-session",
        "last_iteration": 1,
    }
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    (repo / "retained.txt").write_text("reviewed earlier\n", encoding="utf-8")
    journal = repo / ".agents/task/executor.md"
    journal.write_text(
        journal.read_text(encoding="utf-8")
        + "\nSTOPPED : EXECUTOR\nACTIVATING : REVIEWER\n"
        "HANDOFF : READY_FOR_REVIEW\n",
        encoding="utf-8",
    )

    orc.materialize_executor_handoff_correction(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_executor_session_id=EXECUTOR_SESSION,
        expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
    )

    persisted = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert persisted["sessions"]["REVIEWER"]["session_id"] == "reviewer-session"


def test_correction_rejects_current_iteration_reviewer_session(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    state["iteration"] = 2
    ledger_path = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["sessions"]["REVIEWER"] = {
        "session_id": "reviewer-session",
        "last_iteration": 2,
    }
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    with pytest.raises(orc.OrchestratorError, match="at or beyond"):
        orc.materialize_executor_handoff_correction(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_executor_session_id=EXECUTOR_SESSION,
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )
