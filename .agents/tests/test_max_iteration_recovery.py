"""Regression tests for owner-authorized exact max-iteration recovery."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _prepare(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    cfg["max_iterations"] = 5
    state["status"] = "MAX_ITERATIONS"
    state["phase"] = "planner"
    state["iteration"] = 6
    state["branch"] = "main"
    fields = orc._build_fields(state, cfg)
    body = orc.compose_prompt(Path(cfg["templates"]["planner"]), fields)
    metadata = {
        "prompt_schema_version": 1,
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": 6,
        "source_role": "REVIEWER",
        "target_role": "PLANNER",
        "handoff": "CHANGES_REQUESTED",
        "branch": "main",
        "baseline_commit": state["baseline"],
        "source_head": state["baseline"],
        "template_path": "docs/templates/prompt/planner.md",
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    Path(cfg["next_agent"]).write_text(
        orc._render_next_agent(metadata, body), encoding="utf-8"
    )
    ledger = repo / ".agents/runs" / state["run_id"] / "role-sessions.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sessions": {
                    role: {"session_id": role.lower(), "last_iteration": 5}
                    for role in ("PLANNER", "EXECUTOR", "REVIEWER")
                },
            }
        ),
        encoding="utf-8",
    )


def test_reopens_exact_next_iteration_without_mutating_worktree(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    before = orc._worktree_fingerprint(repo)
    prompt_before = Path(cfg["next_agent"]).read_bytes()
    journals_before = {
        role: path.read_bytes() for role, path in cfg["journals"].items()
    }

    orc.recover_max_iterations(
        cfg,
        state,
        expected_run_id=state["run_id"],
        expected_iteration=6,
        expected_worktree_fingerprint=before,
    )

    assert state["status"] == "RUNNING"
    assert state["phase"] == "planner"
    assert state["iteration"] == 6
    assert Path(cfg["next_agent"]).read_bytes() == prompt_before
    assert {
        role: path.read_bytes() for role, path in cfg["journals"].items()
    } == journals_before


def test_rejects_more_than_one_iteration_extension(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    _prepare(orc, cfg, state, repo)
    state["iteration"] = 7
    with pytest.raises(orc.OrchestratorError, match="exactly one"):
        orc.recover_max_iterations(
            cfg,
            state,
            expected_run_id=state["run_id"],
            expected_iteration=7,
            expected_worktree_fingerprint=orc._worktree_fingerprint(repo),
        )


def test_unattended_router_activates_one_fresh_recovery_generation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    role = orc.RolePolicy(
        vendor="codex", brand="codex", model="normal", effort="medium"
    )
    cfg["max_iterations"] = 2
    cfg["runtime_policy"] = orc.RuntimePolicy(
        schema_version=2,
        mode="multi-delegate",
        approval_policy="unattended",
        max_iterations=2,
        roles=dict.fromkeys(("planner", "executor", "reviewer"), role),
        unattended=orc.UnattendedPolicy(allow_execute=True),
        recovery=orc.RecoveryPolicy(
            enabled=True,
            max_escalations=1,
            additional_iterations=1,
        ),
    )
    state.update(
        {
            "phase": "planner_blocked",
            "iteration": 3,
            "effective_max_iterations": 2,
            "recovery_generation": 0,
        }
    )

    result = orc.router(cfg, state)

    assert result["status"] == "RUNNING"
    assert result["session_generation"] == "recovery-1"
    assert result["effective_max_iterations"] == 3
    assert result["recovery_generation"] == 1


def test_recovery_exhaustion_blocks_without_a_second_escalation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    cfg["max_iterations"] = 2
    state.update(
        {
            "phase": "planner",
            "iteration": 4,
            "effective_max_iterations": 3,
            "recovery_generation": 1,
            "session_generation": "recovery-1",
        }
    )

    result = orc.router(cfg, state)

    assert result["status"] == "MAX_ITERATIONS"
    assert result["recovery_generation"] == 1


def test_policy_drift_at_exhaustion_precedes_recovery_or_terminal_mutation(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    policy_path = repo / ".agents" / "run-config.toml"
    policy_path.write_text(
        """schema_version = 2
mode = "solo"
approval_policy = "unattended"
max_iterations = 2

[unattended]
allow_execute = true
allow_local_commit = true
allow_local_merge = true

[recovery]
enabled = true
max_escalations = 1
additional_iterations = 1
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"

[roles.planner]
vendor = "codex"
model = "normal"
effort = "medium"

[roles.executor]
vendor = "codex"
model = "normal"
effort = "medium"

[roles.reviewer]
vendor = "codex"
model = "normal"
effort = "medium"
""",
        encoding="utf-8",
    )
    frozen_policy = orc.load_runtime_policy(
        policy_path, legacy_roles={}, default_max_iterations=5
    )
    state.update(
        {
            "phase": "planner",
            "iteration": 3,
            "effective_max_iterations": 2,
            "recovery_generation": 0,
            "session_generation": "normal",
            "runtime_policy_fingerprint": frozen_policy.fingerprint,
            "scope_fingerprint": orc.scope_fingerprint(state["task"]),
        }
    )
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8")
        .replace("enabled = true", "enabled = false")
        .replace("max_escalations = 1", "max_escalations = 0")
        .replace("additional_iterations = 1", "additional_iterations = 0"),
        encoding="utf-8",
    )
    cfg.update(
        {
            "runtime_policy_path": policy_path,
            "runtime_policy": orc.load_runtime_policy(
                policy_path, legacy_roles={}, default_max_iterations=5
            ),
            "legacy_roles": {},
            "max_iterations": 2,
        }
    )

    with pytest.raises(orc.OrchestratorError, match="changed after run activation"):
        orc.router(cfg, state)

    assert state["status"] == "RUNNING"
    assert state["recovery_generation"] == 0
    assert not any(
        item.get("phase")
        in {"automatic_recovery_activated", "max_iterations_exhausted"}
        for item in state["history"]
    )
