"""End-to-end archive and refresh evidence for one parallel lane."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _load(name: str) -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    path = root / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"hq_{name}_integration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def test_reviewed_draft_replays_above_latest_main(repo: Path) -> None:
    manager = _load("worktree_manager")
    integration = _load("integration_queue")
    baseline = _git(repo, "rev-parse", "HEAD")
    record = manager.create_lane_worktrees(
        repo, goal_run_id="goal", lanes=["codex"], baseline=baseline
    )["codex"]
    lane = Path(record.path)
    manager.prepare_task_branch(
        lane, branch="feature/feat-demo-demo", baseline=baseline
    )
    (lane / "demo.txt").write_text("draft\n", encoding="utf-8")
    planner = lane / ".agents/task/planner.md"
    planner.write_text("reviewed plan\n", encoding="utf-8")
    evidence = integration.archive_draft(
        repo,
        lane,
        goal_run_id="goal",
        task_run_id="task-demo",
        approved_paths=["demo.txt"],
        coordination_paths=[".agents/task/planner.md"],
    )
    refreshed = integration.refresh_archived_draft(
        lane,
        archive_path=repo / evidence["archive"],
        archive_sha256=evidence["archive_sha256"],
        integration_baseline=baseline,
        refreshed_branch="feature/feat-demo-demo-r1",
    )
    assert refreshed["worktree_head"] == baseline
    assert (lane / "demo.txt").read_text(encoding="utf-8") == "draft\n"
    assert planner.read_text(encoding="utf-8") == "reviewed plan\n"
    assert _git(lane, "branch", "--show-current") == "feature/feat-demo-demo-r1"
