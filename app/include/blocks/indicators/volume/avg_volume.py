"""AvgVolume indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AVGVOLUME: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
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

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if average volume is rising at shift compared to shift+1."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if average volume is falling at shift compared to shift+1."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 crosses above series2."""
        return crosses_above(series1, series2, shift=shift)

    @classmethod
    def crosses_below(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 crosses below series2."""
        return crosses_below(series1, series2, shift=shift)

    @classmethod
    def is_higher(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 is higher than series2."""
        return is_greater(series1, series2, shift=shift)

    @classmethod
    def is_lower(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 is lower than series2."""
        return is_lower(series1, series2, shift=shift)

    @classmethod
    def volume_is_rising(cls, volume: IndicatorSeries, shift: int = 0) -> bool:
        """Check if raw bar volume is rising at shift compared to shift+1."""
        return is_rising(volume, shift=shift)

    @classmethod
    def volume_is_falling(cls, volume: IndicatorSeries, shift: int = 0) -> bool:
        """Check if raw bar volume is falling at shift compared to shift+1."""
        return is_falling(volume, shift=shift)

    @classmethod
    def volume_above_average(
        cls, volume: IndicatorSeries, avg_volume: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Check if raw bar volume is greater than average volume at shift."""
        return is_greater(volume, avg_volume, shift=shift)
