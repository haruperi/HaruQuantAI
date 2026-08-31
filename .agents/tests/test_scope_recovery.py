"""Post-role scope-blocker recovery regression tests."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _write_sessions(repo: Path, run_id: str) -> dict[str, Any]:
    ledger = {
        "schema_version": 1,
        "sessions": {
            "PLANNER": {
                "brand": "codex",
                "model": "gpt-5.6-sol",
                "effort": "medium",
                "provider": "",
                "session_id": "planner-exact",
            },
            "EXECUTOR": {
                "brand": "agy",
                "model": "gemini-3.7-flash-high",
                "effort": "high",
                "provider": "",
                "session_id": "executor-exact",
            },
        },
    }
    path = repo / ".agents" / "runs" / run_id / "role-sessions.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return ledger


def _executor_state(state: dict[str, Any]) -> dict[str, Any]:
    state["branch"] = "main"
    state["phase"] = "executor"
    state["approved_write_paths"] = ["approved.txt"]
    state["next_agent"] = {
        "prompt_sha256": "stale-after-executor",
        "worktree_sha256": "stale-after-executor",
    }
    return state


def _ignore_runtime(repo: Path, state: dict[str, Any]) -> None:
    (repo / ".gitignore").write_text(
        ".agents/runs/\n.agents/workflow.lock\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--no-verify", "-m", "ignore runtime"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    state["baseline"] = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def test_scope_mutation_error_is_structured(orc: ModuleType) -> None:
    with pytest.raises(orc.ScopeMutationError) as caught:
        orc.validate_role_mutations(
            "EXECUTOR",
            {"created": {"outside.txt"}, "modified": set(), "deleted": set()},
            approved_write_paths={"approved.txt"},
        )
    assert caught.value.role == "EXECUTOR"
    assert caught.value.offending_paths == ("outside.txt",)


def test_approved_executor_delta_keeps_normal_validation(orc: ModuleType) -> None:
    orc.validate_role_mutations(
        "EXECUTOR",
        {"created": {"approved.txt"}, "modified": set(), "deleted": set()},
        approved_write_paths={"approved.txt"},
    )


def test_recovery_routes_same_sessions_to_planner_iteration_two(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _ignore_runtime(repo, state)
    state = _executor_state(state)
    before_sessions = _write_sessions(repo, state["run_id"])
    (repo / "approved.txt").write_text("keep approved\n", encoding="utf-8")
    (repo / "outside.txt").write_text("keep outside\n", encoding="utf-8")
    (repo / ".agents/task/planner.md").write_text(
        "pre-existing planner work\n", encoding="utf-8"
    )
    product_before = {
        path.name: path.read_bytes()
        for path in (repo / "approved.txt", repo / "outside.txt")
    }

    orc.recover_scope_blocker(cfg, state)

    assert state["phase"] == "planner"
    assert state["iteration"] == 2
    assert state["scope_blocker"]["offending_paths"] == ["outside.txt"]
    assert state["blockers"][-1]["raised_by"] == "ORCHESTRATOR"
    assert state["blockers"][-1]["status"] == "OPEN"
    assert state["history"][-2]["phase"] == "scope_validation_failed"
    assert state["history"][-1]["phase"] == "scope_blocker_recovery_materialized"
    artifact = orc.parse_next_agent(repo / ".agents/task/next-agent.md")
    assert artifact.metadata["source_role"] == "ORCHESTRATOR"
    assert artifact.metadata["handoff"] == "SCOPE_BLOCKED"
    assert artifact.metadata["target_role"] == "PLANNER"
    assert artifact.metadata["iteration"] == 2
    assert state["next_agent"]["worktree_sha256"] == orc._worktree_fingerprint(repo)
    after_sessions = json.loads(
        (repo / ".agents" / "runs" / state["run_id"] / "role-sessions.json").read_text(
            encoding="utf-8"
        )
    )
    assert after_sessions == before_sessions
    assert "REVIEWER" not in after_sessions["sessions"]
    assert {
        path.name: path.read_bytes()
        for path in (repo / "approved.txt", repo / "outside.txt")
    } == product_before


def test_uninvoked_planner_recovery_prompt_can_refresh_legacy_evidence(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _ignore_runtime(repo, state)
    state = _executor_state(state)
    _write_sessions(repo, state["run_id"])
    (repo / "outside.txt").write_text("outside\n", encoding="utf-8")
    orc.recover_scope_blocker(cfg, state)
    state["scope_blocker"]["offending_paths"] = [
        ".agents/task/planner.md",
        "outside.txt",
    ]
    state["blockers"][-1]["offending_paths"] = [
        ".agents/task/planner.md",
        "outside.txt",
    ]

    orc.recover_scope_blocker(cfg, state)

    assert state["phase"] == "planner"
    assert state["iteration"] == 2
    assert state["scope_blocker"]["offending_paths"] == ["outside.txt"]
    assert state["history"][-1]["phase"] == "scope_blocker_recovery_refreshed"


def test_scope_recovery_requires_exact_recoverable_state(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    state["branch"] = "main"
    state["phase"] = "reviewer"
    with pytest.raises(orc.OrchestratorError, match="executor/scope_blocked"):
        orc.recover_scope_blocker(cfg, state)


def test_preserved_scope_fingerprint_mismatch_fails_closed(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _ignore_runtime(repo, state)
    state = _executor_state(state)
    _write_sessions(repo, state["run_id"])
    (repo / "outside.txt").write_text("first\n", encoding="utf-8")
    orc.record_scope_blocker(
        cfg, state, orc.ScopeMutationError("EXECUTOR", ["outside.txt"])
    )
    (repo / "outside.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(orc.OrchestratorError, match="fingerprint changed"):
        orc.recover_scope_blocker(cfg, state)


def test_revised_planner_can_authorize_previous_path(orc: ModuleType) -> None:
    delta = {"created": set(), "modified": {".gitignore"}, "deleted": set()}
    orc.validate_role_mutations("EXECUTOR", delta, approved_write_paths={".gitignore"})
    with pytest.raises(orc.ScopeMutationError):
        orc.validate_role_mutations(
            "EXECUTOR", delta, approved_write_paths={"approved.txt"}
        )


def test_goal_recovery_preserves_frozen_progress_and_active_child(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ignore_runtime(repo, state)
    state = _executor_state(state)
    _write_sessions(repo, state["run_id"])
    (repo / "outside.txt").write_text("preserve\n", encoding="utf-8")
    goal: dict[str, Any] = {
        "goal_run_id": "goal-one",
        "status": "RUNNING",
        "completed_entries": [],
        "remaining_entries": ["1.8", "1.9"],
        "active_child": {
            "entry": "1.8",
            "run_id": state["run_id"],
            "phase": "executor",
            "status": "RUNNING",
        },
    }
    saved: list[dict[str, Any]] = []
    monkeypatch.setattr(orc, "assemble_config", lambda _repo: cfg)
    monkeypatch.setattr(orc, "_require_cli_mode", lambda _cfg: None)
    monkeypatch.setattr(orc, "_enable_scope_recovery_transition", lambda _cfg: None)
    monkeypatch.setattr(orc, "load_goal_state", lambda _cfg, _run_id: goal)
    monkeypatch.setattr(orc, "_load_state", lambda _cfg, _run_id: state)
    monkeypatch.setattr(
        orc, "save_goal_state", lambda _cfg, value: saved.append(dict(value))
    )
    monkeypatch.setattr(orc, "format_goal_status", lambda _goal: "status")

    result = orc.cmd_goal_recover_scope_blocker(
        argparse.Namespace(repo=str(repo), goal_run_id="goal-one")
    )

    assert result == 0
    assert goal["completed_entries"] == []
    assert goal["remaining_entries"] == ["1.8", "1.9"]
    assert goal["active_child"]["entry"] == "1.8"
    assert goal["active_child"]["phase"] == "planner"
    assert state["iteration"] == 2
    assert saved
