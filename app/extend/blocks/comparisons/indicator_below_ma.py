"""Indicator Below Moving Average comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    calculate_ma,
    resolve_shift_value,
    round_value,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.enums import MAType

indicator_below_ma_spec = BlockSpec(
    id="condition.indicator_below_ma",
    version="1.0.0",
    name="Indicator Below MA",
    description="Evaluates whether indicator is below its Moving Average at shift",
    category="comparisons",
    tags=("condition", "moving_average", "indicator_below_ma"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Base indicator series"),
        InputPort("period", PortType.NUMBER, "Moving average period"),
        InputPort("ma_type", PortType.NUMBER, "MA Type (1=SMA, 2=EMA, 3=WMA, 4=HULL)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if indicator < MA"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_below_ma_spec)
def indicator_below_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is below its Moving Average at shift."""
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    return not (math.isnan(ind_val) or math.isnan(ma_val)) and ind_val < ma_val


__all__ = ["indicator_below_ma", "indicator_below_ma_spec"]
