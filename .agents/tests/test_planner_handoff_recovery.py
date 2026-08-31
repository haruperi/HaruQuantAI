"""Recovery tests for a validated Planner handoff not yet persisted in state."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PLANNER_SESSION = "planner-exact"


def _prepare_handoff(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> tuple[bytes, bytes]:
    state["branch"] = "main"
    state["phase"] = "planner"
    journal = repo / ".agents/task/planner.md"
    journal.write_text(
        "# Dry Run 1\n\n"
        "ALLOWED_WRITE_PATHS:\n- .gitignore\n- demo.txt\n"
        "END_ALLOWED_WRITE_PATHS:\n\n"
        "STOPPED : PLANNER\nACTIVATING : EXECUTOR\n"
        "HANDOFF : PENDING_APPROVAL\n",
        encoding="utf-8",
    )
    plan_hash = orc._sha_file(journal)
    template = repo / "docs/templates/prompt/executor.md"
    body = re.sub(r"\{\{[^{}]+\}\}", "test-value", template.read_text(encoding="utf-8"))
    prompt = repo / ".agents/task/next-agent.md"
    prompt.write_text(
        "+++\n"
        "prompt_schema_version = 1\n"
        f'run_id = "{state["run_id"]}"\n'
        f'task_id = "{state["task"]["task_id"]}"\n'
        "iteration = 1\n"
        'source_role = "PLANNER"\n'
        'target_role = "EXECUTOR"\n'
        'handoff = "PENDING_APPROVAL"\n'
        'branch = "main"\n'
        f'baseline_commit = "{state["baseline"]}"\n'
        f'source_head = "{state["baseline"]}"\n'
        'template_path = "docs/templates/prompt/executor.md"\n'
        "requires_owner_gate = true\n"
        'owner_gate = "APPROVED: EXECUTE"\n'
        'allowed_write_paths = [".gitignore", "demo.txt"]\n'
        "+++\n\n"
        f"Approved plan hash: `{plan_hash}`\n\n" + body,
        encoding="utf-8",
    )
    ledger = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sessions": {"PLANNER": {"session_id": PLANNER_SESSION}},
            }
        ),
        encoding="utf-8",
    )
    return journal.read_bytes(), prompt.read_bytes()


def _recover(orc: ModuleType, cfg: dict[str, Any], state: dict[str, Any]) -> None:
    orc.recover_planner_handoff(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_planner_session_id=PLANNER_SESSION,
        expected_worktree_fingerprint=orc._worktree_fingerprint(cfg["repo"]),
    )


def test_valid_planner_handoff_recovers_without_mutation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    journal_before, prompt_before = _prepare_handoff(orc, cfg, state, repo)
    fingerprint_before = orc._worktree_fingerprint(repo)

    _recover(orc, cfg, state)

    assert state["phase"] == "approve"
    assert state["iteration"] == 1
    assert state["plan_hash"] == orc._sha_file(repo / ".agents/task/planner.md")
    assert state["next_agent"]["target_role"] == "EXECUTOR"
    assert state["next_agent"]["handoff"] == "PENDING_APPROVAL"
    assert state["next_agent"]["worktree_sha256"] == fingerprint_before
    assert state["history"][-1]["phase"] == "planner"
    assert state["history"][-1]["recovered"] is True
    assert (repo / ".agents/task/planner.md").read_bytes() == journal_before
    assert (repo / ".agents/task/next-agent.md").read_bytes() == prompt_before
    ledger = json.loads(
        (repo / ".agents/runs" / state["run_id"] / "role-sessions.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["sessions"]["PLANNER"]["session_id"] == PLANNER_SESSION
    assert "EXECUTOR" not in ledger["sessions"]
    assert "REVIEWER" not in ledger["sessions"]


def test_later_handoff_repairs_only_missing_path_metadata(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    state["iteration"] = 3
    prompt = repo / ".agents/task/next-agent.md"
    original = prompt.read_text(encoding="utf-8")
    original = original.replace("iteration = 1", "iteration = 3", 1)
    original = re.sub(r"(?m)^allowed_write_paths = .*\n", "", original)
    prompt.write_text(original, encoding="utf-8")
    ledger_path = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["sessions"] = {
        "PLANNER": {"session_id": PLANNER_SESSION, "last_iteration": 3},
        "EXECUTOR": {"session_id": "executor", "last_iteration": 2},
        "REVIEWER": {"session_id": "reviewer", "last_iteration": 2},
    }
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    body_before = orc.parse_next_agent(prompt).body

    _recover(orc, cfg, state)

    artifact = orc.parse_next_agent(prompt)
    assert state["phase"] == "approve"
    assert state["iteration"] == 3
    assert artifact.metadata["allowed_write_paths"] == [".gitignore", "demo.txt"]
    assert artifact.body == body_before
    assert (
        (repo / ".agents/task/planner.md")
        .read_text(encoding="utf-8")
        .endswith("HANDOFF : PENDING_APPROVAL\n")
    )


@pytest.mark.parametrize("bad_phase", ["approve", "executor", "reviewer"])
def test_recovery_rejects_wrong_phase(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
    bad_phase: str,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    state["phase"] = bad_phase
    with pytest.raises(orc.OrchestratorError, match="planner phase"):
        _recover(orc, cfg, state)


def test_recovery_rejects_changed_journal(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    with (repo / ".agents/task/planner.md").open("a", encoding="utf-8") as handle:
        handle.write("changed\n")
    with pytest.raises(orc.OrchestratorError, match="journal changed"):
        _recover(orc, cfg, state)


def test_recovery_rejects_altered_prompt(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    prompt = repo / ".agents/task/next-agent.md"
    prompt.write_text(
        prompt.read_text(encoding="utf-8").replace(
            'target_role = "EXECUTOR"', 'target_role = "REVIEWER"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(orc.OrchestratorError):
        _recover(orc, cfg, state)


@pytest.mark.parametrize("role", ["EXECUTOR", "REVIEWER"])
def test_recovery_rejects_downstream_session(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
    role: str,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    path = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    ledger["sessions"][role] = {"session_id": "unexpected"}
    path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(orc.OrchestratorError, match="exactly one Planner"):
        _recover(orc, cfg, state)


def test_recovery_rejects_run_branch_head_and_session_mismatches(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    with pytest.raises(orc.OrchestratorError, match="run identity"):
        orc.recover_planner_handoff(
            cfg,
            state,
            expected_run_id="wrong-run",
            expected_planner_session_id=PLANNER_SESSION,
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )
    state["branch"] = "wrong"
    with pytest.raises(orc.OrchestratorError, match="branch mismatch"):
        _recover(orc, cfg, state)
    state["branch"] = "main"
    state["baseline"] = "0" * 40
    with pytest.raises(orc.OrchestratorError, match="baseline HEAD"):
        _recover(orc, cfg, state)
    state["baseline"] = orc._git_ok(repo, "rev-parse", "HEAD")
    with pytest.raises(orc.OrchestratorError, match="session identity"):
        orc.recover_planner_handoff(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_planner_session_id="wrong-session",
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )


def test_recovery_rejects_worktree_fingerprint_mismatch(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    with pytest.raises(orc.OrchestratorError, match="fingerprint mismatch"):
        orc.recover_planner_handoff(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_planner_session_id=PLANNER_SESSION,
            expected_worktree_fingerprint="0" * 64,
        )


def test_goal_recovery_preserves_progress_and_active_child(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_handoff(orc, cfg, state, repo)
    fingerprint = orc._worktree_fingerprint(repo)
    goal: dict[str, Any] = {
        "goal_run_id": "goal-one",
        "status": "RUNNING",
        "completed_entries": [],
        "remaining_entries": ["1.8", "1.9"],
        "active_child": {
            "entry": "1.8",
            "run_id": state["run_id"],
            "phase": "planner",
            "status": "RUNNING",
        },
    }
    saved: list[dict[str, Any]] = []
    monkeypatch.setattr(orc, "assemble_config", lambda _repo: cfg)
    monkeypatch.setattr(orc, "_require_cli_mode", lambda _cfg: None)
    monkeypatch.setattr(orc, "load_goal_state", lambda _cfg, _run_id: goal)
    monkeypatch.setattr(orc, "_load_state", lambda _cfg, _run_id: state)
    monkeypatch.setattr(
        orc, "save_goal_state", lambda _cfg, value: saved.append(dict(value))
    )
    monkeypatch.setattr(orc, "format_goal_status", lambda _goal: "status")
    monkeypatch.setattr(
        orc,
        "WorkflowLock",
        lambda _repo: type(
            "NoopLock",
            (),
            {"acquire": lambda self: None, "release": lambda self: None},
        )(),
    )

    result = orc.cmd_goal_recover_planner_handoff(
        argparse.Namespace(
            repo=str(repo),
            goal_run_id="goal-one",
            task_run_id=state["run_id"],
            planner_session_id=PLANNER_SESSION,
            worktree_fingerprint=fingerprint,
        )
    )

    assert result == 0
    assert state["phase"] == "approve"
    assert goal["completed_entries"] == []
    assert goal["remaining_entries"] == ["1.8", "1.9"]
    assert goal["active_child"]["entry"] == "1.8"
    assert goal["active_child"]["phase"] == "approve"
    assert saved
