"""Minus (subtraction) mathematical expression strategy block.

Description:
    Evaluates arithmetic subtraction of two operands (scalar, series, or callable)
    at a historical bar shift with non-silent requirement logging.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-arithmetic: Arithmetic subtraction evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.minus import minus
    res = minus(10.0, 3.0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.functions._common import _log_func_eval, resolve_shift_value
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

minus_spec = BlockSpec(
    id="function.minus",
    version="1.0.0",
    name="Minus (Subtraction)",
    description="Subtracts right operand from left at specified historical shift",
    category="functions",
    tags=("math", "arithmetic", "minus", "subtraction"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "left", PortType.ANY, "Minuend operand (scalar, series, or callable)"
        ),
        InputPort(
            "right", PortType.ANY, "Subtrahend operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Difference"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(minus_spec)
def minus(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate subtraction of two operands at historical bar shift.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.

    Returns:
        Difference as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return _log_func_eval("minus", float("nan"), category="ARITHMETIC")
    res = v1 - v2
    return _log_func_eval("minus", res, category="ARITHMETIC")


__all__ = ["minus", "minus_spec"]
