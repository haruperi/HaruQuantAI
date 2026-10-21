"""Bollinger Bands (BB) indicator family.

Description:
    Computes Bollinger Bands (Upper, Middle, Lower, BandWidth, and BBRange).
    Consolidates calculations, BBRange, BBWidthRatio, band slope conditions, and
    bar open/close vs. band conditions into a unified Python module.

Purpose:
    FEAT-SERVICES-INDICATOR-BB: Bollinger Bands volatility envelopes and conditions.

Key Capabilities:
    - FR-SERVICES-BB-CALCULATE: Compute Upper, Middle, Lower, BandWidth, and Range.
      Associated: `BollingerBands.calculate()`, `BollingerBands.bb_range()`,
      `BollingerBands.bb_width_ratio()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-BB-CONDITIONS: Evaluate price crossing, bar open/close, and
      band slopes.
      Associated: `BollingerBands.price_crosses_above_upper()`,
      `BollingerBands.bar_closes_above_upper()`, `BollingerBands.upper_is_rising()`
      Logging: DEBUG on evaluation of BB conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.bollinger_bands import BollingerBands

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0])
    bb = BollingerBands.calculate(close, period=5, deviation=2.0)
    upper_val = bb["upper"].get(0)
    lower_val = bb["lower"].get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "bollinger"
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


class BollingerBands(BaseIndicator):
    """Bollinger Bands family consolidating Upper/Middle/Lower bands and conditions."""

    name = "(BB) Bollinger Bands"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 20,
        deviation: float = 2.0,
    ) -> dict[str, IndicatorSeries]:
        """Compute Bollinger Bands (`upper`, `middle`, `lower`, `bandwidth`, etc.)."""
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-BB-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        middle_arr = MovingAverage.sma(arr, period)
        upper_arr = np.full(n, np.nan, dtype=np.float64)
        lower_arr = np.full(n, np.nan, dtype=np.float64)
        bandwidth_arr = np.full(n, np.nan, dtype=np.float64)
        range_arr = np.full(n, np.nan, dtype=np.float64)

        for i in range(period - 1, n):
            window = arr[i - period + 1 : i + 1]
            std = float(np.std(window, ddof=0))
            mid = middle_arr[i]
            upper_arr[i] = mid + deviation * std
            lower_arr[i] = mid - deviation * std
            range_arr[i] = 2.0 * deviation * std
            if mid != 0.0:
                bandwidth_arr[i] = (upper_arr[i] - lower_arr[i]) / mid

        logger.info(
            "FR-SERVICES-BB-CALCULATE: Computed BB(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )

        return {
            "upper": IndicatorSeries(upper_arr, name="BB.Upper"),
            "middle": IndicatorSeries(middle_arr, name="BB.Middle"),
            "lower": IndicatorSeries(lower_arr, name="BB.Lower"),
            "bandwidth": IndicatorSeries(bandwidth_arr, name="BB.BandWidth"),
            "range": IndicatorSeries(range_arr, name="BB.Range"),
        }

    @classmethod
    def bb_range(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 20,
        deviation: float = 2.0,
    ) -> IndicatorSeries:
        """Compute BBRange series (`2 * deviation * std_dev`)."""
        return cls.calculate(data, period=period, deviation=deviation)["range"]

    @classmethod
    def bb_width_ratio(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 20,
        deviation: float = 2.0,
    ) -> IndicatorSeries:
        """Compute BBWidthRatio (`2 * deviation * std_dev / SMA` when `SMA > 0`)."""
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            period = 20
        out = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            sma_val = float(np.mean(win))
            diff_sq = float(np.sum(np.square(win - sma_val)))
            sko = float(np.sqrt(diff_sq / period))
            out[i] = (2.0 * deviation * sko / sma_val) if sma_val > 0.0 else 0.0
        logger.info(
            "FR-SERVICES-BB-CALCULATE: BBWidthRatio(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )
        return IndicatorSeries(out, name="BB.WidthRatio")

    @staticmethod
    def _as_series(
        s: IndicatorSeries | Sequence[float] | np.ndarray,
    ) -> IndicatorSeries:
        return s if isinstance(s, IndicatorSeries) else IndicatorSeries(s)

    # Unified condition helpers
    @classmethod
    def price_crosses_above_upper(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price crosses above Upper band condition."""
        return price_series.crosses_above(bands["upper"], shift)

    @classmethod
    def price_crosses_below_lower(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price crosses below Lower band condition."""
        return price_series.crosses_below(bands["lower"], shift)

    @classmethod
    def price_higher_upper(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price is higher than Upper band."""
        return price_series.is_greater(bands["upper"], shift)

    @classmethod
    def price_lower_lower(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price is lower than Lower band."""
        return price_series.is_lower(bands["lower"], shift)

    @classmethod
    def upper_is_rising(cls, bands: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate BBUpperRising (`Upper[shift + 1] < Upper[shift]`)."""
        return bands["upper"].is_rising(shift)

    @classmethod
    def upper_is_falling(
        cls, bands: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate BBUpperFalling (`Upper[shift + 1] > Upper[shift]`)."""
        return bands["upper"].is_falling(shift)

    @classmethod
    def lower_is_rising(cls, bands: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate BBLowerRising (`Lower[shift + 1] < Lower[shift]`)."""
        return bands["lower"].is_rising(shift)

    @classmethod
    def lower_is_falling(
        cls, bands: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate BBLowerFalling (`Lower[shift + 1] > Lower[shift]`)."""
        return bands["lower"].is_falling(shift)

    @classmethod
    def bar_closes_above_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarClosesAboveUp (`Close[shift] > Upper[shift]`)."""
        return cls._as_series(close_series).is_greater(bands["upper"], shift)

    @classmethod
    def bar_closes_below_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarClosesBelowUp (`Close[shift] < Upper[shift]`)."""
        return cls._as_series(close_series).is_lower(bands["upper"], shift)

    @classmethod
    def bar_closes_above_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarClosesAboveDown (`Close[shift] > Lower[shift]`)."""
        return cls._as_series(close_series).is_greater(bands["lower"], shift)

    @classmethod
    def bar_closes_below_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarClosesBelowDown (`Close[shift] < Lower[shift]`)."""
        return cls._as_series(close_series).is_lower(bands["lower"], shift)

    @classmethod
    def bar_opens_above_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensAboveUp (`Open[shift] > Upper[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        u = bands["upper"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(u)) and (o > u)

    @classmethod
    def bar_opens_below_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensBelowUp (`Open[shift] < Upper[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        u = bands["upper"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(u)) and (o < u)

    @classmethod
    def bar_opens_above_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensAboveDown (`Open[shift] > Lower[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        lo = bands["lower"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(lo)) and (o > lo)

    @classmethod
    def bar_opens_below_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensBelowDown (`Open[shift] < Lower[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        lo = bands["lower"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(lo)) and (o < lo)

    @classmethod
    def bar_opens_above_upper_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensAboveUpAfterOpenBelow (`Open[s+1] < Upper[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, u1 = os.get(shift), os.get(shift + 1), bands["upper"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(u1)) and (
            o1 < u1 and o0 > u1
        )

    @classmethod
    def bar_opens_below_upper_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensBelowUpAfterOpenAbove (`Open[s+1] > Upper[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, u1 = os.get(shift), os.get(shift + 1), bands["upper"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(u1)) and (
            o1 > u1 and o0 < u1
        )

    @classmethod
    def bar_opens_above_lower_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensAboveDownAfterOpenBelow (`Open[s+1] < Lower[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, l1 = os.get(shift), os.get(shift + 1), bands["lower"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(l1)) and (
            o1 < l1 and o0 > l1
        )

    @classmethod
    def bar_opens_below_lower_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate BBBarOpensBelowDownAfterOpenAbove (`Open[s+1] > Lower[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, l1 = os.get(shift), os.get(shift + 1), bands["lower"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(l1)) and (
            o1 > l1 and o0 < l1
        )
