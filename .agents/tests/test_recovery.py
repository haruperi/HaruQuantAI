"""Recovery, locking, and cancellation regression tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def test_second_workflow_lock_fails_and_release_recovers(
    orc: ModuleType, repo: Path
) -> None:
    first = orc.WorkflowLock(repo)
    second = orc.WorkflowLock(repo)
    first.acquire()
    try:
        with pytest.raises(orc.OrchestratorError):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()


def test_blocker_resolved_transition_exists(orc: ModuleType) -> None:
    cfg = orc.assemble_config(str(orc.REPO_ROOT))
    transition = orc._transition_for(
        cfg["transitions"], "ORCHESTRATOR", "BLOCKER_RESOLVED"
    )
    assert transition.target_role == "PLANNER"


def test_blocker_resolution_materializes_fresh_current_prompt(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    state["branch"] = "main"
    old_prompt = repo / ".agents/task/next-agent.md"
    old_prompt.write_text("stale prompt\n", encoding="utf-8")
    (repo / "resolved.txt").write_text("resolution evidence\n", encoding="utf-8")
    orc._write_orchestrator_planner_prompt(cfg, state, "BLOCKER_RESOLVED")
    artifact = orc.parse_next_agent(old_prompt)
    assert artifact.metadata["source_role"] == "ORCHESTRATOR"
    assert artifact.metadata["handoff"] == "BLOCKER_RESOLVED"
    assert old_prompt.read_text(encoding="utf-8") != "stale prompt\n"
    assert state["next_agent"]["worktree_sha256"] == orc._worktree_fingerprint(repo)
