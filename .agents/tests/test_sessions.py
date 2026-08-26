"""Role-session continuity regression tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "session_runner.py"
SPEC = importlib.util.spec_from_file_location("hq_session_runner", MODULE_PATH)
assert SPEC
assert SPEC.loader
session_runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = session_runner
SPEC.loader.exec_module(session_runner)


def _identity(role: str, iteration: int = 1) -> Any:
    return session_runner.PromptIdentity(
        run_id="run-one",
        role=role,
        iteration=iteration,
        prompt_path=Path("next-agent.md"),
    )


def test_codex_resume_uses_exact_id_not_last() -> None:
    command = session_runner.build_vendor_command(
        brand="codex",
        pointer="prompt",
        model="gpt-5.6-sol",
        effort="high",
        provider="",
        print_timeout="110m",
        session_id="planner-thread",
    )
    assert "planner-thread" in command
    assert "--last" not in command
    assert command.index("resume") < command.index("planner-thread")


def test_agy_resume_uses_exact_conversation_id() -> None:
    command = session_runner.build_vendor_command(
        brand="agy",
        pointer="prompt",
        model="gemini-3.7-flash-high",
        effort="high",
        provider="",
        print_timeout="110m",
        session_id="executor-conversation",
    )
    assert command[command.index("--conversation") + 1] == "executor-conversation"
    assert "--continue" not in command


def test_same_role_iteration_reuses_exact_session() -> None:
    ledger = session_runner._empty_ledger()
    session_runner._record_session(
        ledger,
        _identity("PLANNER", 1),
        brand="codex",
        model="gpt-5.6-sol",
        provider="",
        effort="high",
        session_id="planner-one",
    )
    session_runner._record_session(
        ledger,
        _identity("PLANNER", 2),
        brand="codex",
        model="gpt-5.6-sol",
        provider="",
        effort="high",
        session_id="planner-one",
    )
    record = ledger["sessions"]["PLANNER"]
    assert record["session_id"] == "planner-one"
    assert record["last_iteration"] == 2


def test_cross_role_session_collision_fails_closed() -> None:
    ledger = session_runner._empty_ledger()
    session_runner._record_session(
        ledger,
        _identity("PLANNER"),
        brand="codex",
        model="gpt-5.6-sol",
        provider="",
        effort="high",
        session_id="shared",
    )
    with pytest.raises(session_runner.SessionContinuityError, match="Cross-role"):
        session_runner._record_session(
            ledger,
            _identity("EXECUTOR"),
            brand="agy",
            model="gemini",
            provider="",
            effort="high",
            session_id="shared",
        )


def test_resume_id_mismatch_fails_closed() -> None:
    ledger = session_runner._empty_ledger()
    session_runner._record_session(
        ledger,
        _identity("REVIEWER"),
        brand="cline",
        model="glm-5.3",
        provider="zai-coding-plan",
        effort="xhigh",
        session_id="review-one",
    )
    with pytest.raises(session_runner.SessionContinuityError, match="expected exact"):
        session_runner._record_session(
            ledger,
            _identity("REVIEWER", 2),
            brand="cline",
            model="glm-5.3",
            provider="zai-coding-plan",
            effort="xhigh",
            session_id="review-two",
        )


def test_transport_identity_change_mid_run_fails() -> None:
    ledger = session_runner._empty_ledger()
    session_runner._record_session(
        ledger,
        _identity("EXECUTOR"),
        brand="agy",
        model="model-a",
        provider="",
        effort="high",
        session_id="executor-one",
    )
    record = session_runner._existing_record(ledger, "EXECUTOR")
    assert record is not None
    with pytest.raises(session_runner.SessionContinuityError, match="cannot change"):
        session_runner._validate_record_identity(
            record,
            brand="agy",
            model="model-b",
            provider="",
            effort="high",
        )


def test_new_run_has_separate_session_ledger() -> None:
    assert session_runner._session_state_path("run-a") != session_runner._session_state_path(
        "run-b"
    )


def test_session_ids_are_not_role_prompt_metadata(orc: ModuleType) -> None:
    for path in orc.assemble_config(str(orc.REPO_ROOT))["templates"].values():
        if path.name == "default.md":
            continue
        assert "session_id" not in path.read_text(encoding="utf-8")
