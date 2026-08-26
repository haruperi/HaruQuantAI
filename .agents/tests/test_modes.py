"""Transport-mode regression tests."""

from __future__ import annotations

from types import ModuleType

import pytest


@pytest.mark.parametrize("mode", ["solo", "delegate", "manual", "UNCONFIGURED"])
def test_cli_runner_rejects_non_process_modes(orc: ModuleType, mode: str) -> None:
    with pytest.raises(orc.OrchestratorError):
        orc._require_cli_mode({"mode": mode})


def test_cli_runner_accepts_multi_delegate(orc: ModuleType) -> None:
    orc._require_cli_mode({"mode": "multi-delegate"})


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
