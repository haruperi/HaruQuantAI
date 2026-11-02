"""Natural logarithm mathematical expression strategy block.

Description:
    Calculates natural logarithm ln(x) for positive numerical operand at specified
    shift with non-silent requirement logging and NaN safety for non-positive inputs.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Logarithm evaluation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.logarithm import logarithm
    res = logarithm(2.7182818)
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

logarithm_spec = BlockSpec(
    id="function.logarithm",
    version="1.0.0",
    name="Logarithm",
    description="Calculates natural logarithm ln(val) for numerical operand",
    category="functions",
    tags=("math", "logarithm", "log", "ln"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("val", PortType.ANY, "Numerical operand (> 0) (scalar/series)"),),
    outputs=(OutputPort("value", PortType.NUMBER, "ln(val)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(logarithm_spec)
def logarithm(val: Any, shift: int = 0) -> float:
    """Calculate natural logarithm ln(x).

    Args:
        val: Numeric operand (> 0).
        shift: Historical bar offset.

    Returns:
        ln(val) as float, or NaN if val <= 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v <= 0.0:
        return _log_func_eval(
            "logarithm",
            float("nan"),
            category="MATH",
            detail=f"non-positive or NaN input: {v}",
        )
    res = math.log(v)
    return _log_func_eval("logarithm", res, category="MATH", detail=f"v={v}")


__all__ = ["logarithm", "logarithm_spec"]
