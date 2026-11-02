"""Accumulative Swing Index (ASI) trend indicator block.

Description:
    Calculates Welles Wilder's Accumulative Swing Index (ASI) tracking
    cumulative breakout points across Open, High, Low, and Close prices.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-accumulative-swing-index: ASI computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.accumulative_swing_index import (
        AccumulativeSwingIndex,
    )
    res = AccumulativeSwingIndex().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)

_SCALE_50: float = 50.0
_MIN_BARS: int = 2


def _wilder_si(
    curr_ohlc: tuple[float, float, float, float],
    prev_oc: tuple[float, float],
    limit: float,
) -> float:
    open_p, high_p, low_p, close_p = curr_ohlc
    c_prev, o_prev = prev_oc
    k = max(high_p - c_prev, c_prev - low_p)
    diff_hc = abs(high_p - c_prev)
    diff_lc = abs(low_p - c_prev)
    diff_hl = high_p - low_p
    if diff_hc >= diff_lc and diff_hc >= diff_hl:
        r = diff_hc - 0.5 * diff_lc + 0.25 * abs(c_prev - o_prev)
    elif diff_lc >= diff_hc and diff_lc >= diff_hl:
        r = diff_lc - 0.5 * diff_hc + 0.25 * abs(c_prev - o_prev)
    else:
        r = diff_hl + 0.25 * abs(c_prev - o_prev)
    if r == 0.0 or limit == 0.0:
        return 0.0
    num = (close_p - c_prev) + 0.5 * (close_p - open_p) + 0.25 * (c_prev - o_prev)
    return float(_SCALE_50 * (num / r) * (k / limit))


class AccumulativeSwingIndex(BaseIndicator):
    """Accumulative Swing Index (ASI) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.accumulative_swing_index",
        version="1.0.0",
        name="Accumulative Swing Index",
        description="Welles Wilder cumulative swing breakout index",
        category="trend",
        tags=("trend", "asi", "wilder", "swing"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Accumulative Swing Index"),),
        required_market_inputs=("open", "high", "low", "close"),
        parameter_search_space={
            "limit_move": {"type": "float", "min": 0.1, "max": 100.0, "default": 10.0},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    limit_move: float = Field(default=10.0, gt=0.0)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return _MIN_BARS

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Accumulative Swing Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        open_arr = np.asarray(bars.open, dtype=np.float64)
        high_arr = np.asarray(bars.high, dtype=np.float64)
        low_arr = np.asarray(bars.low, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        n = len(close_arr)
        asi = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            cum = 0.0
            for i in range(1, n):
                si = _wilder_si(
                    (open_arr[i], high_arr[i], low_arr[i], close_arr[i]),
                    (close_arr[i - 1], open_arr[i - 1]),
                    self.limit_move,
                )
                cum += si
                asi[i] = cum
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated ASI(limit=%.1f) for %d bars",
            self.limit_move,
            len(bars),
        )
        return {"value": IndicatorSeries(asi, name="ASI")}


__all__ = ["AccumulativeSwingIndex"]
