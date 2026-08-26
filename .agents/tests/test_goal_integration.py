"""Goal-to-Task supervision integration tests with a deterministic fake Task API."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_goal_engine(orc: ModuleType) -> ModuleType:
    path = orc.AGENTS_DIR / "goal_engine.py"
    spec = importlib.util.spec_from_file_location("hq_goal_engine_integration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _mark_complete(path: Path, entry_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = rf"(####\s+{re.escape(entry_id)}\s+)\[ \]"
    text, count = re.subn(pattern, rf"\1[X]", text, count=1)
    assert count == 1
    path.write_text(text, encoding="utf-8")


def test_goal_advances_sequential_children_with_fresh_task_runs(
    orc: ModuleType, tmp_path: Path, monkeypatch: Any
) -> None:
    goal = _load_goal_engine(orc)
    (tmp_path / ".agents" / "task").mkdir(parents=True)
    for name in ("planner.md", "executor.md", "reviewer.md", "next-agent.md"):
        (tmp_path / ".agents" / "task" / name).write_bytes(b"")
    tracker = tmp_path / "tracker.md"
    tracker.write_text(
        "# Tracker\n\n"
        "#### 4.1 [ ] `FEAT-SAME` First\n1. [ ] FR-ONE-001 first\n\n"
        "#### 4.2 [ ] `FEAT-SAME` Second\n1. [ ] FR-TWO-001 second\n\n"
        "#### 4.3 [ ] `FEAT-THREE` Third\n1. [ ] FR-THREE-001 third\n",
        encoding="utf-8",
    )
    cfg = {
        "repo": tmp_path,
        "main_branch": "main",
        "journals": {
            "planner": tmp_path / ".agents" / "task" / "planner.md",
            "executor": tmp_path / ".agents" / "task" / "executor.md",
            "reviewer": tmp_path / ".agents" / "task" / "reviewer.md",
        },
        "next_agent": tmp_path / ".agents" / "task" / "next-agent.md",
    }
    spec = {
        "goal_id": "GOAL-TEST",
        "goal_slug": "test-goal",
        "goal_name": "Test Goal",
        "goal_request": "Complete three children.",
        "implementation_file": "tracker.md",
        "selection_type": "phase",
        "selection": "4",
        "execution_order": "tracker",
        "skip_completed": True,
        "stop_on_blocked": True,
    }
    prepared: list[tuple[str, str]] = []
    heads = {"value": 0}

    def fake_prepare(
        _cfg: dict[str, Any],
        task: dict[str, Any],
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        entry = str(task["implementation_entry"])
        assert run_id is not None
        prepared.append((entry, run_id))
        return {
            "run_id": run_id,
            "task": task,
            "baseline": f"base-{entry}",
            "branch": None,
            "iteration": 1,
            "phase": "task_activation",
            "status": "RUNNING",
        }

    def fake_resume(
        _cfg: dict[str, Any], child: dict[str, Any], **_kwargs: Any
    ) -> dict[str, Any]:
        entry = str(child["task"]["implementation_entry"])
        _mark_complete(tracker, entry)
        heads["value"] += 1
        child["phase"] = "done"
        child["status"] = "ACCEPTED"
        return child

    def fake_git(_repo: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("status", "--porcelain"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return f"head-{heads['value']}"
        raise AssertionError(args)

    monkeypatch.setattr(goal, "prepare_task_run", fake_prepare)
    monkeypatch.setattr(goal, "resume_task_run", fake_resume)
    monkeypatch.setattr(goal, "_git_ok", fake_git)

    state = goal.create_goal_state(cfg, spec)
    result = goal.advance_goal(cfg, state, auto_approve=True)

    assert result["status"] == "ACCEPTED"
    assert [entry for entry, _run_id in prepared] == ["4.1", "4.2", "4.3"]
    run_ids = [run_id for _entry, run_id in prepared]
    assert len(set(run_ids)) == 3
    assert "4.1-same" in run_ids[0]
    assert "4.2-same" in run_ids[1]
    assert result["completed_entries"] == ["4.1", "4.2", "4.3"]
    assert result["remaining_entries"] == []
    assert result["active_child"] is None
    assert result["child_runs"] == {
        entry: run_id for entry, run_id in prepared
    }
    assert len({child["task_run_id"] for child in result["children"]}) == 3
    serialized = goal.json.dumps(result)
    assert "session_id" not in serialized
    assert "role_sessions" not in serialized
