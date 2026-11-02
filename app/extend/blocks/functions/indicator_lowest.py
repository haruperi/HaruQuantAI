"""Indicator lowest ranking expression strategy block.

Description:
    Extracts Nth lowest indicator value in a rolling historical window
    with non-silent requirement logging and StrategyQuant donor parameter defaults.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-rank: Rolling window lowest value ranking.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.indicator_lowest import indicator_lowest
    val = indicator_lowest(series, period=5, nth_value=0)
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
from app.extend.blocks.functions._common import (
    MIN_RANK_PERIOD,
    _log_func_eval,
    resolve_shift_value,
)

indicator_lowest_spec = BlockSpec(
    id="function.indicator_lowest",
    version="1.0.0",
    name="Indicator Lowest",
    description="Extracts Nth lowest indicator value in a rolling window",
    category="functions",
    tags=("ranking", "rolling", "lowest", "indicator"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.ANY, "Indicator series or callable"),
        InputPort("period", PortType.NUMBER, "Lookback period (minimum 2)", default=5),
        InputPort("nth_value", PortType.NUMBER, "0-indexed rank (0=lowest)", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Nth lowest value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_lowest_spec)
def indicator_lowest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth lowest indicator value in a rolling window.

    NthValue=0 means lowest, 1 means second lowest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth lowest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        return _log_func_eval(
            "indicator_lowest",
            -1.0,
            category="RANK",
            detail=f"invalid period={period}, nth={nth_value}",
        )

    vals: list[float] = []
    for i in range(period):
        v = resolve_shift_value(indicator, shift + i)
        if math.isnan(v):
            return _log_func_eval(
                "indicator_lowest",
                -1.0,
                category="RANK",
                detail=f"NaN encountered at relative bar {i}",
            )
        vals.append(v)

    vals.sort()
    res = vals[nth_value]
    return _log_func_eval(
        "indicator_lowest",
        res,
        category="RANK",
        detail=f"period={period}, nth={nth_value}, shift={shift}",
    )


__all__ = ["indicator_lowest", "indicator_lowest_spec"]
