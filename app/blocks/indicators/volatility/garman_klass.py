"""Garman-Klass Volatility Estimator Block.

Description:
    Computes Garman and Klass's volatility estimator extending Parkinson's
    model by incorporating opening and closing prices alongside highs and lows.
    This captures jump opening risk and continuous intraday drift, providing
    approximately seven to eight times higher statistical efficiency than
    standard close-to-close estimators.

Purpose:
    FEAT-BLOCKS-INDICATOR-GARMAN-KLASS

Key Capabilities:
    - FR-BLOCKS-GARMANKLASS-CALCULATE: Computes rolling Garman-Klass volatility.
      Associated: `GarmanKlassVolatility.calculate()`
      Logging: INFO level logging of period, annualization, and bar count.
    - FR-BLOCKS-GARMANKLASS-CONDITIONS: Evaluates elevated, subdued, and trend states.
      Associated: `GarmanKlassVolatility.is_elevated()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.blocks.indicators.volatility.garman_klass import GarmanKlassVolatility

    vol = GarmanKlassVolatility.calculate(open, high, low, close, period=20)
    is_high = GarmanKlassVolatility.is_elevated(vol, threshold=0.25, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

MIN_GK_PERIOD: int = 2
DEFAULT_GK_PERIOD: int = 20
DEFAULT_TRADING_PERIODS: int = 252
EPSILON: float = 1e-12
GK_HIGH_LOW_FACTOR: float = 0.5
GK_CLOSE_FACTOR: float = 2.0 * np.log(2.0) - 1.0


class GarmanKlassVolatility(BaseIndicator):
    """Garman-Klass OHLC volatility estimator block."""

    @classmethod
    @override
    def calculate(
        cls,
        open: IndicatorSeries | np.ndarray[Any, Any],
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_GK_PERIOD,
        annualize: bool = False,
        trading_periods: int = DEFAULT_TRADING_PERIODS,
    ) -> IndicatorSeries:
        """Compute rolling Garman-Klass volatility.

        Args:
            open: Open price series.
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Lookback window (>= 2).
            annualize: Whether to scale by sqrt(trading_periods).
            trading_periods: Annualization factor (e.g. 252 or 365).

        Returns:
            IndicatorSeries with Garman-Klass volatility values.
        """
        logger.info(
            "GarmanKlassVolatility initiated: period=%d, annualize=%s",
            period,
            annualize,
        )
        if period < MIN_GK_PERIOD:
            raise ValueError(f"period must be >= {MIN_GK_PERIOD}, got {period}")
        if trading_periods < 1:
            raise ValueError(f"trading_periods must be >= 1, got {trading_periods}")

        o_arr = cls.to_numpy(open)
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        ann_factor = np.sqrt(float(trading_periods)) if annualize else 1.0
        vol_vals = cls._compute_garman_klass(
            (o_arr, h_arr, l_arr, c_arr), period, ann_factor
        )
        logger.info("GarmanKlassVolatility completed: bars=%d", n)
        return IndicatorSeries(vol_vals, name=f"GarmanKlass({period})")

    @classmethod
    def _compute_garman_klass(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        period: int,
        ann_factor: float,
    ) -> np.ndarray[Any, Any]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        valid_o = np.maximum(o_arr, EPSILON)
        valid_l = np.maximum(l_arr, EPSILON)
        valid_h = np.maximum(h_arr, valid_l)
        valid_c = np.maximum(c_arr, EPSILON)

        log_hl = np.log(valid_h / valid_l)
        log_co = np.log(valid_c / valid_o)

        bar_var = (GK_HIGH_LOW_FACTOR * log_hl * log_hl) - (
            GK_CLOSE_FACTOR * log_co * log_co
        )
        vol = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            mean_var = float(np.sum(bar_var[start : i + 1])) / window_len
            vol[i] = np.sqrt(max(0.0, mean_var)) * ann_factor

        return vol

    @classmethod
    def is_elevated(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility exceeds threshold."""
        logger.info(
            "Evaluating GarmanKlass is_elevated: threshold=%.4f, shift=%d",
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
        """True if volatility is below threshold."""
        logger.info(
            "Evaluating GarmanKlass is_subdued: threshold=%.4f, shift=%d",
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
            "Evaluating GarmanKlass crosses_above: threshold=%.4f, shift=%d",
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
            "Evaluating GarmanKlass crosses_below: threshold=%.4f, shift=%d",
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
        logger.info("Evaluating GarmanKlass is_rising at shift=%d", shift)
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is falling between shift+1 and shift."""
        logger.info("Evaluating GarmanKlass is_falling at shift=%d", shift)
        curr = vol.get(shift)
        prev = vol.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
