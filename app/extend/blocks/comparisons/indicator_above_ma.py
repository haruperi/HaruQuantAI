"""Indicator Above Moving Average comparative condition strategy block.

Description:
    Evaluates whether indicator is above its Moving Average at shift,
    matching StrategyQuant IndicatorAboveMA snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IndicatorAboveMA block.
Key Capabilities:
    - FR-comparison-ma: Compare indicator against its moving average.
Python API Usage:
    from app.extend.blocks.comparisons.indicator_above_ma import (
        indicator_above_ma,
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

indicator_above_ma_spec = BlockSpec(
    id="condition.indicator_above_ma",
    version="1.0.0",
    name="Indicator Above MA",
    description="Evaluates whether indicator is above its Moving Average at shift",
    category="comparisons",
    tags=("condition", "moving_average", "indicator_above_ma"),
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
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if indicator > MA"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_above_ma_spec)
def indicator_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is above its Moving Average at shift."""
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    if math.isnan(ind_val) or math.isnan(ma_val):
        return _log_comparison("indicator_above_ma", False)
    res = ind_val > ma_val
    return _log_comparison("indicator_above_ma", res)


__all__ = ["indicator_above_ma", "indicator_above_ma_spec"]
