"""Division mathematical expression strategy block.

Description:
    Evaluates arithmetic division of two operands (scalar, series, or callable)
    at a historical bar shift with non-silent requirement logging and StrategyQuant
    parity handling for division by zero returning FLOAT_MAX_VALUE.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-arithmetic: Arithmetic division evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.division import division
    res = division(10.0, 2.0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.functions._common import (
    FLOAT_MAX_VALUE,
    _log_func_eval,
    resolve_shift_value,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

division_spec = BlockSpec(
    id="function.division",
    version="1.0.0",
    name="Division",
    description="Divides left operand by right at specified historical shift",
    category="functions",
    tags=("math", "arithmetic", "division", "divide"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Dividend operand (scalar, series, callable)"),
        InputPort("right", PortType.ANY, "Divisor operand (scalar, series, callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Quotient"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(division_spec)
def division(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate division of two operands.

    When the divisor is 0, returns safe FLOAT_MAX_VALUE (Double.MAX_VALUE parity).

    Args:
        left: Dividend operand.
        right: Divisor operand.
        shift: Historical bar offset.

    Returns:
        Quotient as float, FLOAT_MAX_VALUE on division by zero, or NaN on invalid input.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return _log_func_eval("division", float("nan"), category="ARITHMETIC")
    res = v1 / v2 if v2 != 0.0 else FLOAT_MAX_VALUE
    return _log_func_eval(
        "division",
        res,
        category="ARITHMETIC",
        detail=f"v1={v1}, v2={v2}",
    )


__all__ = ["division", "division_spec"]
