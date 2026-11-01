"""Unit tests for foundational types and variable blocks."""

from __future__ import annotations

from app.extend.blocks.metadata import PortType
from app.extend.blocks.registry import BlockRegistry
from app.extend.blocks.types import (
    BooleanConstant,
    BooleanVariable,
    DoubleVariable,
    IntVariable,
    NumberConstant,
    Types,
    Variable,
    boolean,
    boolean_constant,
    boolean_spec,
    boolean_variable,
    boolean_variable_spec,
    double_variable,
    double_variable_spec,
    int_variable,
    int_variable_spec,
    number,
    number_constant,
    number_spec,
)


def test_boolean_constant_block_and_class() -> None:
    """Verify boolean block and BooleanConstant class evaluation."""
    assert boolean() == 0.0
    assert boolean(value=False) == 0.0
    assert boolean(value=True) == 1.0
    assert boolean_constant(True) == 1.0
    assert boolean_constant(False) == 0.0

    bc_false = BooleanConstant(False)
    bc_true = BooleanConstant(True)
    assert bc_false.evaluate() == 0.0
    assert bc_true.evaluate() == 1.0
    assert bc_true.evaluate(shift=5) == 1.0

    assert boolean_spec.id == "types.boolean"
    assert boolean_spec.category == "types"
    assert boolean_spec.outputs[0].port_type == PortType.BOOLEAN


def test_number_constant_block_and_class() -> None:
    """Verify number block and NumberConstant class evaluation."""
    assert number() == 0.0
    assert number(123.456) == 123.456
    assert number(-99.0, shift=2) == -99.0
    assert number_constant(42.0) == 42.0

    nc = NumberConstant(789.25)
    assert nc.evaluate() == 789.25
    assert nc.evaluate(shift=1) == 789.25

    assert number_spec.id == "types.number"
    assert number_spec.category == "types"
    assert number_spec.outputs[0].port_type == PortType.NUMBER


def test_variable_container() -> None:
    """Verify Variable container state, property getter/setter, equality, repr."""
    v = Variable("my_int", "int", 10)
    assert v.name == "my_int"
    assert v.var_type == "int"
    assert v.get_value() == 10
    assert v.value == 10

    v.set_value(25)
    assert v.get_value() == 25
    assert v.value == 25

    v.value = 50
    assert v.value == 50

    v2 = Variable("my_int", "int", 50)
    assert v == v2
    assert v == 50
    assert "Variable(name='my_int'" in repr(v)


def test_boolean_variable_block_and_class() -> None:
    """Verify boolean_variable block and BooleanVariable class."""
    var_true = Variable("flag", "bool", True)
    var_false = Variable("flag", "bool", False)

    assert boolean_variable(var_true) == 1.0
    assert boolean_variable(var_false) == 0.0
    assert boolean_variable(True) == 1.0
    assert boolean_variable(False) == 0.0

    bv_true = BooleanVariable(var_true)
    bv_false = BooleanVariable(var_false)
    assert bv_true.evaluate() == 1.0
    assert bv_false.evaluate() == 0.0

    assert boolean_variable_spec.id == "types.boolean_variable"
    assert boolean_variable_spec.category == "types"
    assert boolean_variable_spec.outputs[0].port_type == PortType.BOOLEAN


def test_double_variable_block_and_class() -> None:
    """Verify double_variable block and DoubleVariable class."""
    var_float = Variable("target", "double", 1.2345)

    assert double_variable(var_float) == 1.2345
    assert double_variable(9.8765) == 9.8765

    dv = DoubleVariable(var_float)
    assert dv.evaluate() == 1.2345

    assert double_variable_spec.id == "types.double_variable"
    assert double_variable_spec.category == "types"
    assert double_variable_spec.outputs[0].port_type == PortType.NUMBER


def test_int_variable_block_and_class() -> None:
    """Verify int_variable block and IntVariable class."""
    var_int = Variable("count", "int", 42)

    assert int_variable(var_int) == 42.0
    assert int_variable(100) == 100.0

    iv = IntVariable(var_int)
    assert iv.evaluate() == 42.0

    assert int_variable_spec.id == "types.int_variable"
    assert int_variable_spec.category == "types"
    assert int_variable_spec.outputs[0].port_type == PortType.NUMBER


def test_types_facade() -> None:
    """Verify Types facade helpers and factory."""
    assert Types.boolean(True) == 1.0
    assert Types.boolean(False) == 0.0
    assert Types.number(3.14159) == 3.14159

    v_b = Types.create_variable("b_test", "bool", True)
    v_d = Types.create_variable("d_test", "double", 10.5)
    v_i = Types.create_variable("i_test", "int", 7)

    assert Types.boolean_var(v_b) == 1.0
    assert Types.double_var(v_d) == 10.5
    assert Types.int_var(v_i) == 7.0


def test_block_registry_discovers_types_blocks() -> None:
    """Verify BlockRegistry discovers all types blocks with 0 diagnostics."""
    registry = BlockRegistry()
    registry.discover("app/extend/blocks/types")

    expected_ids = {
        "types.boolean",
        "types.number",
        "types.boolean_variable",
        "types.double_variable",
        "types.int_variable",
    }
    discovered_ids = {b.spec.id for b in registry.snapshot().blocks.values()}
    assert expected_ids.issubset(discovered_ids)
    assert not registry.diagnostics


def test_app_include_reexports_types() -> None:
    """Verify app.include re-exports foundational types and classes."""
    import app.include as inc

    assert hasattr(inc, "BooleanConstant")
    assert hasattr(inc, "NumberConstant")
    assert hasattr(inc, "Types")
    assert hasattr(inc, "Variable")
