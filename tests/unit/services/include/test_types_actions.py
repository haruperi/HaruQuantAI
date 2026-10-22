"""Unit tests for primitive type/variable blocks and rule action blocks.

Description:
    Validates all 5 SQ.Blocks.Other type/variable blocks in
    app.services.include.types (BooleanConstant, BooleanVariable,
    DoubleVariable, IntVariable, NumberConstant, Variable, standalone
    evaluators, and Types facade) and all 8 SQ.Blocks.OtherActions blocks in
    app.services.include.actions (AssignVariableAction, CustomAction,
    DrawDownArrowAction, DrawUpArrowAction, DrawVerticalLineAction,
    LogToFileAction, LogToJournalAction, SendEmailAction, standalone helpers,
    and Actions facade).

Purpose:
    FEAT-SERVICES-TYPES: Verification of primitive type and variable blocks.
    FEAT-SERVICES-ACTIONS: Verification of trading rule and annotation action blocks.

Key Capabilities:
    - FR-TEST-TYPES-BLOCKS: Verify Variable state container, constant/variable
      block classes, standalone functions, and Types facade.
    - FR-TEST-ACTIONS-BLOCKS: Verify variable assignment coercion, custom
      actions, chart annotations, file/journal logging, email notifications,
      and Actions facade.

Python API Usage:
    ```python
    from app.services.include.actions import Actions
    from app.services.include.types import Types

    v = Types.create_variable("flag", "bool", False)
    Actions.assign(v, 1.0, is_boolean=True)
    assert v.value is True
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_types_actions.py --no-cov
    ```
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.include.actions import (
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
from app.services.include.types import (
    BooleanConstant,
    BooleanVariable,
    DoubleVariable,
    IntVariable,
    NumberConstant,
    Types,
    Variable,
    boolean_constant,
    boolean_variable,
    double_variable,
    int_variable,
    number_constant,
)


def test_variable_and_type_blocks() -> None:
    """Verify Variable state container, type block classes, functions, and Types facade."""
    var_b = Variable[bool]("is_ready", "bool", False)
    assert var_b.get_value() is False
    assert var_b.value is False
    var_b.value = True
    assert var_b.get_value() is True
    assert "Variable(name='is_ready'" in repr(var_b)

    # Classes
    assert BooleanConstant().evaluate() == pytest.approx(0.0)
    assert BooleanConstant(True).evaluate(shift=1) == pytest.approx(1.0)
    assert BooleanVariable(var_b).evaluate() == pytest.approx(1.0)
    assert BooleanVariable(False).evaluate() == pytest.approx(0.0)

    var_d = Types.create_variable("level", "double", 1.2345)
    assert DoubleVariable(var_d).evaluate() == pytest.approx(1.2345)
    assert DoubleVariable(2.5).evaluate() == pytest.approx(2.5)

    var_i = Types.create_variable("count", "int", 7)
    assert IntVariable(var_i).evaluate() == pytest.approx(7.0)
    assert IntVariable(3).evaluate() == pytest.approx(3.0)

    assert NumberConstant().evaluate() == pytest.approx(0.0)
    assert NumberConstant(42.5).evaluate() == pytest.approx(42.5)

    # Standalone functions and defaults
    assert boolean_constant() == pytest.approx(0.0)
    assert boolean_constant(True) == pytest.approx(1.0)
    assert boolean_variable(var_b) == pytest.approx(1.0)
    assert boolean_variable(False) == pytest.approx(0.0)
    assert double_variable(var_d) == pytest.approx(1.2345)
    assert int_variable(var_i) == pytest.approx(7.0)
    assert number_constant() == pytest.approx(0.0)
    assert number_constant(99.0) == pytest.approx(99.0)

    # Facade
    assert Types.boolean() == pytest.approx(0.0)
    assert Types.boolean(True) == pytest.approx(1.0)
    assert Types.boolean_var(var_b) == pytest.approx(1.0)
    assert Types.double_var(var_d) == pytest.approx(1.2345)
    assert Types.int_var(var_i) == pytest.approx(7.0)
    assert Types.number() == pytest.approx(0.0)
    assert Types.number(12.5) == pytest.approx(12.5)


def test_action_blocks_and_facade(tmp_path: Path) -> None:
    """Verify all 8 OtherActions blocks, standalone helpers, and Actions facade."""
    v_bool = Variable[bool]("flag", "bool", True)

    # AssignVariable with numeric ORDER_NOT_DEFINED (-99999999.0) and 0.0 -> False
    assert ORDER_NOT_DEFINED == pytest.approx(-99_999_999.0)
    rec1 = AssignVariableAction(v_bool, ORDER_NOT_DEFINED, is_boolean=True).execute()
    assert bool(v_bool.value) is False
    assert rec1.action_type == "assign_variable"

    AssignVariableAction(v_bool, 0.0, is_boolean=True).execute()
    assert bool(v_bool.value) is False

    # Strictly verify NO BACKWARD COMPATIBILITY / shim: -1.0 must evaluate to True
    AssignVariableAction(v_bool, -1.0, is_boolean=True).execute()
    assert bool(v_bool.value) is True

    # AssignVariable with evaluate()-bearing block object -> True
    AssignVariableAction(v_bool, NumberConstant(5.0), is_boolean=True).execute()
    assert bool(v_bool.value) is True

    # AssignVariable with callable returning non-numeric truthy object
    AssignVariableAction(v_bool, lambda: "non_empty", is_boolean=True).execute()
    assert bool(v_bool.value) is True

    # AssignVariable non-boolean
    v_num = Variable[float]("target", "float", 0.0)
    Actions.assign(v_num, 105.5, is_boolean=False)
    assert v_num.value == pytest.approx(105.5)

    # CustomAction with and without handler
    rec_c1 = custom_action()
    assert rec_c1.params == {"command": "", "result": None}
    rec_c2 = Actions.custom("Alert('hi')", handler=lambda cmd: f"ran:{cmd}")
    assert rec_c2.params["result"] == "ran:Alert('hi')"
    assert CustomAction("noop").execute().params["result"] is None

    # Draw arrows and vertical line
    assert DrawDownArrowAction(1).execute().params == {"shift": 1}
    assert DrawUpArrowAction(2).execute().params == {"shift": 2}
    assert DrawVerticalLineAction(3).execute().params == {"shift": 3}
    assert Actions.draw_down_arrow(4).params == {"shift": 4}
    assert Actions.draw_up_arrow(5).params == {"shift": 5}
    assert Actions.draw_vertical_line(6).params == {"shift": 6}
    assert draw_down_arrow().params == {"shift": 0}
    assert draw_up_arrow().params == {"shift": 0}
    assert draw_vertical_line().params == {"shift": 0}

    # LogToFile without base_dir and with sandboxed tmp_path base_dir
    rec_f0 = log_to_file("test.log", "line1")
    assert rec_f0.params["path"] is None
    rec_f1 = Actions.log_file("audit.log", "hello world", base_dir=tmp_path)
    log_path = tmp_path / "audit.log"
    assert rec_f1.params["path"] == str(log_path)
    assert log_path.read_text(encoding="utf-8") == "hello world\n"
    assert LogToFileAction().execute().params["path"] is None

    # LogToJournal
    assert LogToJournalAction("j1").execute().params == {"message": "j1"}
    assert log_to_journal("j2").params == {"message": "j2"}
    assert Actions.log_journal("j3").params == {"message": "j3"}

    # SendEmail without and with dispatcher
    rec_e0 = SendEmailAction("Subj", "Body").execute()
    assert rec_e0.params["delivered"] is False
    rec_e1 = send_email("Subj", "Body", dispatcher=lambda s, m: bool(s and m))
    assert rec_e1.params["delivered"] is True
    rec_e2 = Actions.send_email("Alert", "Filled", dispatcher=lambda s, m: True)
    assert rec_e2.params["delivered"] is True

    # Direct assign_variable helper
    assign_variable(v_num, 200.0)
    assert v_num.value == pytest.approx(200.0)
