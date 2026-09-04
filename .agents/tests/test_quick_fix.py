"""Focused regression tests for the shortened Quick-Fix workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from task_api import prepare_task_run
from workflow_engine import _complete_quick_fix
from workflow_runtime import _activate_task, _gate_authorization


def _install_quick_fix_templates(cfg: dict[str, Any], repo: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    prompt_dir = repo / "docs" / "templates" / "prompt"
    for key, name in (
        ("quick_fix_planner", "quick-fix-planner.md"),
        ("quick_fix_executor", "quick-fix-executor.md"),
    ):
        target = prompt_dir / name
        target.write_text(
            (source_root / "docs" / "templates" / "prompt" / name).read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        cfg["templates"][key] = target


def test_quick_fix_activation_remains_on_main(
    orc: Any, cfg: dict[str, Any], state: dict[str, Any], repo: Path
) -> None:
    _install_quick_fix_templates(cfg, repo)
    orc._git_ok(repo, "add", ".")
    orc._git_ok(repo, "commit", "--no-verify", "-m", "templates")
    state["baseline"] = orc._git_ok(repo, "rev-parse", "HEAD")
    state["runtime_mode"] = "quick-fix"
    state["approval_policy"] = "interactive"

    _activate_task(cfg, state)

    assert orc._git_ok(repo, "branch", "--show-current") == "main"
    assert state["branch"] == "main"
    assert state["phase"] == "planner"
    artifact = orc.parse_next_agent(cfg["next_agent"])
    assert artifact.metadata["handoff"] == "QUICK_FIX_ACTIVATED"
    assert artifact.metadata["template_path"].endswith("quick-fix-planner.md")


def test_quick_fix_gate_rejects_preauthorization(
    orc: Any, cfg: dict[str, Any], state: dict[str, Any]
) -> None:
    state["runtime_mode"] = "quick-fix"
    with pytest.raises(orc.OrchestratorError, match="exact interactive owner message"):
        _gate_authorization(
            cfg,
            state,
            gate="APPROVED: EXECUTE",
            owner_message=False,
            rejection=None,
        )


def test_quick_fix_completion_archives_and_leaves_approved_diff(
    cfg: dict[str, Any], state: dict[str, Any], repo: Path
) -> None:
    state.update(
        {
            "runtime_mode": "quick-fix",
            "branch": "main",
            "approved_write_paths": ["demo.txt"],
            "approved_plan_hash": "plan-hash",
            "executor_report_hash": "report-hash",
            "execute_authorization_source": "OWNER_MESSAGE",
        }
    )
    (repo / "demo.txt").write_text("approved change\n", encoding="utf-8")
    cfg["journals"]["planner"].write_text("plan\n", encoding="utf-8")
    cfg["journals"]["executor"].write_text("report\n", encoding="utf-8")
    cfg["next_agent"].write_text("executor prompt\n", encoding="utf-8")

    _complete_quick_fix(cfg, state)

    assert state["status"] == "QUICK_FIX_COMPLETE"
    assert state["phase"] == "done"
    assert state["quick_fix_changed_paths"] == ["demo.txt"]
    assert (repo / "demo.txt").read_text(encoding="utf-8") == "approved change\n"
    assert all(
        path.stat().st_size == 0
        for path in (*cfg["journals"].values(), cfg["next_agent"])
    )
    archive = cfg["runs_dir"] / state["run_id"] / "quick-fix"
    assert (archive / "planner.md").read_text(encoding="utf-8") == "plan\n"
    assert (archive / "executor.md").read_text(encoding="utf-8") == "report\n"
    assert (archive / "completion.json").is_file()


def test_quick_fix_refuses_a_running_goal(
    orc: Any, cfg: dict[str, Any], state: dict[str, Any], repo: Path
) -> None:
    goal_dir = repo / ".agents" / "goals" / "active"
    goal_dir.mkdir(parents=True)
    (goal_dir / "state.json").write_text('{"status": "RUNNING"}\n', encoding="utf-8")
    cfg["runtime_policy"] = orc.RuntimePolicy(
        schema_version=3,
        mode="quick-fix",
        approval_policy="interactive",
        max_iterations=3,
        roles={},
        unattended=orc.UnattendedPolicy(),
        recovery=orc.RecoveryPolicy(),
    )
    with pytest.raises(orc.OrchestratorError, match="Goal is RUNNING"):
        prepare_task_run(cfg, state["task"])
