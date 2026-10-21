"""Rogers-Satchell Non-Zero Drift Volatility Estimator Block.

Description:
    Computes Rogers and Satchell's volatility estimator. Unlike Parkinson and
    standard Garman-Klass estimators which assume zero drift, Rogers-Satchell
    provides an unbiased volatility estimate in the presence of strong non-zero
    trend drift using continuous OHLC intraday paths.

Purpose:
    FEAT-SERVICES-INDICATOR-ROGERS-SATCHELL

Key Capabilities:
    - FR-SERVICES-ROGERSSATCHELL-CALCULATE: Computes rolling Rogers-Satchell volatility.
      Associated: `RogersSatchellVolatility.calculate()`
      Logging: INFO level logging of period, annualization, and bar count.
    - FR-SERVICES-ROGERSSATCHELL-CONDITIONS: Evaluates elevated, subdued, and crosses.
      Associated: `RogersSatchellVolatility.is_elevated()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )

    vol = RogersSatchellVolatility.calculate(open, high, low, close, period=20)
    is_high = RogersSatchellVolatility.is_elevated(vol, threshold=0.25, shift=0)
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
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_RS_PERIOD: int = 2
DEFAULT_RS_PERIOD: int = 20
DEFAULT_TRADING_PERIODS: int = 252
EPSILON: float = 1e-12


class RogersSatchellVolatility(BaseIndicator):
    """Rogers-Satchell non-zero drift OHLC volatility estimator block."""

    @classmethod
    @override
    def calculate(
        cls,
        open: IndicatorSeries | np.ndarray[Any, Any],
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_RS_PERIOD,
        annualize: bool = False,
        trading_periods: int = DEFAULT_TRADING_PERIODS,
    ) -> IndicatorSeries:
        """Compute rolling Rogers-Satchell volatility.

        Args:
            open: Open price series.
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Lookback window (>= 2).
            annualize: Whether to scale by sqrt(trading_periods).
            trading_periods: Annualization factor (e.g. 252 or 365).

        Returns:
            IndicatorSeries with Rogers-Satchell volatility values.
        """
        logger.info(
            "RogersSatchellVolatility initiated: period=%d, annualize=%s",
            period,
            annualize,
        )
        if period < MIN_RS_PERIOD:
            raise ValueError(f"period must be >= {MIN_RS_PERIOD}, got {period}")
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
        vol_vals = cls._compute_rogers_satchell(
            (o_arr, h_arr, l_arr, c_arr), period, ann_factor
        )
        logger.info("RogersSatchellVolatility completed: bars=%d", n)
        return IndicatorSeries(vol_vals, name=f"RogersSatchell({period})")

    @classmethod
    def _compute_rogers_satchell(
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

        term1 = np.log(valid_h / valid_c) * np.log(valid_h / valid_o)
        term2 = np.log(valid_l / valid_c) * np.log(valid_l / valid_o)
        bar_var = term1 + term2

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
            "Evaluating RogersSatchell is_elevated: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_greater(vol, threshold, shift1=shift)

    @classmethod
    def is_subdued(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility is below threshold."""
        logger.info(
            "Evaluating RogersSatchell is_subdued: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_lower(vol, threshold, shift1=shift)

    @classmethod
    def crosses_above(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility crosses above threshold at shift."""
        logger.info(
            "Evaluating RogersSatchell crosses_above: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_above(vol, threshold, shift=shift)

    @classmethod
    def crosses_below(
        cls,
        vol: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if volatility crosses below threshold at shift."""
        logger.info(
            "Evaluating RogersSatchell crosses_below: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_below(vol, threshold, shift=shift)

    @classmethod
    def is_rising(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is rising between shift+1 and shift."""
        logger.info("Evaluating RogersSatchell is_rising at shift=%d", shift)
        return is_rising(vol, shift=shift)

    @classmethod
    def is_falling(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is falling between shift+1 and shift."""
        logger.info("Evaluating RogersSatchell is_falling at shift=%d", shift)
        return is_falling(vol, shift=shift)
