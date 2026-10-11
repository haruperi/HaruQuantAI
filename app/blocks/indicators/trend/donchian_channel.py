"""Donchian Channels Indicator Block.

Description:
    Calculates Donchian Channels developed by Richard Donchian. The upper band
    represents the highest high over the lookback window, the lower band
    represents the lowest low, and the middle band is the simple arithmetic mean
    of the upper and lower bands. The channel width measures market volatility
    and channel squeezes.

Purpose:
    FEAT-BLOCKS-INDICATOR-DONCHIAN

Key Capabilities:
    - FR-BLOCKS-DONCHIAN-CALCULATE: Computes upper, lower, middle bands and width.
      Associated: `DonchianChannels.calculate()`
      Logging: INFO level logging of period and bar count.
    - FR-BLOCKS-DONCHIAN-CONDITIONS: Evaluates breakouts, middle crosses, and squeeze.
      Associated: `DonchianChannels.is_above_upper()`, `is_squeezed()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.blocks.indicators.trend.donchian_channel import DonchianChannels

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

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

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
        p_val = price.get(shift)
        u_val = upper.get(shift)
        return not np.isnan(p_val) and not np.isnan(u_val) and p_val > u_val

    @classmethod
    def is_below_lower(
        cls,
        price: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price is less than lower channel band."""
        logger.info("Evaluating Donchian is_below_lower at shift=%d", shift)
        p_val = price.get(shift)
        l_val = lower.get(shift)
        return not np.isnan(p_val) and not np.isnan(l_val) and p_val < l_val

    @classmethod
    def crosses_above_upper(
        cls,
        price: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses above upper band."""
        logger.info("Evaluating Donchian crosses_above_upper at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        u_curr = upper.get(shift)
        u_prev = upper.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(u_curr) or np.isnan(u_prev):
            return False
        return bool(p_prev <= u_prev and p_curr > u_curr)

    @classmethod
    def crosses_below_lower(
        cls,
        price: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses below lower band."""
        logger.info("Evaluating Donchian crosses_below_lower at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        l_curr = lower.get(shift)
        l_prev = lower.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(l_curr) or np.isnan(l_prev):
            return False
        return bool(p_prev >= l_prev and p_curr < l_curr)

    @classmethod
    def crosses_above_middle(
        cls,
        price: IndicatorSeries,
        middle: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses above middle band."""
        logger.info("Evaluating Donchian crosses_above_middle at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        m_curr = middle.get(shift)
        m_prev = middle.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(m_curr) or np.isnan(m_prev):
            return False
        return bool(p_prev <= m_prev and p_curr > m_curr)

    @classmethod
    def crosses_below_middle(
        cls,
        price: IndicatorSeries,
        middle: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses below middle band."""
        logger.info("Evaluating Donchian crosses_below_middle at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        m_curr = middle.get(shift)
        m_prev = middle.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(m_curr) or np.isnan(m_prev):
            return False
        return bool(p_prev >= m_prev and p_curr < m_curr)

    @classmethod
    def is_squeezed(
        cls,
        width: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if channel width is less than specified threshold."""
        logger.info("Evaluating Donchian is_squeezed at shift=%d", shift)
        w_val = width.get(shift)
        return not np.isnan(w_val) and w_val <= threshold
