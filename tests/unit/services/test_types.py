"""Unit tests for StrategyQuant X Types and Variables building blocks.

Tests:
    - Variable container operations, getters, setters, repr.
    - BooleanConstant evaluations with True, False, and default values.
    - BooleanVariable evaluations with Variable container and raw boolean values.
    - DoubleVariable evaluations with Variable container and raw float values.
    - IntVariable evaluations with Variable container and raw int values.
    - NumberConstant evaluations with zero, positive, negative, and default values.
    - Functional primitives: boolean_constant, boolean_variable, double_variable, int_variable, number_constant.
    - Centralized Types facade methods.
"""

from __future__ import annotations

import pytest
from app.services.utils.types import (
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


def test_variable_container() -> None:
    """Verify Variable container state, mutation, property, and repr."""
    v = Variable[float](name="stop_loss", var_type="float", initial_value=1.1200)
    assert v.name == "stop_loss"
    assert v.var_type == "float"
    assert v.get_value() == 1.1200
    assert v.value == 1.1200

    v.set_value(1.1250)
    assert v.get_value() == 1.1250
    assert v.value == 1.1250

    v.value = 1.1300
    assert v.value == 1.1300
    assert "Variable" in repr(v)
    assert "stop_loss" in repr(v)


def test_boolean_constant() -> None:
    """Verify BooleanConstant evaluation to 1.0 or 0.0."""
    b_default = BooleanConstant()
    assert b_default.evaluate() == 0.0

    b_true = BooleanConstant(True)
    assert b_true.evaluate() == 1.0
    assert b_true.evaluate(shift=5) == 1.0

    b_false = BooleanConstant(False)
    assert b_false.evaluate() == 0.0


def test_boolean_variable() -> None:
    """Verify BooleanVariable evaluation with container and raw values."""
    var = Variable[bool](name="in_trade", var_type="bool", initial_value=True)
    b_var = BooleanVariable(var)
    assert b_var.evaluate() == 1.0

    var.set_value(False)
    assert b_var.evaluate() == 0.0

    # Raw boolean value
    assert BooleanVariable(True).evaluate() == 1.0
    assert BooleanVariable(False).evaluate() == 0.0


def test_double_variable() -> None:
    """Verify DoubleVariable evaluation with container and raw values."""
    var = Variable[float](name="entry_price", var_type="float", initial_value=1.2345)
    d_var = DoubleVariable(var)
    assert d_var.evaluate() == pytest.approx(1.2345)

    var.set_value(1.2355)
    assert d_var.evaluate(shift=2) == pytest.approx(1.2355)

    # Raw float value
    assert DoubleVariable(42.5).evaluate() == pytest.approx(42.5)


def test_int_variable() -> None:
    """Verify IntVariable evaluation with container and raw values."""
    var = Variable[int](name="bars_count", var_type="int", initial_value=10)
    i_var = IntVariable(var)
    assert i_var.evaluate() == 10.0
    assert isinstance(i_var.evaluate(), float)

    var.set_value(25)
    assert i_var.evaluate(shift=1) == 25.0

    # Raw int value
    assert IntVariable(7).evaluate() == 7.0


def test_number_constant() -> None:
    """Verify NumberConstant evaluation."""
    n_default = NumberConstant()
    assert n_default.evaluate() == 0.0

    n_custom = NumberConstant(123.456)
    assert n_custom.evaluate() == pytest.approx(123.456)
    assert n_custom.evaluate(shift=3) == pytest.approx(123.456)

    n_negative = NumberConstant(-99.5)
    assert n_negative.evaluate() == pytest.approx(-99.5)


def test_functional_primitives() -> None:
    """Verify standalone functional primitive evaluators."""
    assert boolean_constant(True) == 1.0
    assert boolean_constant(False) == 0.0

    b_var = Variable[bool]("flag", "bool", True)
    assert boolean_variable(b_var) == 1.0
    assert boolean_variable(False) == 0.0

    d_var = Variable[float]("d", "float", 9.81)
    assert double_variable(d_var) == pytest.approx(9.81)
    assert double_variable(3.1415) == pytest.approx(3.1415)

    i_var = Variable[int]("count", "int", 4)
    assert int_variable(i_var) == 4.0
    assert int_variable(12) == 12.0

    assert number_constant(100.0) == 100.0
    assert number_constant(-50.0) == -50.0


def test_types_facade() -> None:
    """Verify Types facade static methods."""
    assert Types.boolean(True) == 1.0
    assert Types.boolean(False) == 0.0

    v_bool = Types.create_variable("active", "bool", True)
    assert Types.boolean_var(v_bool) == 1.0

    v_double = Types.create_variable("price", "double", 1.0550)
    assert Types.double_var(v_double) == pytest.approx(1.0550)

    v_int = Types.create_variable("period", "int", 14)
    assert Types.int_var(v_int) == 14.0

    assert Types.number(88.8) == pytest.approx(88.8)
