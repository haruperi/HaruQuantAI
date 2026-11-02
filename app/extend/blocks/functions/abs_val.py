"""Absolute value mathematical expression strategy block.

Description:
    Calculates absolute value of numerical operand at specified shift
    with non-silent requirement logging.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Absolute value calculation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.abs_val import abs_val
    res = abs_val(-42.5)
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

abs_val_spec = BlockSpec(
    id="function.abs_val",
    version="1.0.0",
    name="Absolute Value",
    description="Calculates absolute value of numerical operand at specified shift",
    category="functions",
    tags=("math", "arithmetic", "abs", "absolute"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val", PortType.ANY, "Numerical operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Absolute value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(abs_val_spec)
def abs_val(val: Any, shift: int = 0) -> float:
    """Calculate absolute value for numeric operand.

    Args:
        val: Numeric operand.
        shift: Historical bar offset.

    Returns:
        Absolute float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return _log_func_eval("abs_val", float("nan"), category="MATH")
    res = abs(v)
    return _log_func_eval("abs_val", res, category="MATH")


__all__ = ["abs_val", "abs_val_spec"]
