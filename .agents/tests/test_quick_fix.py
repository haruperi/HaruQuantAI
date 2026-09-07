"""Focused regression tests for chat-direct Quick-Fix policy."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest


def _select_quick_fix(orc: Any, cfg: dict[str, Any]) -> None:
    """Install the interactive chat-direct Quick-Fix runtime policy."""
    cfg["mode"] = "quick-fix"
    cfg["runtime_policy"] = orc.RuntimePolicy(
        schema_version=3,
        mode="quick-fix",
        approval_policy="interactive",
        max_iterations=3,
        roles={},
        unattended=orc.UnattendedPolicy(),
        recovery=orc.RecoveryPolicy(),
    )


def test_quick_fix_task_api_rejects_before_entry_gate_or_state_mutation(
    orc: Any,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quick-Fix must remain entirely outside Task activation and journals."""
    _select_quick_fix(orc, cfg)
    before = {
        path: path.read_bytes()
        for path in (*cfg["journals"].values(), cfg["next_agent"])
    }

    def fail_entry_gate(_cfg: dict[str, Any]) -> str:
        pytest.fail("Quick-Fix reached the Task clean-main entry gate")

    task_api_module = sys.modules[orc.prepare_task_run.__module__]
    monkeypatch.setattr(task_api_module, "_entry_gate", fail_entry_gate)

    with pytest.raises(orc.OrchestratorError, match="chat-direct"):
        orc.prepare_task_run(cfg, state["task"])

    assert all(path.read_bytes() == content for path, content in before.items())


def test_quick_fix_private_activation_fails_before_branch_or_prompt_mutation(
    orc: Any, cfg: dict[str, Any], state: dict[str, Any]
) -> None:
    """Even an internal activation call cannot create Quick-Fix Task artifacts."""
    _select_quick_fix(orc, cfg)
    state["runtime_mode"] = "quick-fix"
    branch_before = orc._git_ok(cfg["repo"], "branch", "--show-current")
    prompt_before = cfg["next_agent"].read_bytes()

    with pytest.raises(orc.OrchestratorError, match="must not activate Task state"):
        orc._activate_task(cfg, state)

    assert orc._git_ok(cfg["repo"], "branch", "--show-current") == branch_before
    assert cfg["next_agent"].read_bytes() == prompt_before
    assert state.get("branch") in {None, ""}


def test_quick_fix_runtime_policy_requires_interactive_approval(
    orc: Any, tmp_path: Path
) -> None:
    """Unattended authorization remains invalid for chat-direct Quick-Fix."""
    runtime_policy_module = sys.modules[orc.RuntimePolicy.__module__]
    path = tmp_path / "run-config.toml"
    path.write_text(
        "schema_version = 3\n"
        'mode = "quick-fix"\n'
        'approval_policy = "unattended"\n'
        "max_iterations = 3\n",
        encoding="utf-8",
    )
    with pytest.raises(orc.RuntimePolicyError, match="requires interactive"):
        runtime_policy_module.load_runtime_policy(
            path,
            legacy_roles={},
            default_max_iterations=3,
        )
