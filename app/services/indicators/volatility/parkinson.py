"""Parkinson Extreme Value Volatility Indicator Block.

Description:
    Computes Michael Parkinson's extreme value volatility estimator using the
    logarithmic ratio of high and low prices. The Parkinson estimator is up to
    five times more statistically efficient than standard close-to-close
    historical volatility because it accounts for continuous intraday price range.

Purpose:
    FEAT-SERVICES-INDICATOR-PARKINSON

Key Capabilities:
    - FR-SERVICES-PARKINSON-CALCULATE: Computes rolling extreme value variance/vol.
      Associated: `ParkinsonVolatility.calculate()`
      Logging: INFO level logging of period, annualization, and bar count.
    - FR-SERVICES-PARKINSON-CONDITIONS: Evaluates elevated, subdued, and trend states.
      Associated: `ParkinsonVolatility.is_elevated()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.volatility.parkinson import ParkinsonVolatility

    vol = ParkinsonVolatility.calculate(high, low, period=20, annualize=True)
    is_high_vol = ParkinsonVolatility.is_elevated(vol, threshold=0.30, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_PARKINSON_PERIOD: int = 2
DEFAULT_PARKINSON_PERIOD: int = 20
DEFAULT_TRADING_PERIODS: int = 252
EPSILON: float = 1e-12
PARKINSON_DENOM_FACTOR: float = 4.0 * np.log(2.0)


class ParkinsonVolatility(BaseIndicator):
    """Parkinson High-Low extreme value volatility estimator."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_PARKINSON_PERIOD,
        annualize: bool = False,
        trading_periods: int = DEFAULT_TRADING_PERIODS,
    ) -> IndicatorSeries:
        """Compute rolling Parkinson volatility.

        Args:
            high: High price series.
            low: Low price series.
            period: Lookback window (>= 2).
            annualize: Whether to scale by sqrt(trading_periods).
            trading_periods: Annualization factor (e.g. 252 or 365).

        Returns:
            IndicatorSeries with Parkinson volatility values.
        """
        logger.info(
            "ParkinsonVolatility initiated: period=%d, annualize=%s",
            period,
            annualize,
        )
        if period < MIN_PARKINSON_PERIOD:
            raise ValueError(f"period must be >= {MIN_PARKINSON_PERIOD}, got {period}")
        if trading_periods < 1:
            raise ValueError(f"trading_periods must be >= 1, got {trading_periods}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        ann_factor = np.sqrt(float(trading_periods)) if annualize else 1.0
        vol_vals = cls._compute_parkinson(h_arr, l_arr, period, ann_factor)
        logger.info("ParkinsonVolatility completed: bars=%d", n)
        return IndicatorSeries(vol_vals, name=f"Parkinson({period})")

    @classmethod
    def _compute_parkinson(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        ann_factor: float,
    ) -> np.ndarray[Any, Any]:
        n = len(h_arr)
        valid_l = np.maximum(l_arr, EPSILON)
        valid_h = np.maximum(h_arr, valid_l)
        log_hl = np.log(valid_h / valid_l)
        log_hl_sq = log_hl * log_hl

        vol = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            denom = PARKINSON_DENOM_FACTOR * window_len
            sum_sq = float(np.sum(log_hl_sq[start : i + 1]))
            vol[i] = np.sqrt(max(0.0, sum_sq / denom)) * ann_factor

        return vol

    @classmethod
    def is_elevated(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility exceeds specified threshold."""
        logger.info(
            "Evaluating Parkinson is_elevated: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        val = vol.get(shift)
        return not np.isnan(val) and val > threshold

    @classmethod
    def is_subdued(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility is below specified threshold."""
        logger.info(
            "Evaluating Parkinson is_subdued: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        val = vol.get(shift)
        return not np.isnan(val) and val < threshold

    @classmethod
    def crosses_above(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility crosses above threshold at shift."""
        logger.info(
            "Evaluating Parkinson crosses_above: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= threshold and curr > threshold)

    @classmethod
    def crosses_below(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility crosses below threshold at shift."""
        logger.info(
            "Evaluating Parkinson crosses_below: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= threshold and curr < threshold)

    @classmethod
    def is_rising(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is rising between shift+1 and shift."""
        logger.info("Evaluating Parkinson is_rising at shift=%d", shift)
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is falling between shift+1 and shift."""
        logger.info("Evaluating Parkinson is_falling at shift=%d", shift)
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
