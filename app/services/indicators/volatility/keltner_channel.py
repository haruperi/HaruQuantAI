"""Keltner Channel (KC) indicator family implementation.

Description:
    Computes Chester Keltner's volatility channels based on Average True Range /
    bar range envelopes around a moving average of typical price.
    Middle = SMA(Typical Price, Period), where Typical = (High + Low + Close) / 3.
    Offset = SMA(High - Low, Period) * Deviation.
    Upper = Middle + Offset.
    Lower = Middle - Offset.
    Provides condition helpers for band closes, band opens, breakouts, and band
    slope direction.

Purpose:
    FEAT-SERVICES-INDICATOR-KELTNER: Keltner Channel calculation and conditions.

Key Capabilities:
    - FR-SERVICES-KELTNER-CALCULATE: Vectorized Upper, Middle, Lower band calculation.
      Associated: `KeltnerChannel.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-KELTNER-CONDITIONS: Condition checks (closes, opens, slopes).
      Associated: `KeltnerChannel.bar_closes_above_upper()`,
                  `KeltnerChannel.bar_opens_above_upper()`,
                  `KeltnerChannel.upper_is_rising()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.keltner_channel import KeltnerChannel

    high = np.array([10.5, 11.0, 11.5, 12.0, 12.5])
    low = np.array([9.5, 10.0, 10.5, 11.0, 11.5])
    close = np.array([10.0, 10.5, 11.0, 11.5, 12.0])
    kc = KeltnerChannel.calculate(high, low, close, period=20, deviation=1.5)
    upper = kc["upper"].get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "keltner"
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


class KeltnerChannel(BaseIndicator):
    """Keltner Channel indicator family."""

    name: str = "KeltnerChannel"
    category: str = "Bands"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 20,
        deviation: float = 1.5,
    ) -> dict[str, IndicatorSeries]:
        """Compute Upper, Middle, and Lower Keltner Channel series."""
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-KELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        typical = (high_arr + low_arr + close_arr) / 3.0
        bar_range = high_arr - low_arr

        middle = MovingAverage.sma(typical, period)
        offset = MovingAverage.sma(bar_range, period) * deviation

        upper = middle + offset
        lower = middle - offset

        logger.info(
            "FR-SERVICES-KELTNER-CALCULATE: KC(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="KC.Upper"),
            "middle": IndicatorSeries(middle, name="KC.Middle"),
            "lower": IndicatorSeries(lower, name="KC.Lower"),
        }

    @staticmethod
    def _as_series(
        s: IndicatorSeries | Sequence[float] | np.ndarray,
    ) -> IndicatorSeries:
        return s if isinstance(s, IndicatorSeries) else IndicatorSeries(s)

    # Unified condition helpers
    @classmethod
    def bar_closes_above_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesAboveUpper (`Close[shift] > Upper[shift]`)."""
        return cls._as_series(close_series).is_greater(kc_dict["upper"], shift)

    @classmethod
    def bar_closes_below_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesBelowUpper (`Close[shift] < Upper[shift]`)."""
        return cls._as_series(close_series).is_lower(kc_dict["upper"], shift)

    @classmethod
    def bar_closes_above_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesAboveLower (`Close[shift] > Lower[shift]`)."""
        return cls._as_series(close_series).is_greater(kc_dict["lower"], shift)

    @classmethod
    def bar_closes_below_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesBelowLower (`Close[shift] < Lower[shift]`)."""
        return cls._as_series(close_series).is_lower(kc_dict["lower"], shift)

    @classmethod
    def bar_opens_above_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveUpper (`Open[shift] > Upper[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        u = kc_dict["upper"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(u)) and o > u

    @classmethod
    def bar_opens_below_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowUpper (`Open[shift] < Upper[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        u = kc_dict["upper"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(u)) and (o < u)

    @classmethod
    def bar_opens_above_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveLower (`Open[shift] > Lower[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        lo = kc_dict["lower"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(lo)) and (o > lo)

    @classmethod
    def bar_opens_below_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowLower (`Open[shift] < Lower[shift + 1]`)."""
        o = cls._as_series(open_series).get(shift)
        lo = kc_dict["lower"].get(shift + 1)
        return not (np.isnan(o) or np.isnan(lo)) and (o < lo)

    @classmethod
    def bar_opens_above_upper_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveUpperAfterOpenBelow (`Open[s+1] < Upper[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, u1 = os.get(shift), os.get(shift + 1), kc_dict["upper"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(u1)) and (
            o1 < u1 and o0 > u1
        )

    @classmethod
    def bar_opens_below_upper_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowUpperAfterOpenAbove (`Open[s+1] > Upper[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, u1 = os.get(shift), os.get(shift + 1), kc_dict["upper"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(u1)) and (
            o1 > u1 and o0 < u1
        )

    @classmethod
    def bar_opens_above_lower_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveLowerAfterOpenBelow (`Open[s+1] < Lower[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, l1 = os.get(shift), os.get(shift + 1), kc_dict["lower"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(l1)) and (
            o1 < l1 and o0 > l1
        )

    @classmethod
    def bar_opens_below_lower_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowLowerAfterOpenAbove (`Open[s+1] > Lower[s+1]`)."""
        os = cls._as_series(open_series)
        o0, o1, l1 = os.get(shift), os.get(shift + 1), kc_dict["lower"].get(shift + 1)
        return not (np.isnan(o0) or np.isnan(o1) or np.isnan(l1)) and (
            o1 > l1 and o0 < l1
        )

    @classmethod
    def upper_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is rising."""
        return kc_dict["upper"].is_rising(shift)

    @classmethod
    def upper_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is falling."""
        return kc_dict["upper"].is_falling(shift)

    @classmethod
    def lower_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is rising."""
        return kc_dict["lower"].is_rising(shift)

    @classmethod
    def lower_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is falling."""
        return kc_dict["lower"].is_falling(shift)
