"""StdDev indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-STDDEV: validated batch calculation.
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


class StdDev(BaseIndicator):
    """Standard Deviation indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.std_dev",
        name="StdDev",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        data = bars.close
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-STDDEV-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20
        res = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            if len(win) > 0:
                res[i] = float(np.std(win, ddof=0))
        logger.info(
            "FR-SERVICES-STDDEV-CALCULATE: Computed StdDev(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"StdDev({period})")}
