"""Git worktree lifecycle tests for parallel lanes."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "worktree_manager.py"
    spec = importlib.util.spec_from_file_location("hq_worktree_manager_tests", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_create_three_detached_lane_worktrees(repo: Path) -> None:
    manager = _load()
    baseline = _git(repo, "rev-parse", "HEAD")
    records = manager.create_lane_worktrees(
        repo,
        goal_run_id="goal-test",
        lanes=["codex", "gemini", "zcode"],
        baseline=baseline,
    )
    assert set(records) == {"codex", "gemini", "zcode"}
    assert all(
        record.head == baseline and record.branch is None for record in records.values()
    )


def test_fourth_or_duplicate_lane_is_rejected() -> None:
    manager = _load()
    with pytest.raises(manager.WorktreeError):
        manager.validate_lanes(["a", "b", "c", "d"])
    with pytest.raises(manager.WorktreeError):
        manager.validate_lanes(["codex", "codex"])


def test_dirty_lane_cannot_be_removed(repo: Path) -> None:
    manager = _load()
    baseline = _git(repo, "rev-parse", "HEAD")
    record = manager.create_lane_worktrees(
        repo, goal_run_id="goal-test", lanes=["codex"], baseline=baseline
    )["codex"]
    path = Path(record.path)
    (path / "dirty.txt").write_text("retain", encoding="utf-8")
    with pytest.raises(manager.WorktreeError, match="dirty"):
        manager.remove_clean_lane_worktree(repo, path, "goal-test")
