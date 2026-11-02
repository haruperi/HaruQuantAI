"""Exponential mathematical expression strategy block.

Description:
    Calculates natural exponential (e^x) for a numerical operand at specified
    shift with non-silent logging and overflow protection returning FLOAT_MAX_VALUE.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Exponential evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.exponential import exponential
    res = exponential(1.0)
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

exponential_spec = BlockSpec(
    id="function.exponential",
    version="1.0.0",
    name="Exponential",
    description="Calculates e^val for numerical operand at specified shift",
    category="functions",
    tags=("math", "exponential", "exp"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val", PortType.ANY, "Exponent operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "e^val"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(exponential_spec)
def exponential(val: Any, shift: int = 0) -> float:
    """Calculate natural exponential (e^x).

    Args:
        val: Numeric exponent.
        shift: Historical bar offset.

    Returns:
        e^val as float, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return _log_func_eval("exponential", float("nan"), category="MATH")
    try:
        res = math.exp(v)
    except OverflowError:
        res = FLOAT_MAX_VALUE
    return _log_func_eval(
        "exponential",
        res,
        category="MATH",
        detail=f"v={v}",
    )


__all__ = ["exponential", "exponential_spec"]
