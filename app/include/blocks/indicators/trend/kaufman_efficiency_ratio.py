"""KaufmanEfficiencyRatio indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-KAUFMANEFFICIENCYRATIO: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class KaufmanEfficiencyRatio(BaseIndicator):
    """Kaufman Efficiency Ratio indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.kaufman_efficiency_ratio",
        name="KaufmanEfficiencyRatio",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 40, "default": 10}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=11,
    )
    period: int = Field(default=10, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = bars.close
        period = self.period
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-KER-CALCULATE: Invalid period %d, defaulting to 10", period
            )
            period = 10
        res = np.zeros(n, dtype=np.float64)
        if n <= period:
            logger.info(
                "FR-SERVICES-KER-CALCULATE: Insufficient bars (%d <= %d), all 0.0",
                n,
                period,
            )
            return {"value": IndicatorSeries(res, name=f"KER({period})")}
        diffs = np.abs(np.diff(c_arr))
        for t in range(period, n):
            change = abs(c_arr[t] - c_arr[t - period])
            vol_sum = float(np.sum(diffs[t - period : t]))
            if vol_sum > 0:
                res[t] = min(1.0, change / vol_sum)
            else:
                res[t] = 0.0
        logger.info(
            "FR-SERVICES-KER-CALCULATE: Computed KER(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(res, name=f"KER({period})")}
