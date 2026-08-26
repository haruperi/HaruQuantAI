"""Recovery, locking, and cancellation regression tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

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
