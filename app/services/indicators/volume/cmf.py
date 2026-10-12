"""Chaikin Money Flow (CMF) Indicator Block.

Description:
    Computes the Chaikin Money Flow (CMF) oscillator measuring institutional
    accumulation and distribution over a specified lookback period.
    Formula: Sum(((Close - Low) - (High - Close)) / (High - Low) * Volume, n)
             / Sum(Volume, n).
    Values range from -1.0 to +1.0 with zero acting as the centerline.

Purpose:
    FEAT-SERVICES-INDICATOR-CMF

Key Capabilities:
    - FR-SERVICES-CMF-CALCULATE: Computes rolling money flow volume divided by volume.
    - FR-SERVICES-CMF-CONDITIONS: Evaluates positive, negative, and zero crossovers.

Python API Usage:
    ```python
    from app.services.indicators.volume.cmf import CMF

    cmf = CMF.calculate(high, low, close, volume, period=20)
    is_bullish = CMF.is_above_zero(cmf, shift=0)
    cross_up = CMF.crosses_above(cmf, level=0.0, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_CMF_PERIOD: int = 1
DEFAULT_CMF_PERIOD: int = 20
EPSILON: float = 1e-12


class CMF(BaseIndicator):
    """Chaikin Money Flow volume accumulation/distribution indicator."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_CMF_PERIOD,
    ) -> IndicatorSeries:
        """Compute rolling Chaikin Money Flow.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Volume series.
            period: Lookback window (>= 1).

        Returns:
            IndicatorSeries containing CMF values in [-1, 1].
        """
        logger.info("CMF calculation initiated: period=%d", period)
        if period < MIN_CMF_PERIOD:
            raise ValueError(f"period must be >= {MIN_CMF_PERIOD}, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        cmf_vals = cls._compute_cmf(h_arr, l_arr, c_arr, v_arr, period)
        return IndicatorSeries(cmf_vals, name=f"CMF({period})")

    @classmethod
    def _compute_cmf(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        period: int,
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        cmf = np.zeros(n, dtype=np.float64)

        # Money Flow Multiplier
        rng = h_arr - l_arr
        mfm = np.zeros(n, dtype=np.float64)
        valid_rng = rng > EPSILON
        mfm[valid_rng] = (
            (c_arr[valid_rng] - l_arr[valid_rng])
            - (h_arr[valid_rng] - c_arr[valid_rng])
        ) / rng[valid_rng]

        mfv = mfm * v_arr

        for i in range(n):
            start = max(0, i - period + 1)
            sum_mfv = float(np.sum(mfv[start : i + 1]))
            sum_vol = float(np.sum(v_arr[start : i + 1]))
            cmf[i] = sum_mfv / sum_vol if sum_vol > EPSILON else 0.0

        return cmf

    @classmethod
    def is_above_zero(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is above zero (buying pressure)."""
        logger.info("Evaluating CMF is_above_zero at shift=%d", shift)
        val = cmf.get(shift)
        return not np.isnan(val) and val > 0.0

    @classmethod
    def is_below_zero(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is below zero (selling pressure)."""
        logger.info("Evaluating CMF is_below_zero at shift=%d", shift)
        val = cmf.get(shift)
        return not np.isnan(val) and val < 0.0

    @classmethod
    def crosses_above(
        cls, cmf: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if CMF crosses above specified level."""
        logger.info("Evaluating CMF crosses_above level=%.2f at shift=%d", level, shift)
        curr = cmf.get(shift)
        prev = cmf.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(
        cls, cmf: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if CMF crosses below specified level."""
        logger.info("Evaluating CMF crosses_below level=%.2f at shift=%d", level, shift)
        curr = cmf.get(shift)
        prev = cmf.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)

    @classmethod
    def is_rising(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating CMF is_rising at shift=%d", shift)
        curr = cmf.get(shift)
        prev = cmf.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating CMF is_falling at shift=%d", shift)
        curr = cmf.get(shift)
        prev = cmf.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
