"""Primitive type and variable blocks matching StrategyQuant SQ.Blocks.Other.

Description:
    Exposes canonical constant and variable evaluation building blocks corresponding
    to StrategyQuant SQ.Blocks.Other snippets (Boolean, BooleanVariable, DoubleVariable,
    IntVariable, Number), the generic Variable container, and the unified Types facade.
Purpose:
    FEAT-TYPES-BLOCKS: StrategyQuant donor-faithful primitive type and variable blocks.
Key Capabilities:
    - FR-TYPES-EXPORTS: Canonical primitive type and variable block exports.
Python API Usage:
    from app.extend.blocks.types import Boolean, Number, Types, Variable
    b = Boolean(True)
    n = Number(42.0)
    v = Types.create_variable("flag", "bool", True)
CLI Usage:
    uv run pytest tests/extend/blocks/test_types.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.types.boolean import (
    Boolean,
    BooleanConstant,
    boolean,
    boolean_constant,
    boolean_spec,
)
from app.extend.blocks.types.boolean_variable import (
    BooleanVariable,
    boolean_variable,
    boolean_variable_spec,
)
from app.extend.blocks.types.double_variable import (
    DoubleVariable,
    double_variable,
    double_variable_spec,
)
from app.extend.blocks.types.facade import Types
from app.extend.blocks.types.int_variable import (
    IntVariable,
    int_variable,
    int_variable_spec,
)
from app.extend.blocks.types.number import (
    Number,
    NumberConstant,
    number,
    number_constant,
    number_spec,
)
from app.extend.blocks.types.variable import Variable

__all__ = [
    "Boolean",
    "BooleanConstant",
    "BooleanVariable",
    "DoubleVariable",
    "IntVariable",
    "Number",
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
