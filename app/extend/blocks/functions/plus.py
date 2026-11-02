"""Addition (plus) mathematical expression strategy block.

Description:
    Evaluates arithmetic addition of two operands (scalar, series, or callable)
    at a historical bar shift with non-silent requirement logging.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-arithmetic: Arithmetic addition evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.plus import plus
    res = plus(10.0, 5.0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.functions._common import _log_func_eval, resolve_shift_value

plus_spec = BlockSpec(
    id="function.plus",
    version="1.0.0",
    name="Plus (Addition)",
    description="Adds two numerical values or series at the specified bar shift",
    category="functions",
    tags=("math", "arithmetic", "plus", "addition"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "First operand (scalar, array, or series)"),
        InputPort("right", PortType.ANY, "Second operand (scalar, array, or series)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Sum of operands"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(plus_spec)
def plus(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate addition of two operands at historical bar shift.

    Args:
        left: Left operand (scalar, series, array, or callable).
        right: Right operand (scalar, series, array, or callable).
        shift: Historical bar offset (default 0).

    Returns:
        Sum as float, or NaN if either operand is invalid or unresolvable.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return _log_func_eval("plus", float("nan"), category="ARITHMETIC")
    res = v1 + v2
    return _log_func_eval("plus", res, category="ARITHMETIC")


__all__ = ["plus", "plus_spec"]
