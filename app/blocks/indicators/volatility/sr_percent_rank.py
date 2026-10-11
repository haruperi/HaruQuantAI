"""Support/Resistance Percent Rank (SRPercentRank) indicator family implementation.

Description:
    Computes Support/Resistance Percent Rank (SRPercentRank) measuring the percentage
    of historical bars within lookback Length where the current Close falls within
    the bar's range (Mode 1: Low < Close < High) or within an ATR buffer around
    the bar's range (Mode 2: Low - ATR < Close < High + ATR).
    Used to identify consolidation zones, breakout regions, and key support/resistance.

Purpose:
    FEAT-BLOCKS-INDICATOR-SRPERCENT: SR Percent Rank calculation and condition blocks.

Key Capabilities:
    - FR-BLOCKS-SRPERCENT-CALCULATE: Vectorized calculation of SR Percent Rank values.
      Associated: `SRPercentRank.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-SRPERCENT-CONDITIONS: Threshold and persistence condition checks.
      Associated: `SRPercentRank.is_above_level()`,
                  `SRPercentRank.is_below_level()`,
                  `SRPercentRank.is_above_level_x_bars()`,
                  `SRPercentRank.is_below_level_x_bars()`,
                  `SRPercentRank.is_rising()`, `SRPercentRank.is_falling()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.sr_percent_rank import SRPercentRank

    high = np.array([10.5, 10.8, 11.0, 10.9, 11.2, 11.5])
    low = np.array([9.5, 9.8, 10.0, 9.9, 10.2, 10.5])
    close = np.array([10.0, 10.2, 10.5, 10.1, 10.8, 11.0])

    sr = SRPercentRank.calculate(high, low, close, mode=1, length=3, atr_period=3)
    val = sr.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.sr_percent_rank
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.volatility.mt_atr import MTATR
from app.host.logging import get_logger

logger = get_logger(__name__)


class SRPercentRank(BaseIndicator):
    """Support/Resistance Percent Rank indicator family."""

    name: str = "SRPercentRank"
    category: str = "SupportResistance"

    MODE_BASIC = 1
    MODE_ATR = 2

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        mode: int = 1,
        length: int = 120,
        atr_period: int = 12,
    ) -> IndicatorSeries:
        """Calculate SRPercentRank.

        FR-BLOCKS-SRPERCENT-CALCULATE:
            Mode 1 (Basic): Percent of bars in [t-length, t-1] where
            Low < Close[t] < High.
            Mode 2 (ATR): Percent of bars where Low - ATR < Close[t] < High + ATR.
        """
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
                cls.name,
                length,
                n,
            )
            return IndicatorSeries(
                res, name=f"SRPercentRank({mode},{length},{atr_period})"
            )

        if mode == cls.MODE_ATR:
            atr_series = MTATR.calculate(h_arr, l_arr, c_arr, period=atr_period)
            atr_vals = atr_series.values
        else:
            atr_vals = np.zeros(n, dtype=np.float64)

        for t in range(length + 1, n):
            c_val = c_arr[t]
            low_window = l_arr[t - length : t]
            high_window = h_arr[t - length : t]

            if mode == cls.MODE_BASIC:
                match_count = int(np.sum((c_val > low_window) & (c_val < high_window)))
            elif mode == cls.MODE_ATR:
                atr_val = atr_vals[t]
                if np.isnan(atr_val):
                    match_count = 0
                else:
                    match_count = int(
                        np.sum(
                            (c_val > (low_window - atr_val))
                            & (c_val < (high_window + atr_val))
                        )
                    )
            else:
                match_count = 0

            res[t] = (float(match_count) / float(length)) * 100.0

        logger.info(
            "Calculated %s: mode=%d, length=%d, atr_period=%d, output size=%d",
            cls.name,
            mode,
            length,
            atr_period,
            n,
        )
        return IndicatorSeries(res, name=f"SRPercentRank({mode},{length},{atr_period})")

    @classmethod
    def is_above_level(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is above level."""
        val = series.get(shift)
        res = bool(val > level)
        logger.debug(
            "FR-BLOCKS-SRPERCENT-CONDITIONS is_above_level val=%.4f level=%.4f res=%s",
            val,
            level,
            res,
        )
        return res

    @classmethod
    def is_below_level(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is below level."""
        val = series.get(shift)
        res = bool(val < level)
        logger.debug(
            "FR-BLOCKS-SRPERCENT-CONDITIONS is_below_level val=%.4f level=%.4f res=%s",
            val,
            level,
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
            val = series.get(shift + i)
            if val < level:
                logger.debug(
                    "FR-BLOCKS-SRPERCENT-CONDITIONS above failed at bar %d "
                    "(val=%.4f < %.4f)",
                    i,
                    val,
                    level,
                )
                return False
            if val > level:
                at_least_once = True
        return at_least_once

    @classmethod
    def is_below_level_x_bars(
        cls, series: IndicatorSeries, level: float, bars: int = 2, shift: int = 0
    ) -> bool:
        """Check if SRPercentRank is below level for X consecutive bars."""
        at_least_once = False
        for i in range(bars):
            val = series.get(shift + i)
            if val > level:
                logger.debug(
                    "FR-BLOCKS-SRPERCENT-CONDITIONS below failed at bar %d "
                    "(val=%.4f > %.4f)",
                    i,
                    val,
                    level,
                )
                return False
            if val < level:
                at_least_once = True
        return at_least_once

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if SRPercentRank is rising."""
        curr = series.get(shift)
        prev = series.get(shift + 1)
        res = bool(curr > prev)
        logger.debug(
            "FR-BLOCKS-SRPERCENT-CONDITIONS is_rising curr=%.4f prev=%.4f res=%s",
            curr,
            prev,
            res,
        )
        return res

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if SRPercentRank is falling."""
        curr = series.get(shift)
        prev = series.get(shift + 1)
        res = bool(curr < prev)
        logger.debug(
            "FR-BLOCKS-SRPERCENT-CONDITIONS is_falling curr=%.4f prev=%.4f res=%s",
            curr,
            prev,
            res,
        )
        return res
