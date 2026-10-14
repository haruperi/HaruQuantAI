"""Triple Exponential Moving Average (TEMA) Indicator Block.

Description:
    Implements Patrick Mulloy's Triple Exponential Moving Average (TEMA) designed
    to minimize lag while maintaining smoothness by combining single, double,
    and triple exponential moving averages.
    Formula: TEMA = 3 * EMA1 - 3 * EMA2 + EMA3.

Purpose:
    FEAT-SERVICES-INDICATOR-TEMA

Key Capabilities:
    - FR-SERVICES-TEMA-CALCULATE: Computes triple smoothed moving average.
      Associated: `TEMA.calculate()`
      Logging: INFO level logging of period and bar count.
    - FR-SERVICES-TEMA-CONDITIONS: Evaluates price crossovers and directional trends.
      Associated: `TEMA.crosses_above()`, `TEMA.is_rising()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.trend.tema import TEMA

    tema = TEMA.calculate(close, period=14)
    is_up = TEMA.is_rising(tema, shift=0)
    cross_up = TEMA.crosses_above(close, tema, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_TEMA_PERIOD: int = 1
DEFAULT_TEMA_PERIOD: int = 14


class TEMA(BaseIndicator):
    """Triple Exponential Moving Average (TEMA) trend smoothing block."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_TEMA_PERIOD,
    ) -> IndicatorSeries:
        """Compute Triple Exponential Moving Average over lookback period.

        Args:
            price: Input price series (e.g. Close).
            period: Smoothing lookback period (>= 1).

        Returns:
            IndicatorSeries containing TEMA values.
        """
        logger.info("TEMA calculation initiated: period=%d", period)
        if period < MIN_TEMA_PERIOD:
            raise ValueError(f"period must be >= {MIN_TEMA_PERIOD}, got {period}")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Price array cannot be empty")

        tema_vals = cls._compute_tema(p_arr, period)
        logger.info("TEMA calculation completed: bars=%d", n)
        return IndicatorSeries(tema_vals, name=f"TEMA({period})")

    @classmethod
    def _compute_tema(
        cls, price: np.ndarray[Any, Any], period: int
    ) -> np.ndarray[Any, Any]:
        """Compute 3 * EMA1 - 3 * EMA2 + EMA3."""
        ema1 = cls._compute_ema(price, period)
        ema2 = cls._compute_ema(ema1, period)
        ema3 = cls._compute_ema(ema2, period)
        res: np.ndarray[Any, Any] = np.asarray(
            3.0 * ema1 - 3.0 * ema2 + ema3, dtype=np.float64
        )
        return res

    @staticmethod
    def _compute_ema(data: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        """Standard recursive exponential moving average."""
        n = len(data)
        ema = np.zeros(n, dtype=np.float64)
        if n == 0:
            return ema

        alpha = 2.0 / (period + 1.0)
        ema[0] = data[0]
        for i in range(1, n):
            ema[i] = alpha * data[i] + (1.0 - alpha) * ema[i - 1]
        return ema

    @classmethod
    def is_above_price(
        cls,
        tema: IndicatorSeries,
        price: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if TEMA is above price at shift."""
        logger.info("Evaluating TEMA is_above_price at shift=%d", shift)
        t_val = tema.get(shift)
        p_val = price.get(shift)
        return not np.isnan(t_val) and not np.isnan(p_val) and t_val > p_val

    @classmethod
    def is_below_price(
        cls,
        tema: IndicatorSeries,
        price: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if TEMA is below price at shift."""
        logger.info("Evaluating TEMA is_below_price at shift=%d", shift)
        t_val = tema.get(shift)
        p_val = price.get(shift)
        return not np.isnan(t_val) and not np.isnan(p_val) and t_val < p_val

    @classmethod
    def crosses_above(
        cls,
        price: IndicatorSeries,
        tema: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses above TEMA at shift."""
        logger.info("Evaluating price crosses_above TEMA at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        t_curr = tema.get(shift)
        t_prev = tema.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(t_curr) or np.isnan(t_prev):
            return False
        return bool(p_prev <= t_prev and p_curr > t_curr)

    @classmethod
    def crosses_below(
        cls,
        price: IndicatorSeries,
        tema: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if price crosses below TEMA at shift."""
        logger.info("Evaluating price crosses_below TEMA at shift=%d", shift)
        p_curr = price.get(shift)
        p_prev = price.get(shift + 1)
        t_curr = tema.get(shift)
        t_prev = tema.get(shift + 1)
        if np.isnan(p_curr) or np.isnan(p_prev) or np.isnan(t_curr) or np.isnan(t_prev):
            return False
        return bool(p_prev >= t_prev and p_curr < t_curr)

    @classmethod
    def is_rising(cls, tema: IndicatorSeries, shift: int = 0) -> bool:
        """True if TEMA is rising between shift+1 and shift."""
        logger.info("Evaluating TEMA is_rising at shift=%d", shift)
        curr = tema.get(shift)
        prev = tema.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, tema: IndicatorSeries, shift: int = 0) -> bool:
        """True if TEMA is falling between shift+1 and shift."""
        logger.info("Evaluating TEMA is_falling at shift=%d", shift)
        curr = tema.get(shift)
        prev = tema.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
