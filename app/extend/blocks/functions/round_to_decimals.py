"""Round to decimals mathematical expression strategy block.

Description:
    Rounds numerical operand to specified decimal places at historical shift
    with non-silent requirement logging and StrategyQuant donor parameter defaults.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-math: Value rounding to decimal precision.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.round_to_decimals import round_to_decimals
    res = round_to_decimals(1.234567, decimals=4)
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

round_to_decimals_spec = BlockSpec(
    id="function.round_to_decimals",
    version="1.0.0",
    name="Round to Decimals",
    description="Rounds numerical operand to specified decimal places",
    category="functions",
    tags=("math", "round", "precision"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val", PortType.ANY, "Value to round (scalar, series, or callable)"),
        InputPort("decimals", PortType.NUMBER, "Decimal places", default=5),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Rounded value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(round_to_decimals_spec)
def round_to_decimals(val: Any, decimals: int = 5, shift: int = 0) -> float:
    """Round operand to specified decimal places.

    Args:
        val: Numeric operand.
        decimals: Number of decimal places (default 5).
        shift: Historical bar offset.

    Returns:
        Rounded float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return _log_func_eval("round_to_decimals", float("nan"), category="MATH")
    res = round(v, decimals)
    return _log_func_eval(
        "round_to_decimals",
        res,
        category="MATH",
        detail=f"v={v}, dec={decimals}",
    )


# StrategyQuant alias
round_val = round_to_decimals
round_spec = round_to_decimals_spec

__all__ = ["round_spec", "round_to_decimals", "round_to_decimals_spec", "round_val"]
