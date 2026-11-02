"""Minimum mathematical expression strategy block.

Description:
    Calculates minimum of two numerical operands at specified historical shift
    with non-silent requirement logging.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Minimum value evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.minimum import minimum
    res = minimum(5.0, 10.0)
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

minimum_spec = BlockSpec(
    id="function.minimum",
    version="1.0.0",
    name="Minimum",
    description="Calculates minimum of two numerical operands at specified shift",
    category="functions",
    tags=("math", "extrema", "minimum", "min"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val1", PortType.ANY, "First operand (scalar, series, or callable)"),
        InputPort("val2", PortType.ANY, "Second operand (scalar, series, or callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Minimum value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(minimum_spec)
def minimum(val1: Any, val2: Any, shift: int = 0) -> float:
    """Calculate minimum of two operands.

    Args:
        val1: First operand.
        val2: Second operand.
        shift: Historical bar offset.

    Returns:
        Smaller value as float, or NaN.
    """
    v1 = resolve_shift_value(val1, shift)
    v2 = resolve_shift_value(val2, shift)
    if math.isnan(v1) or math.isnan(v2):
        return _log_func_eval("minimum", float("nan"), category="MATH")
    res = min(v1, v2)
    return _log_func_eval("minimum", res, category="MATH", detail=f"v1={v1}, v2={v2}")


__all__ = ["minimum", "minimum_spec"]
