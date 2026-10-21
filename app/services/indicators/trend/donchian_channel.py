"""Donchian Channels Indicator Block.

Description:
    Calculates Donchian Channels developed by Richard Donchian. The upper band
    represents the highest high over the lookback window, the lower band
    represents the lowest low, and the middle band is the simple arithmetic mean
    of the upper and lower bands. The channel width measures market volatility
    and channel squeezes.

Purpose:
    FEAT-SERVICES-INDICATOR-DONCHIAN

Key Capabilities:
    - FR-SERVICES-DONCHIAN-CALCULATE: Computes upper, lower, middle bands and width.
      Associated: `DonchianChannels.calculate()`
      Logging: INFO level logging of period and bar count.
    - FR-SERVICES-DONCHIAN-CONDITIONS: Evaluates breakouts, middle crosses, and squeeze.
      Associated: `DonchianChannels.is_above_upper()`, `is_squeezed()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.trend.donchian_channel import DonchianChannels

    channels = DonchianChannels.calculate(high, low, period=20)
    upper = channels["upper"]
    lower = channels["lower"]
    is_breakout = DonchianChannels.crosses_above_upper(close, upper, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    crosses_above,
    crosses_below,
    is_greater,
    is_lower,
    is_lower_or_equal,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_DONCHIAN_PERIOD: int = 2
DEFAULT_DONCHIAN_PERIOD: int = 20
EPSILON: float = 1e-12


class DonchianChannels(BaseIndicator):
    """Donchian Channels breakout envelope and volatility width block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_DONCHIAN_PERIOD,
        offset: int = 0,
    ) -> dict[str, IndicatorSeries]:
        """Compute Donchian Channel bands and channel width.

        Args:
            high: High price series.
            low: Low price series.
            period: Lookback window (>= 2).
            offset: Shift offset for bands (>= 0).

        Returns:
            Dictionary containing:
                - 'upper': Highest high over lookback window.
                - 'lower': Lowest low over lookback window.
                - 'middle': Arithmetic average of upper and lower bands.
                - 'width': Absolute channel width (upper - lower).
        """
        logger.info(
            "DonchianChannels calculation initiated: period=%d, offset=%d",
            period,
            offset,
        )
        if period < MIN_DONCHIAN_PERIOD:
            raise ValueError(f"period must be >= {MIN_DONCHIAN_PERIOD}, got {period}")
        if offset < 0:
            raise ValueError(f"offset must be >= 0, got {offset}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        upper, lower, middle, width = cls._compute_channels(
            h_arr, l_arr, period, offset, n
        )

        logger.info("DonchianChannels calculation completed: bars=%d", n)
        return {
            "upper": IndicatorSeries(upper, name=f"DonchianUpper({period})"),
            "lower": IndicatorSeries(lower, name=f"DonchianLower({period})"),
            "middle": IndicatorSeries(middle, name=f"DonchianMiddle({period})"),
            "width": IndicatorSeries(width, name=f"DonchianWidth({period})"),
        }

    @classmethod
    def _compute_channels(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        offset: int,
        n: int,
    ) -> tuple[
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
    ]:
        raw_upper = np.zeros(n, dtype=np.float64)
        raw_lower = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start = max(0, i - period + 1)
            raw_upper[i] = float(np.max(h_arr[start : i + 1]))
            raw_lower[i] = float(np.min(l_arr[start : i + 1]))

        if offset > 0:
            upper = np.full(n, np.nan, dtype=np.float64)
            lower = np.full(n, np.nan, dtype=np.float64)
            if offset < n:
                upper[offset:] = raw_upper[: n - offset]
                lower[offset:] = raw_lower[: n - offset]
        else:
            upper = raw_upper
            lower = raw_lower

        middle = (upper + lower) / 2.0
        width = upper - lower
        return upper, lower, middle, width

    @classmethod
    def is_above_upper(
        cls,
        price: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price is greater than upper channel band."""
        logger.info("Evaluating Donchian is_above_upper at shift=%d", shift)
        return is_greater(price, upper, shift=shift)

    @classmethod
    def is_below_lower(
        cls,
        price: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price is less than lower channel band."""
        logger.info("Evaluating Donchian is_below_lower at shift=%d", shift)
        return is_lower(price, lower, shift=shift)

    @classmethod
    def crosses_above_upper(
        cls,
        price: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses above upper band."""
        logger.info("Evaluating Donchian crosses_above_upper at shift=%d", shift)
        return crosses_above(price, upper, shift=shift)

    @classmethod
    def crosses_below_lower(
        cls,
        price: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses below lower band."""
        logger.info("Evaluating Donchian crosses_below_lower at shift=%d", shift)
        return crosses_below(price, lower, shift=shift)

    @classmethod
    def crosses_above_middle(
        cls,
        price: IndicatorSeries,
        middle: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses above middle band."""
        logger.info("Evaluating Donchian crosses_above_middle at shift=%d", shift)
        return crosses_above(price, middle, shift=shift)

    @classmethod
    def crosses_below_middle(
        cls,
        price: IndicatorSeries,
        middle: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses below middle band."""
        logger.info("Evaluating Donchian crosses_below_middle at shift=%d", shift)
        return crosses_below(price, middle, shift=shift)

    @classmethod
    def is_squeezed(
        cls,
        width: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if channel width is less than or equal to specified threshold."""
        logger.info("Evaluating Donchian is_squeezed at shift=%d", shift)
        return is_lower_or_equal(width, threshold, shift1=shift, round_digits=8)
