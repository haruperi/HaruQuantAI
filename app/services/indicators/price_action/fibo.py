"""Fibonacci Retracement and Expansion Indicator Block.

Description:
    Computes Fibonacci retracement and extension price levels (23.6%, 38.2%,
    50.0%, 61.8%, 78.6%, 100.0%, 161.8%) across rolling lookback swing ranges
    or session boundaries. Evaluates directional retracements based on swing
    polarity and price crossover conditions.

Purpose:
    FEAT-SERVICES-INDICATOR-FIBO

Key Capabilities:
    - FR-SERVICES-FIBO-CALCULATE: Computes standard Fibonacci retracement levels.
    - FR-SERVICES-FIBO-CONDITIONS: Evaluates penetration and crossovers of levels.

Python API Usage:
    ```python
    from app.services.indicators.price_action.fibo import Fibo

    fibo = Fibo.calculate(high, low, close, open_prices=open_p, period=20)
    level_38 = fibo["level_38_2"]
    level_61 = fibo["level_61_8"]

    # Condition checks
    is_above = Fibo.is_above_level(close, level_61, shift=0)
    cross_38 = Fibo.crosses_above(close, level_38, shift=0)
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
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_FIBO_PERIOD: int = 2
STANDARD_FIBO_LEVELS: tuple[float, ...] = (
    23.6,
    38.2,
    50.0,
    61.8,
    78.6,
    100.0,
    161.8,
)


class Fibo(BaseIndicator):
    """Fibonacci Retracement and Extension indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        open_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        period: int = 14,
        custom_level: float | None = None,
    ) -> dict[str, IndicatorSeries]:
        """Compute standard and custom Fibonacci retracement levels.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            open_prices: Optional open prices series (if None, close is used).
            period: Lookback window length in bars (must be >= 2).
            custom_level: Optional custom Fibonacci percentage level (e.g. 127.2).

        Returns:
            Dictionary mapping level keys to IndicatorSeries:
                'level_23_6', 'level_38_2', 'level_50_0', 'level_61_8',
                'level_78_6', 'level_100_0', 'level_161_8', and optionally 'custom'.

        Raises:
            ValueError: If period < 2 or series lengths mismatch.
        """
        logger.info(
            "Fibo calculation initiated with period=%d, custom_level=%s",
            period,
            str(custom_level),
            extra={"period": period, "custom_level": custom_level},
        )
        if period < MIN_FIBO_PERIOD:
            raise ValueError(f"Period must be >= 2, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        o_arr = cls.to_numpy(open_prices) if open_prices is not None else c_arr

        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not (len(h_arr) == len(l_arr) == len(o_arr) == n):
            raise ValueError("All price input series must have equal lengths")

        levels_to_calc = list(STANDARD_FIBO_LEVELS)
        if custom_level is not None and custom_level not in levels_to_calc:
            levels_to_calc.append(custom_level)

        output_arrays: dict[float, np.ndarray[Any, Any]] = {
            lvl: np.full(n, np.nan, dtype=np.float64) for lvl in levels_to_calc
        }

        for i in range(period - 1, n):
            start_idx = i - period + 1
            upper = np.max(h_arr[start_idx : i + 1])
            lower = np.min(l_arr[start_idx : i + 1])
            step = (upper - lower) / 100.0

            # Determine polarity: bullish if latest close > open at start of swing
            is_bullish = c_arr[i] >= o_arr[start_idx]

            for lvl in levels_to_calc:
                delta = lvl * step
                output_arrays[lvl][i] = (
                    (upper - delta) if is_bullish else (lower + delta)
                )

        result: dict[str, IndicatorSeries] = {}
        for lvl in STANDARD_FIBO_LEVELS:
            key = f"level_{str(lvl).replace('.', '_')}"
            result[key] = IndicatorSeries(output_arrays[lvl], name=f"Fibo({lvl}%)")

        if custom_level is not None:
            result["custom"] = IndicatorSeries(
                output_arrays[custom_level], name=f"Fibo({custom_level}%)"
            )

        logger.info(
            "Fibo calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return result

    @staticmethod
    def is_above_level(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly above a Fibonacci level."""
        logger.info(
            "Evaluating Fibo is_above_level at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return is_greater(price, level, shift=shift)

    @staticmethod
    def is_below_level(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly below a Fibonacci level."""
        logger.info(
            "Evaluating Fibo is_below_level at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return is_lower(price, level, shift=shift)

    @staticmethod
    def crosses_above(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed above a Fibonacci level."""
        logger.info(
            "Evaluating Fibo crosses_above at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_above(price, level, shift=shift)

    @staticmethod
    def crosses_below(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed below a Fibonacci level."""
        logger.info(
            "Evaluating Fibo crosses_below at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_below(price, level, shift=shift)
