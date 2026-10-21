"""Commodity Channel Index (CCI) indicator family.

Description:
    Computes Commodity Channel Index (CCI) and evaluates all standard level
    crossovers, slopes, direction changes, and Woodies CCI pattern conditions
    (Zero Line Break, Trend, ZLR, Famir, and Vegas Trade).

Purpose:
    FEAT-SERVICES-INDICATOR-CCI: Commodity Channel Index oscillator and conditions.

Key Capabilities:
    - FR-SERVICES-CCI-CALCULATE: Compute Typical Price, Mean Deviation, and CCI series.
      Associated: `CCI.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-CCI-CONDITIONS: Evaluate overbought, oversold, zero-line crosses,
      and Woodies CCI patterns.
      Associated: `CCI.crosses_above()`, `CCI.changes_up()`, `CCI.woodies_zlr_up()`
      Logging: DEBUG on evaluation of CCI conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.cci import CCI

    high = np.array([12.0, 12.5, 12.8, 12.2, 13.0, 12.9, 13.2])
    low = np.array([11.2, 11.5, 12.0, 11.8, 12.1, 12.0, 12.5])
    close = np.array([11.8, 12.2, 12.1, 12.0, 12.8, 12.6, 13.0])

    cci_series = CCI.calculate(high, low, close, period=5)
    current_cci = cci_series.get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "cci"
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.trend.moving_average import MovingAverage

logger = get_logger(__name__)

WOODIES_ZLR_BAND: float = 100.0
WOODIES_FAMIR_LEVEL: float = 50.0
WOODIES_VEGAS_LEVEL: float = 200.0


class CCI(BaseIndicator):
    """Commodity Channel Index family consolidating calculation and conditions."""

    name = "(CCI) Commodity Channel Index"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Commodity Channel Index (CCI) series."""
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-CCI-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        tp = (high_arr + low_arr + close_arr) / 3.0
        sma_tp = MovingAverage.sma(tp, period)
        cci_vals = np.full(n, np.nan, dtype=np.float64)

        for i in range(period - 1, n):
            window = tp[i - period + 1 : i + 1]
            mean_dev = float(np.mean(np.abs(window - sma_tp[i])))
            if mean_dev != 0.0:
                cci_vals[i] = (tp[i] - sma_tp[i]) / (0.015 * mean_dev)
            else:
                cci_vals[i] = 0.0

        logger.info(
            "FR-SERVICES-CCI-CALCULATE: Computed CCI(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(cci_vals, name="CCI")

    @staticmethod
    def _vals(series: IndicatorSeries, count: int, shift: int) -> list[float] | None:
        vals = [series.get(shift + k) for k in range(count)]
        if any(np.isnan(v) for v in vals):
            return None
        return vals

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIChangesUp condition (`CCI[s+2] > CCI[s+1] < CCI[s]`)."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIChangesDown condition (`CCI[s+2] < CCI[s+1] > CCI[s]`)."""
        return series.changes_down(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate CCICrossUp condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate CCICrossDown condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate CCIHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate CCILower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate CCIHigher than threshold level (`CCI[shift] > level`)."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower_level(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate CCILower than threshold level (`CCI[shift] < level`)."""
        return series.is_lower(level, shift)

    # Woodies CCI pattern conditions
    @classmethod
    def woodies_zero_line_break_up(
        cls, series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesCCIZeroLineBreakUP (`CCI[s+1] < 0 and CCI[s] > 0`)."""
        v = cls._vals(series, 2, shift)
        return v is not None and (v[1] < 0.0 and v[0] > 0.0)

    @classmethod
    def woodies_zero_line_break_down(
        cls, series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesCCIZeroLineBreakDown (`CCI[s+1] > 0 and CCI[s] < 0`)."""
        v = cls._vals(series, 2, shift)
        return v is not None and (v[1] > 0.0 and v[0] < 0.0)

    @classmethod
    def woodies_trend_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WoodiesTrendUP (6 consecutive bars `> 0`)."""
        v = cls._vals(series, 6, shift)
        return v is not None and all(x > 0.0 for x in v)

    @classmethod
    def woodies_trend_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WoodiesTrendDown (6 consecutive bars `< 0`)."""
        v = cls._vals(series, 6, shift)
        return v is not None and all(x < 0.0 for x in v)

    @classmethod
    def woodies_zlr_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesZLRUP zero-line reject bullish hook."""
        v = cls._vals(series, 6, shift)
        if v is None:
            return False
        curr, c1, c2 = v[0], v[1], v[2]
        trend_up = all(x > 0.0 for x in v)
        hook_up = curr > c1 and c2 > c1
        factor_cond = (curr - c1) > factor and (c2 - c1) > factor
        in_band = all(-WOODIES_ZLR_BAND < x < WOODIES_ZLR_BAND for x in (curr, c1, c2))
        return trend_up and hook_up and factor_cond and in_band

    @classmethod
    def woodies_zlr_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesZLRDown zero-line reject bearish hook."""
        v = cls._vals(series, 6, shift)
        if v is None:
            return False
        curr, c1, c2 = v[0], v[1], v[2]
        trend_dn = all(x < 0.0 for x in v)
        hook_dn = curr < c1 and c2 < c1
        factor_cond = (c1 - curr) > factor and (c1 - c2) > factor
        in_band = all(-WOODIES_ZLR_BAND < x < WOODIES_ZLR_BAND for x in (curr, c1, c2))
        return trend_dn and hook_dn and factor_cond and in_band

    @classmethod
    def woodies_famir_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesFamirUP failed ZLR bullish reversal."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3 = v[0], v[1], v[2], v[3]
        prior_neg = all(x < 0.0 for x in v[1:])
        broken_hook = c1 < c2 and c3 < c2 and curr > c1
        factor_cond = (c2 - c1) > factor and (c2 - c3) > factor
        return curr > -WOODIES_FAMIR_LEVEL and prior_neg and broken_hook and factor_cond

    @classmethod
    def woodies_famir_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesFamirDown failed ZLR bearish reversal."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3 = v[0], v[1], v[2], v[3]
        prior_pos = all(x > 0.0 for x in v[1:])
        broken_hook = c1 > c2 and c3 > c2 and curr < c1
        factor_cond = (c1 - c2) > factor and (c3 - c2) > factor
        return curr < WOODIES_FAMIR_LEVEL and prior_pos and broken_hook and factor_cond

    @classmethod
    def woodies_vegas_trade_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesVegasTradeUP extreme exhaustion bullish setup."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3, c4 = v[0], v[1], v[2], v[3], v[4]
        trend_dn = all(x < 0.0 for x in v[1:])
        area200 = any(x < -WOODIES_VEGAS_LEVEL for x in v[1:6])
        basket_up = c1 < c2 and c1 < c3 and c4 < c2 and c4 < c3
        factor_cond = (c2 - c1) > factor and (c3 - c4) > factor
        return (
            area200
            and basket_up
            and factor_cond
            and trend_dn
            and curr > ((c3 + c2) / 2.0)
        )

    @classmethod
    def woodies_vegas_trade_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesVegasTradeDown extreme exhaustion bearish setup."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3, c4 = v[0], v[1], v[2], v[3], v[4]
        trend_up = all(x > 0.0 for x in v[1:])
        area200 = any(x > WOODIES_VEGAS_LEVEL for x in v[1:6])
        basket_dn = c1 > c2 and c1 > c3 and c4 > c2 and c4 > c3
        factor_cond = (c4 - c3) > factor and (c1 - c2) > factor
        return (
            area200
            and basket_dn
            and factor_cond
            and trend_up
            and curr < ((c3 + c2) / 2.0)
        )
