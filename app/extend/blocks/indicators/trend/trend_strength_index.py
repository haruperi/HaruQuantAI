"""Trend Strength Index (TSI) strategy block.

Description:
    Calculates the Trend Strength Index measuring cumulative directional price
    displacement normalized by absolute price movement over a lookback window.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend-strength-index: Trend strength index computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.trend_strength_index import (
        TrendStrengthIndex,
    )
    res = TrendStrengthIndex().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_SCALE_100: float = 100.0


class TrendStrengthIndex(BaseIndicator):
    """Trend Strength Index block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.trend_strength_index",
        version="1.0.0",
        name="Trend Strength Index",
        description="Quantifies directional trend persistence and power",
        category="trend",
        tags=("trend", "strength", "directional"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Trend Strength Index"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Trend Strength Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        tsi = np.full(n, np.nan, dtype=np.float64)
        p = self.period
        if n > p:
            diff = np.diff(close)
            abs_diff = np.abs(diff)
            diff_cs = np.insert(np.cumsum(diff), 0, 0.0)
            abs_cs = np.insert(np.cumsum(abs_diff), 0, 0.0)
            net_move = diff_cs[p:] - diff_cs[:-p]
            tot_move = abs_cs[p:] - abs_cs[:-p]
            with np.errstate(divide="ignore", invalid="ignore"):
                val = np.where(
                    tot_move > _EPSILON, _SCALE_100 * net_move / tot_move, 0.0
                )
            tsi[p:] = val
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated TrendStrength(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(tsi, name="TSI_Trend")}


__all__ = ["TrendStrengthIndex"]
