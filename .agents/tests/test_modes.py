"""Transport-mode regression tests."""

from __future__ import annotations

import importlib.util
import sys
from types import ModuleType
from typing import Any

import pytest


def _load_stub_agent(orc: ModuleType) -> ModuleType:
    path = orc.AGENTS_DIR / "tests" / "stub_agent.py"
    spec = importlib.util.spec_from_file_location("ide_transport_stub", path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_exposes_no_auto_approve_override(
    orc: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = orc.build_parser()
    help_text = parser.format_help()
    assert "--auto-approve" not in help_text
    with pytest.raises(SystemExit):
        parser.parse_args(["resume", "--help"])
    resume_help = capsys.readouterr().out
    assert "--role-complete" in resume_help
    assert "--app-agent-id" in resume_help


def test_all_configured_modes_are_first_class(orc: ModuleType) -> None:
    for mode in (
        "solo",
        "solo-headless",
        "delegate",
        "delegate-headless",
        "delegate-multi",
        "manual",
    ):
        orc._require_cli_mode({"mode": mode})
    with pytest.raises(orc.OrchestratorError):
        orc._require_cli_mode({"mode": "UNCONFIGURED"})


def test_manual_mode_activates_task_then_waits_for_role_chat(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    cfg["mode"] = "manual"

    result = orc.router(cfg, state)

    assert result["phase"] == "planner"
    assert result["status"] == "RUNNING"
    assert cfg["next_agent"].stat().st_size > 0


@pytest.mark.parametrize("mode", ["solo", "delegate"])
def test_ide_mode_activates_and_prepares_inline_role_boundary(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    mode: str,
) -> None:
    cfg["mode"] = mode
    state["run_id"] = "self-test"

    result = orc.router(cfg, state)

    assert result["phase"] == "planner"
    assert result["ide_role_invocation"]["role"] == "PLANNER"
    assert result["ide_role_invocation"]["mode"] == mode
    assert cfg["next_agent"].stat().st_size > 0

    _load_stub_agent(orc)._planner(cfg["repo"], state["iteration"])
    result = orc.router(
        cfg,
        state,
        role_complete=True,
        app_agent_id="planner-agent" if mode == "delegate" else None,
    )

    assert result["phase"] == "approve"
    assert "ide_role_invocation" not in result
    if mode == "delegate":
        assert orc.expected_delegate_handle(cfg, state, "PLANNER") == "planner-agent"


@pytest.mark.parametrize("mode", ["solo", "delegate"])
def test_ide_unattended_policy_automatically_satisfies_execute_gate(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    mode: str,
) -> None:
    cfg["mode"] = mode
    policy = orc.RuntimePolicy(
        schema_version=3,
        mode=mode,
        approval_policy="unattended",
        max_iterations=5,
        roles={},
        unattended=orc.UnattendedPolicy(
            allow_execute=True,
            allow_local_commit=True,
            allow_local_merge=True,
        ),
        recovery=orc.RecoveryPolicy(),
    )
    cfg["runtime_policy"] = policy
    state["run_id"] = "self-test"
    state["runtime_policy_fingerprint"] = policy.fingerprint
    state["scope_fingerprint"] = orc.scope_fingerprint(state["task"])

    orc.router(cfg, state)
    _load_stub_agent(orc)._planner(cfg["repo"], state["iteration"])
    result = orc.router(
        cfg,
        state,
        role_complete=True,
        app_agent_id="planner-agent" if mode == "delegate" else None,
    )

    assert result["phase"] == "executor"
    assert result["ide_role_invocation"]["role"] == "EXECUTOR"
    authorization = [
        item for item in result["history"] if item["phase"] == "execute_authorization"
    ]
    assert authorization[-1]["source"] == "RUN_PREAUTHORIZATION"


@pytest.mark.parametrize("mode", ["solo", "delegate"])
def test_ide_unattended_policy_reaches_commit_handler_without_owner_flag(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    workflow_engine = sys.modules["workflow_engine"]
    cfg["mode"] = mode
    cfg["runtime_policy"] = orc.RuntimePolicy(
        schema_version=3,
        mode=mode,
        approval_policy="unattended",
        max_iterations=5,
        roles={},
        unattended=orc.UnattendedPolicy(
            allow_execute=True,
            allow_local_commit=True,
            allow_local_merge=True,
        ),
        recovery=orc.RecoveryPolicy(),
    )
    state["phase"] = "commit_gate"
    invoked: list[bool] = []

    def handle_commit_gate(
        _cfg: dict[str, Any],
        current: dict[str, Any],
        *,
        approved: bool,
        rejection: str | None,
    ) -> None:
        assert rejection is None
        invoked.append(approved)
        current["phase"] = "done"

    monkeypatch.setattr(workflow_engine, "_handle_commit_gate", handle_commit_gate)

    result = orc.router(cfg, state)

    assert result["phase"] == "done"
    assert invoked == [False]


def test_procedure_transport_language_is_current(orc: ModuleType) -> None:
    procedure = (orc.REPO_ROOT / ".agents/PROCEDURE.md").read_text(encoding="utf-8")
    for obsolete in (
        "already-validated artifact",
        "Proceed with Reviewer",
        "stepped mode",
        "fresh Planner chat",
        "fresh Executor chat",
        "fresh Reviewer close-out chat",
    ):
        assert obsolete not in procedure
    assert "CONTINUE: REVIEWER" in procedure
    assert "CONTINUE: GOAL" in procedure
    assert "transport/resume" in procedure
    assert "same Planner conversation" in procedure
    assert "same Reviewer conversation" in procedure
    assert "new dedicated Planner/Executor/Reviewer chat set" in procedure
    assert "The only owner authorization messages are:" in procedure


def test_protocol_declares_same_role_continuity(orc: ModuleType) -> None:
    cfg = orc.assemble_config(str(orc.REPO_ROOT))
    policy = cfg["session_continuity"]
    assert policy["scope"] == "workflow-run"
    assert policy["same_role_resume"] is True
    assert policy["new_run_new_sessions"] is True
    assert policy["reviewer_closeout_reuses_reviewer"] is True
    assert policy["session_context_is_authority"] is False


def test_goal_adds_no_authorization_gate(orc: ModuleType) -> None:
    agents = (orc.REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "APPROVED: GOAL" not in agents
    assert "APPROVED: EXECUTE" in agents
    assert "APPROVED: COMMIT" in agents
