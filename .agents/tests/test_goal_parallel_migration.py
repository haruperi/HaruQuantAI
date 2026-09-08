"""Parallel Goal specification and migration precondition tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def test_parallel_goal_spec_is_explicit(orc: ModuleType, tmp_path: Path) -> None:
    goal_file = tmp_path / "goal.toml"
    goal_file.write_text(
        """goal_id = "G"
goal_slug = "g"
goal_name = "G"
goal_request = "G"
implementation_file = "tracker.md"
selection_type = "entries"
entries = ["1.08"]
parallelism = 3
lane_names = ["codex", "gemini", "zcode"]
dependency_schedule = "docs/dev/evidence/dependency-schedule.json"
""",
        encoding="utf-8",
    )
    goal = __import__("goal_engine")
    spec = goal.load_goal_spec(goal_file)
    assert spec["parallelism"] == 3
    assert spec["lane_names"] == ["codex", "gemini", "zcode"]


def test_migration_rejects_active_child(orc: ModuleType, cfg: dict[str, Any]) -> None:
    del orc
    goal = __import__("goal_engine")
    state = {
        "status": "RUNNING",
        "active_child": {"entry": "1.08"},
    }
    with pytest.raises(goal.OrchestratorError, match="no active child"):
        goal.migrate_goal_to_parallel(cfg, state)


def test_parallel_finalization_cleans_lanes_after_full_reconciliation(
    orc: ModuleType,
    cfg: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del orc
    goal = __import__("goal_engine")
    removed: list[Path] = []
    state = {
        "goal_run_id": "goal-run",
        "resolved_entries": ["1.08"],
        "remaining_entries": [],
        "completed_entries": ["1.08"],
        "active_children": {},
        "integration_queue": [],
        "integration_owner": None,
        "path_leases": {},
        "worktrees": {
            lane: {"path": str(cfg["repo"] / ".agents/worktrees/goal-run" / lane)}
            for lane in ("codex", "gemini", "zcode")
        },
        "history": [],
        "status": "RUNNING",
    }
    monkeypatch.setattr(
        goal,
        "_current_tracker_entries",
        lambda _cfg, _state: {"1.08": {"done": True}},
    )
    monkeypatch.setattr(
        goal,
        "_git_ok",
        lambda _repo, *args: "main" if args == ("branch", "--show-current") else "",
    )
    monkeypatch.setattr(
        goal,
        "remove_clean_lane_worktree",
        lambda _repo, path, _run_id: removed.append(path),
    )
    monkeypatch.setattr(goal, "save_goal_state", lambda _cfg, _state: Path("state"))

    result = goal._finalize_parallel_goal(cfg, state)

    assert result["status"] == "ACCEPTED"
    assert result["worktrees"] == {}
    assert [path.name for path in removed] == ["codex", "gemini", "zcode"]
