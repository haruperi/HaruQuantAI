"""Square root mathematical expression strategy block.

Description:
    Calculates square root for non-negative numerical operand at specified shift
    with non-silent requirement logging and NaN safety for negative inputs.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Square root evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.square_root import square_root
    res = square_root(16.0)
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

square_root_spec = BlockSpec(
    id="function.square_root",
    version="1.0.0",
    name="Square Root",
    description="Calculates square root of non-negative numerical operand",
    category="functions",
    tags=("math", "square_root", "sqrt"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val", PortType.ANY, "Numerical operand (>= 0) (scalar/series)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "sqrt(val)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(square_root_spec)
def square_root(val: Any, shift: int = 0) -> float:
    """Calculate square root of numeric operand.

    Args:
        val: Numeric operand (>= 0).
        shift: Historical bar offset.

    Returns:
        sqrt(val) as float, or NaN if val < 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v < 0.0:
        return _log_func_eval(
            "square_root",
            float("nan"),
            category="MATH",
            detail=f"negative or NaN input: {v}",
        )
    res = math.sqrt(v)
    return _log_func_eval("square_root", res, category="MATH", detail=f"v={v}")


__all__ = ["square_root", "square_root_spec"]
