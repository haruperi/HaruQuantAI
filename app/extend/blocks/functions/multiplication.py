"""Multiplication mathematical expression strategy block.

Description:
    Evaluates arithmetic multiplication of two operands (scalar, series, or callable)
    at a historical bar shift with non-silent requirement logging.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-arithmetic: Arithmetic multiplication evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.multiplication import multiplication
    res = multiplication(4.0, 2.5)
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

multiplication_spec = BlockSpec(
    id="function.multiplication",
    version="1.0.0",
    name="Multiplication",
    description="Multiplies two numerical operands at specified historical shift",
    category="functions",
    tags=("math", "arithmetic", "multiplication", "multiply"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "First factor (scalar, series, or callable)"),
        InputPort("right", PortType.ANY, "Second factor (scalar, series, or callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Product"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(multiplication_spec)
def multiplication(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate multiplication of two operands at historical bar shift.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.

    Returns:
        Product as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return _log_func_eval("multiplication", float("nan"), category="ARITHMETIC")
    res = v1 * v2
    return _log_func_eval("multiplication", res, category="ARITHMETIC")


__all__ = ["multiplication", "multiplication_spec"]
