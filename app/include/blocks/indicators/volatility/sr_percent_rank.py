"""SRPercentRank indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-SRPERCENTRANK: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import is_falling, is_lower, is_rising
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.volatility.mt_atr import MTATR
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

ATR_MODE = 2

logger = get_logger(__name__)


class SRPercentRank(BaseIndicator):
    """Support/Resistance Percent Rank indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.sr_percent_rank",
        name="SRPercentRank",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "mode": {"type": "int", "choices": [1, 2], "default": 1},
            "length": {"type": "int", "min": 1, "max": 480, "default": 120},
            "atr_period": {"type": "int", "min": 1, "max": 48, "default": 12},
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.volatility.mt_atr",),
        required_history_lookback=122,
    )
    mode: Literal[1, 2] = Field(default=1)
    length: int = Field(default=120, ge=1)
    atr_period: int = Field(default=12, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.length + 2, self.atr_period + 1)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        mode = self.mode
        length = self.length
        atr_period = self.atr_period
        h_arr = np.asarray(high, dtype=np.float64)
        l_arr = np.asarray(low, dtype=np.float64)
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)
        if n != len(h_arr) or n != len(l_arr):
            raise ValueError("High, low, and close arrays must have the same length.")
        res = np.zeros(n, dtype=np.float64)
        if n <= length + 1 or length <= 0:
            logger.info(
                "Calculated %s: length %d, data size %d (insufficient bars, all 0.0)",
                self.spec.name,
                length,
                n,
            )
            return {
                "value": IndicatorSeries(
                    res, name=f"SRPercentRank({mode},{length},{atr_period})"
                )
            }
        if mode == ATR_MODE:
            atr_series = MTATR(period=atr_period).calculate(bars)["value"]
            atr_vals = atr_series.values
        else:
            atr_vals = np.zeros(n, dtype=np.float64)
        for t in range(length + 1, n):
            c_val = c_arr[t]
            low_window = l_arr[t - length : t]
            high_window = h_arr[t - length : t]
            if mode == 1:
                match_count = int(np.sum((c_val > low_window) & (c_val < high_window)))
            else:
                atr_val = atr_vals[t]
                if np.isnan(atr_val):
                    match_count = 0
                else:
                    match_count = int(
                        np.sum(
                            (c_val > low_window - atr_val)
                            & (c_val < high_window + atr_val)
                        )
                    )
            res[t] = float(match_count) / float(length) * 100.0
        logger.info(
            "Calculated %s: mode=%d, length=%d, atr_period=%d, output size=%d",
            self.spec.name,
            mode,
            length,
            atr_period,
            n,
        )
        return {
            "value": IndicatorSeries(
                res, name=f"SRPercentRank({mode},{length},{atr_period})"
            )
        }

    @classmethod
    def is_above_level(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is above level."""
        res = is_greater(series, level, shift=shift)
        logger.debug(
            "FR-SERVICES-SRPERCENT-CONDITIONS is_above level=%.4f shift=%d res=%s",
            level,
            shift,
            res,
        )
        return res

    @classmethod
    def is_below_level(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is below level."""
        res = is_lower(series, level, shift=shift)
        logger.debug(
            "FR-SERVICES-SRPERCENT-CONDITIONS is_below level=%.4f shift=%d res=%s",
            level,
            shift,
            res,
        )
        return res

    @classmethod
    def is_above_level_x_bars(
        cls, series: IndicatorSeries, level: float, bars: int = 2, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is above level for X consecutive bars."""
        at_least_once = False
        for i in range(bars):
            if is_lower(series, level, shift1=shift + i):
                logger.debug(
                    "FR-SERVICES-SRPERCENT-CONDITIONS above failed at bar %d", i
                )
                return False
            if is_greater(series, level, shift1=shift + i):
                at_least_once = True
        return at_least_once

    @classmethod
    def is_below_level_x_bars(
        cls, series: IndicatorSeries, level: float, bars: int = 2, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is below level for X consecutive bars."""
        at_least_once = False
        for i in range(bars):
            if is_greater(series, level, shift1=shift + i):
                logger.debug(
                    "FR-SERVICES-SRPERCENT-CONDITIONS below failed at bar %d", i
                )
                return False
            if is_lower(series, level, shift1=shift + i):
                at_least_once = True
        return at_least_once

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if SRPercentRank is rising."""
        res = is_rising(series, shift=shift)
        logger.debug(
            "FR-SERVICES-SRPERCENT-CONDITIONS is_rising shift=%d res=%s", shift, res
        )
        return res

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if SRPercentRank is falling."""
        res = is_falling(series, shift=shift)
        logger.debug(
            "FR-SERVICES-SRPERCENT-CONDITIONS is_falling shift=%d res=%s", shift, res
        )
        return res
