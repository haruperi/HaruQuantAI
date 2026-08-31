"""Regression tests for same-session Reviewer handoff correction."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REVIEWER_SESSION = "reviewer-exact"


def _prepare(
    cfg: dict[str, Any], state: dict[str, Any], repo: Path
) -> tuple[bytes, str]:
    state["branch"] = "main"
    state["phase"] = "reviewer"
    state["iteration"] = 3
    (repo / "demo.txt").write_text("implementation\n", encoding="utf-8")
    journal = repo / ".agents/task/reviewer.md"
    journal.write_text(
        "# Review 3\n\nSTOPPED : REVIEWER\nACTIVATING : PLANNER\n"
        "HANDOFF : CHANGES_REQUESTED\n",
        encoding="utf-8",
    )
    prompt = repo / ".agents/task/next-agent.md"
    prompt.write_text("invalid planner prompt\n", encoding="utf-8")
    ledger = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sessions": {
                    "PLANNER": {"session_id": "planner", "last_iteration": 3},
                    "EXECUTOR": {"session_id": "executor", "last_iteration": 3},
                    "REVIEWER": {
                        "session_id": REVIEWER_SESSION,
                        "last_iteration": 3,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return (repo / "demo.txt").read_bytes(), journal.read_text(encoding="utf-8")


def test_materializes_reviewer_correction_without_product_or_journal_mutation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    product_before, journal_before = _prepare(cfg, state, repo)

    orc.materialize_reviewer_handoff_correction(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_reviewer_session_id=REVIEWER_SESSION,
        expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
    )

    assert (repo / "demo.txt").read_bytes() == product_before
    assert (repo / ".agents/task/reviewer.md").read_text() == journal_before
    artifact = orc.parse_next_agent(repo / ".agents/task/next-agent.md")
    assert artifact.metadata["source_role"] == "ORCHESTRATOR"
    assert artifact.metadata["target_role"] == "REVIEWER"
    assert artifact.metadata["handoff"] == "REVIEWER_HANDOFF_CORRECTION"
    assert "complete canonical PLANNER prompt for iteration 4" in artifact.body


def test_reviewer_correction_rejects_wrong_session(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(cfg, state, repo)
    with pytest.raises(orc.OrchestratorError, match="identity"):
        orc.materialize_reviewer_handoff_correction(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_reviewer_session_id="wrong",
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )
