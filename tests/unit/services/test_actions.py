"""Unit tests for StrategyQuant X Actions building blocks.

Tests:
    - AssignVariableAction and assign_variable with values, callables, and boolean coercion.
    - CustomAction and custom_action with custom command strings and handlers.
    - Chart annotation actions: DrawDownArrowAction, DrawUpArrowAction, DrawVerticalLineAction.
    - LogToFileAction and log_to_file writing to sandboxed file directory.
    - LogToJournalAction and log_to_journal.
    - SendEmailAction and send_email with optional delivery dispatcher.
    - Centralized Actions facade methods.
"""

from __future__ import annotations

from pathlib import Path

from app.services.utils.actions import (
    ORDER_NOT_DEFINED,
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
from app.services.utils.types import Variable


class FormulaMock:
    """Mock formula block with evaluate() method."""

    def __init__(self, value: float) -> None:
        self._val = value

    def evaluate(self) -> float:
        return self._val


def test_assign_variable_action() -> None:
    """Verify variable assignment with raw values and formula objects."""
    var = Variable[float]("risk", "float", 0.01)

    action = AssignVariableAction(var, 0.02)
    record = action.execute()
    assert var.value == 0.02
    assert record.action_type == "assign_variable"
    assert record.params["name"] == "risk"
    assert record.params["value"] == 0.02

    # Callable value
    assign_variable(var, lambda: 0.05)
    assert var.value == 0.05

    # Object with evaluate() method
    assign_variable(var, FormulaMock(0.08))
    assert var.value == 0.08


def test_assign_variable_boolean_coercion() -> None:
    """Verify boolean coercion where 0 and -1 map to False per SQX rules."""
    bool_var = Variable[bool]("signal", "bool", False)

    # 0.0 maps to False
    assign_variable(bool_var, 0.0, is_boolean=True)
    assert bool_var.get_value() is False

    # ORDER_NOT_DEFINED (-1.0) maps to False
    assign_variable(bool_var, ORDER_NOT_DEFINED, is_boolean=True)
    assert bool_var.get_value() is False

    # 1.0 maps to True
    assign_variable(bool_var, 1.0, is_boolean=True)
    assert bool_var.get_value() is True

    # Any non-zero positive number maps to True
    assign_variable(bool_var, 42.0, is_boolean=True)
    assert bool_var.get_value() is True

    # Non-numeric object coercion
    assign_variable(bool_var, "active", is_boolean=True)
    assert bool_var.get_value() is True

    assign_variable(bool_var, "", is_boolean=True)
    assert bool_var.get_value() is False


def test_custom_action() -> None:
    """Verify custom action command descriptor and optional handler execution."""
    rec = custom_action("Alert('Breakout')")
    assert rec.action_type == "custom_action"
    assert rec.params["command"] == "Alert('Breakout')"
    assert rec.params["result"] is None

    # With handler
    executed: list[str] = []

    def my_handler(cmd: str) -> str:
        executed.append(cmd)
        return "SUCCESS"

    rec2 = custom_action("CloseAllOrders()", handler=my_handler)
    assert rec2.params["result"] == "SUCCESS"
    assert executed == ["CloseAllOrders()"]

    action = CustomAction("CustomCmd")
    assert action.execute().params["command"] == "CustomCmd"


def test_chart_drawing_actions() -> None:
    """Verify down arrow, up arrow, and vertical line action descriptors."""
    rec_down = draw_down_arrow(shift=2)
    assert rec_down.action_type == "draw_down_arrow"
    assert rec_down.params["shift"] == 2

    rec_up = draw_up_arrow(shift=0)
    assert rec_up.action_type == "draw_up_arrow"
    assert rec_up.params["shift"] == 0

    rec_vl = draw_vertical_line(shift=3)
    assert rec_vl.action_type == "draw_vertical_line"
    assert rec_vl.params["shift"] == 3

    # Direct class instantiations
    assert DrawDownArrowAction(1).execute().params["shift"] == 1
    assert DrawUpArrowAction(4).execute().params["shift"] == 4
    assert DrawVerticalLineAction(2).execute().params["shift"] == 2


def test_log_to_file(tmp_path: Path) -> None:
    """Verify log to file writes cleanly when base directory is provided."""
    rec = log_to_file("trade.log", "Entry Long at 1.1000", base_dir=tmp_path)
    assert rec.action_type == "log_to_file"
    assert rec.params["filename"] == "trade.log"
    assert rec.params["message"] == "Entry Long at 1.1000"

    log_path = tmp_path / "trade.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "Entry Long at 1.1000\n" in content

    # Without base_dir (in-memory descriptor only)
    rec2 = log_to_file("dummy.log", "Memory log")
    assert rec2.params["path"] is None

    action = LogToFileAction("another.log", "direct call")
    assert action.execute().params["filename"] == "another.log"


def test_log_to_journal() -> None:
    """Verify journal logging action."""
    rec = log_to_journal("Strategy initialized")
    assert rec.action_type == "log_to_journal"
    assert rec.params["message"] == "Strategy initialized"

    action = LogToJournalAction("Direct journal")
    assert action.execute().params["message"] == "Direct journal"


def test_send_email() -> None:
    """Verify email action with and without dispatcher."""
    rec = send_email("Stop Hit", "SL triggered at 1.0950")
    assert rec.action_type == "send_email"
    assert rec.params["email_subject"] == "Stop Hit"
    assert rec.params["delivered"] is False

    # With dispatcher callback
    dispatched: list[tuple[str, str]] = []

    def mock_dispatcher(subj: str, body: str) -> bool:
        dispatched.append((subj, body))
        return True

    rec2 = send_email("TP Hit", "Target reached", dispatcher=mock_dispatcher)
    assert rec2.params["delivered"] is True
    assert dispatched == [("TP Hit", "Target reached")]

    action = SendEmailAction("Direct", "Msg")
    assert action.execute().params["email_subject"] == "Direct"


def test_actions_facade(tmp_path: Path) -> None:
    """Verify centralized Actions facade methods."""
    var = Variable[int]("count", "int", 1)
    rec_assign = Actions.assign(var, 2)
    assert var.value == 2
    assert rec_assign.action_type == "assign_variable"

    rec_custom = Actions.custom("DoCustom()")
    assert rec_custom.action_type == "custom_action"

    assert Actions.draw_down_arrow(1).action_type == "draw_down_arrow"
    assert Actions.draw_up_arrow(2).action_type == "draw_up_arrow"
    assert Actions.draw_vertical_line(3).action_type == "draw_vertical_line"

    rec_file = Actions.log_file("facade.log", "Facade message", base_dir=tmp_path)
    assert rec_file.action_type == "log_to_file"

    rec_journal = Actions.log_journal("Facade journal")
    assert rec_journal.action_type == "log_to_journal"

    rec_email = Actions.send_email("Facade Subj", "Facade Body")
    assert rec_email.action_type == "send_email"
