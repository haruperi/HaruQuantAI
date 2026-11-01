"""AvgVolume indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AVGVOLUME: validated batch calculation.
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
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_PERIOD: int = 14


class AvgVolume(BaseIndicator):
    """Average Volume indicator with trend and crossover condition evaluation."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.avg_volume",
        name="AvgVolume",
        category="volume",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("volume", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("volume",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=DEFAULT_PERIOD, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        volume = bars.volume
        period = self.period
        vol_arr = to_numpy(volume)
        n = len(vol_arr)
        if period < 1:
            logger.warning(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Invalid period %d, defaulting to %d",
                period,
                DEFAULT_PERIOD,
            )
            period = DEFAULT_PERIOD
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            logger.info(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return {"value": IndicatorSeries(out, name=f"AvgVolume({period})")}
        cumsum = np.cumsum(np.nan_to_num(vol_arr, nan=0.0))
        out[period - 1] = cumsum[period - 1] / period
        out[period:] = (cumsum[period:] - cumsum[:-period]) / period
        logger.info(
            "FR-SERVICES-AVGVOLUME-CALCULATE: AvgVolume(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(out, name=f"AvgVolume({period})")}
