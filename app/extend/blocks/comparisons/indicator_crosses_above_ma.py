"""Indicator Crosses Above MA comparative condition strategy block.

Description:
    Evaluates whether indicator crosses above its MA from shift + 1 to shift,
    matching StrategyQuant IndicatorCrossesAboveMA snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IndicatorCrossesAboveMA.
Key Capabilities:
    - FR-comparison-crossover: Detect indicator crossing above its moving average.
Python API Usage:
    from app.extend.blocks.comparisons.indicator_crosses_above_ma import (
        indicator_crosses_above_ma,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.core.enums import MAType
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    _log_comparison,
    calculate_ma,
    resolve_shift_value,
    round_value,
)

indicator_crosses_above_ma_spec = BlockSpec(
    id="condition.indicator_crosses_above_ma",
    version="1.0.0",
    name="Indicator Crosses Above MA",
    description=(
        "Evaluate whether indicator crosses above its MA from shift + 1 to shift"
    ),
    category="comparisons",
    tags=("condition", "moving_average", "crossover", "crosses_above_ma"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Base indicator series"),
        InputPort("period", PortType.NUMBER, "Moving average period", default=14),
        InputPort(
            "ma_type",
            PortType.NUMBER,
            "MA Type (1=SMA, 2=EMA, 3=WMA, 4=HULL)",
            default=1,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if crossed above MA"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_crosses_above_ma_spec)
def indicator_crosses_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator crosses above its MA from shift + 1 to shift."""
    ind_curr = round_value(resolve_shift_value(indicator, shift), precision)
    ind_prev = round_value(resolve_shift_value(indicator, shift + 1), precision)
    ma_curr = calculate_ma(indicator, period, ma_type, shift, precision)
    ma_prev = calculate_ma(indicator, period, ma_type, shift + 1, precision)
    if any(math.isnan(v) for v in (ind_curr, ind_prev, ma_curr, ma_prev)):
        return _log_comparison("indicator_crosses_above_ma", False)
    res = ind_prev < ma_prev and ind_curr > ma_curr
    return _log_comparison("indicator_crosses_above_ma", res)


__all__ = ["indicator_crosses_above_ma", "indicator_crosses_above_ma_spec"]
