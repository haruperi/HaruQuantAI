"""Indicator highest ranking expression strategy block.

Description:
    Extracts Nth highest indicator value in a rolling historical window
    with non-silent requirement logging and StrategyQuant donor parameter defaults.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-rank: Rolling window highest value ranking.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.indicator_highest import indicator_highest
    val = indicator_highest(series, period=5, nth_value=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.functions._common import (
    MIN_RANK_PERIOD,
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

indicator_highest_spec = BlockSpec(
    id="function.indicator_highest",
    version="1.0.0",
    name="Indicator Highest",
    description="Extracts Nth highest indicator value in a rolling window",
    category="functions",
    tags=("ranking", "rolling", "highest", "indicator"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.ANY, "Indicator series or callable"),
        InputPort("period", PortType.NUMBER, "Lookback period (minimum 2)", default=5),
        InputPort(
            "nth_value", PortType.NUMBER, "0-indexed rank (0=highest)", default=0
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Nth highest value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_highest_spec)
def indicator_highest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth highest indicator value in a rolling window.

    NthValue=0 means highest, 1 means second highest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth highest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        return _log_func_eval(
            "indicator_highest",
            -1.0,
            category="RANK",
            detail=f"invalid period={period}, nth={nth_value}",
        )

    vals: list[float] = []
    for i in range(period):
        v = resolve_shift_value(indicator, shift + i)
        if math.isnan(v):
            return _log_func_eval(
                "indicator_highest",
                -1.0,
                category="RANK",
                detail=f"NaN encountered at relative bar {i}",
            )
        vals.append(v)

    vals.sort(reverse=True)
    res = vals[nth_value]
    return _log_func_eval(
        "indicator_highest",
        res,
        category="RANK",
        detail=f"period={period}, nth={nth_value}, shift={shift}",
    )


__all__ = ["indicator_highest", "indicator_highest_spec"]
