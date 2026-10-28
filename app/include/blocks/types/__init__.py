"""Foundational primitive type and variable blocks."""

from __future__ import annotations

from app.include.blocks.types.boolean import (
    BooleanConstant,
    boolean,
    boolean_constant,
    boolean_spec,
)
from app.include.blocks.types.boolean_variable import (
    BooleanVariable,
    boolean_variable,
    boolean_variable_spec,
)
from app.include.blocks.types.double_variable import (
    DoubleVariable,
    double_variable,
    double_variable_spec,
)
from app.include.blocks.types.facade import Types
from app.include.blocks.types.int_variable import (
    IntVariable,
    int_variable,
    int_variable_spec,
)
from app.include.blocks.types.number import (
    NumberConstant,
    number,
    number_constant,
    number_spec,
)
from app.include.blocks.types.variable import Variable

__all__ = [
    "BooleanConstant",
    "BooleanVariable",
    "DoubleVariable",
    "IntVariable",
    "NumberConstant",
    "Types",
    "Variable",
    "boolean",
    "boolean_constant",
    "boolean_spec",
    "boolean_variable",
    "boolean_variable_spec",
    "double_variable",
    "double_variable_spec",
    "int_variable",
    "int_variable_spec",
    "number",
    "number_constant",
    "number_spec",
]
