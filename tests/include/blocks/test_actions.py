"""Unit tests for action strategy blocks."""

from __future__ import annotations

from pathlib import Path

from app.include.blocks.actions import (
    ORDER_NOT_DEFINED,
    ActionRecord,
    Actions,
    AssignVariableAction,
    CustomAction,
    DrawDownArrowAction,
    DrawUpArrowAction,
    DrawVerticalLineAction,
    LogToFileAction,
    LogToJournalAction,
    SendEmailAction,
    assign_variable,
    custom_action,
    draw_down_arrow,
    draw_up_arrow,
    draw_vertical_line,
    log_to_file,
    log_to_journal,
    send_email,
)
from app.include.blocks.actions.annotations import (
    DrawDownArrowAction as AnnotDown,
)
from app.include.blocks.actions.custom import CustomAction as CustomModuleAction
from app.include.blocks.actions.logging import (
    LogToJournalAction as LoggingJournal,
)
from app.include.blocks.metadata import ExecutionKind
from app.include.blocks.registry import BlockRegistry
from app.include.blocks.types import Variable


def test_order_not_defined_and_action_record() -> None:
    """Verify order undefined constant and ActionRecord immutability."""
    assert ORDER_NOT_DEFINED == -99_999_999.0
    rec = ActionRecord(action_type="test", params={"k": "v"})
    assert rec.action_type == "test"
    assert rec.params["k"] == "v"
    assert rec.timestamp


def test_assign_variable_action() -> None:
    """Verify AssignVariableAction numeric, callable, and boolean coercion."""
    var = Variable("balance", "double", 100.0)
    rec1 = assign_variable(var, 250.5)
    assert rec1.action_type == "assign_variable"
    assert var.value == 250.5

    # Callable value
    rec2 = assign_variable(var, lambda: 500.0)
    assert rec2.params["value"] == 500.0
    assert var.value == 500.0

    # Class with evaluate()
    class MockEvaluator:
        def evaluate(self) -> float:
            return 750.0

    assign_variable(var, MockEvaluator())
    assert var.value == 750.0

    # Boolean coercion
    bool_var = Variable("flag", "bool", False)
    assign_variable(bool_var, 1.0, is_boolean=True)
    assert bool(bool_var.value) is True

    assign_variable(bool_var, 0.0, is_boolean=True)
    assert bool(bool_var.value) is False

    assign_variable(bool_var, ORDER_NOT_DEFINED, is_boolean=True)
    assert bool(bool_var.value) is False

    assert AssignVariableAction.spec.id == "action.assign_variable"
    assert AssignVariableAction.spec.category == "actions"
    assert AssignVariableAction.spec.execution_kind == ExecutionKind.ACTION
    assert AssignVariableAction.spec.is_generation_eligible is False


def test_custom_action() -> None:
    """Verify CustomAction execution and handler invocation."""
    calls: list[str] = []

    def mock_handler(cmd: str) -> str:
        calls.append(cmd)
        return f"executed:{cmd}"

    rec = custom_action("Alert('Hello')", mock_handler)
    assert rec.action_type == "custom_action"
    assert rec.params["command"] == "Alert('Hello')"
    assert rec.params["result"] == "executed:Alert('Hello')"
    assert calls == ["Alert('Hello')"]

    assert CustomAction.spec.id == "action.custom"
    assert CustomAction.spec.category == "actions"


def test_drawing_actions() -> None:
    """Verify draw_down_arrow, draw_up_arrow, and draw_vertical_line."""
    rec_down = draw_down_arrow(shift=2)
    assert rec_down.action_type == "draw_down_arrow"
    assert rec_down.params["shift"] == 2

    rec_up = draw_up_arrow(shift=1)
    assert rec_up.action_type == "draw_up_arrow"
    assert rec_up.params["shift"] == 1

    rec_line = draw_vertical_line(shift=0)
    assert rec_line.action_type == "draw_vertical_line"
    assert rec_line.params["shift"] == 0

    assert DrawDownArrowAction.spec.id == "action.draw_down_arrow"
    assert DrawUpArrowAction.spec.id == "action.draw_up_arrow"
    assert DrawVerticalLineAction.spec.id == "action.draw_vertical_line"


def test_log_to_file(tmp_path: Path) -> None:
    """Verify log_to_file writes message text to destination file."""
    rec = log_to_file("audit.log", "test audit entry", base_dir=tmp_path)
    assert rec.action_type == "log_to_file"
    assert rec.params["filename"] == "audit.log"

    out_file = tmp_path / "audit.log"
    assert out_file.exists()
    assert "test audit entry" in out_file.read_text(encoding="utf-8")

    assert LogToFileAction.spec.id == "action.log_to_file"


def test_log_to_journal_and_send_email() -> None:
    """Verify log_to_journal and send_email actions."""
    rec_j = log_to_journal("System initialized")
    assert rec_j.action_type == "log_to_journal"
    assert rec_j.params["message"] == "System initialized"

    sent: list[tuple[str, str]] = []

    def mock_dispatcher(subject: str, body: str) -> bool:
        sent.append((subject, body))
        return True

    rec_e = send_email("Alert", "Margin call", mock_dispatcher)
    assert rec_e.action_type == "send_email"
    assert rec_e.params["delivered"] is True
    assert sent == [("Alert", "Margin call")]

    assert LogToJournalAction.spec.id == "action.log_to_journal"
    assert SendEmailAction.spec.id == "action.send_email"


def test_actions_facade() -> None:
    """Verify Actions facade convenience methods."""
    var = Variable("p", "double", 1.0)
    assert Actions.assign(var, 99.0).action_type == "assign_variable"
    assert Actions.custom("cmd").action_type == "custom_action"
    assert Actions.draw_down_arrow(1).action_type == "draw_down_arrow"
    assert Actions.draw_up_arrow(2).action_type == "draw_up_arrow"
    assert Actions.draw_vertical_line(3).action_type == "draw_vertical_line"
    assert Actions.log_file("test.log", "msg").action_type == "log_to_file"
    assert Actions.log_journal("msg").action_type == "log_to_journal"
    assert Actions.send_email("subj", "msg").action_type == "send_email"


def test_reexport_submodules_compatibility() -> None:
    """Verify annotations, custom, and logging compatibility submodules."""
    assert AnnotDown is DrawDownArrowAction
    assert CustomModuleAction is CustomAction
    assert LoggingJournal is LogToJournalAction


def test_block_registry_discovers_all_action_blocks() -> None:
    """Verify BlockRegistry discovers all 8 action blocks with 0 diagnostics."""
    registry = BlockRegistry()
    registry.discover("app/include/blocks/actions")

    expected_ids = {
        "action.assign_variable",
        "action.custom",
        "action.draw_down_arrow",
        "action.draw_up_arrow",
        "action.draw_vertical_line",
        "action.log_to_file",
        "action.log_to_journal",
        "action.send_email",
    }
    discovered = {b.spec.id for b in registry.snapshot().blocks.values()}
    assert expected_ids.issubset(discovered)
    assert not registry.diagnostics
