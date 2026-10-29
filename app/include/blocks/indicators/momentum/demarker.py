"""DeMarker indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-DEMARKER: validated batch calculation.
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
from app.include.calculators.average import sma_kernel

logger = get_logger(__name__)


class DeMarker(BaseIndicator):
    """DeMarker oscillator indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.demarker",
        name="DeMarker",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-DEMARKER-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        de_max = np.zeros(n, dtype=np.float64)
        de_min = np.zeros(n, dtype=np.float64)
        if n > 1:
            diff_h = high_arr[1:] - high_arr[:-1]
            diff_l = low_arr[:-1] - low_arr[1:]
            de_max[1:] = np.maximum(diff_h, 0.0)
            de_min[1:] = np.maximum(diff_l, 0.0)
        avg_de_max = sma_kernel(de_max, period)
        avg_de_min = sma_kernel(de_min, period)
        denom = avg_de_max + avg_de_min
        res = np.zeros(n, dtype=np.float64)
        valid = (denom != 0.0) & ~np.isnan(denom)
        res[valid] = avg_de_max[valid] / denom[valid]
        logger.info(
            "FR-SERVICES-DEMARKER-CALCULATE: Computed DeMarker(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"DeMarker({period})")}
