"""Schaff Trend Cycle (STC) Indicator Block.

Description:
    Implements Doug Schaff's Trend Cycle (STC) oscillator. STC applies a double
    smoothed Stochastic oscillator algorithm to the MACD line, providing an
    early, cycle-tuned signal of trend acceleration and exhaustion bounded in
    [0.0, 100.0]. Includes condition evaluators for levels and transitions.

Purpose:
    FEAT-SERVICES-INDICATOR-STC

Key Capabilities:
    - FR-SERVICES-STC-CALCULATE: Computes double-smoothed Stochastic MACD cycle.
    - FR-SERVICES-STC-CONDITIONS: Evaluates overbought/oversold levels and turns.

Python API Usage:
    ```python
    from app.services.indicators.schaff_trend_cycle import SchaffTrendCycle

    stc = SchaffTrendCycle.calculate(
        close, stoch_period=10, fast_period=20, slow_period=50
    )

    # Condition checks
    is_rising = SchaffTrendCycle.is_rising(stc, shift=0)
    cross_up = SchaffTrendCycle.crosses_above(stc, level=25.0, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_STC_PERIOD: int = 2
DEFAULT_STOCH_PERIOD: int = 10
DEFAULT_FAST_PERIOD: int = 20
DEFAULT_SLOW_PERIOD: int = 50
DEFAULT_FACTOR: float = 0.5


class SchaffTrendCycle(BaseIndicator):
    """Doug Schaff's Trend Cycle (STC) double-smoothed stochastic MACD indicator."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        stoch_period: int = DEFAULT_STOCH_PERIOD,
        fast_period: int = DEFAULT_FAST_PERIOD,
        slow_period: int = DEFAULT_SLOW_PERIOD,
        factor: float = DEFAULT_FACTOR,
    ) -> IndicatorSeries:
        """Compute Schaff Trend Cycle across price series.

        Args:
            price: Input price series (typically Close).
            stoch_period: Lookback window for stochastic cycles (must be >= 2).
            fast_period: Fast EMA lookback for MACD (must be >= 2).
            slow_period: Slow EMA lookback for MACD (must be > fast_period).
            factor: Smoothing factor (default 0.5).

        Returns:
            IndicatorSeries bounded in [0.0, 100.0].

        Raises:
            ValueError: If periods are invalid or series is empty.
        """
        logger.info(
            "STC calculation initiated: stoch=%d, fast=%d, slow=%d",
            stoch_period,
            fast_period,
            slow_period,
            extra={
                "stoch_period": stoch_period,
                "fast_period": fast_period,
                "slow_period": slow_period,
            },
        )
        cls._validate_params(stoch_period, fast_period, slow_period, factor)

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        stc_vals = np.zeros(n, dtype=np.float64)
        if n <= slow_period:
            return IndicatorSeries(stc_vals, name=f"STC({stoch_period})")

        macd = cls._calc_macd(p_arr, fast_period, slow_period)
        pf = cls._run_first_cycle(macd, stoch_period, slow_period, factor)
        stc_vals = cls._run_second_cycle(pf, stoch_period, slow_period, factor)

        logger.info(
            "STC calculation complete: bars=%d",
            n,
            extra={"bars": n},
        )
        return IndicatorSeries(stc_vals, name=f"STC({stoch_period})")

    @classmethod
    def _validate_params(cls, stoch: int, fast: int, slow: int, factor: float) -> None:
        if stoch < MIN_STC_PERIOD:
            raise ValueError(f"stoch_period must be >= 2, got {stoch}")
        if fast < MIN_STC_PERIOD:
            raise ValueError(f"fast_period must be >= 2, got {fast}")
        if slow <= fast:
            raise ValueError(f"slow_period ({slow}) must be > fast_period ({fast})")
        if not (0.0 < factor <= 1.0):
            raise ValueError(f"factor must be in (0.0, 1.0], got {factor}")

    @classmethod
    def _calc_macd(
        cls, p_arr: np.ndarray[Any, Any], fast: int, slow: int
    ) -> np.ndarray[Any, Any]:
        """Compute MACD difference line."""
        fast_ema = cls._calc_ema(p_arr, fast)
        slow_ema = cls._calc_ema(p_arr, slow)
        return np.asarray(fast_ema - slow_ema, dtype=np.float64)

    @staticmethod
    def _calc_ema(arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        n = len(arr)
        ema = np.zeros(n, dtype=np.float64)
        alpha = 2.0 / (period + 1.0)
        ema[0] = arr[0]
        for i in range(1, n):
            ema[i] = (alpha * arr[i]) + ((1.0 - alpha) * ema[i - 1])
        return ema

    @staticmethod
    def _run_first_cycle(
        macd: np.ndarray[Any, Any], stoch_period: int, slow_period: int, factor: float
    ) -> np.ndarray[Any, Any]:
        n = len(macd)
        frac1 = np.zeros(n, dtype=np.float64)
        pf = np.zeros(n, dtype=np.float64)

        for i in range(slow_period, n):
            start_idx = max(0, i - stoch_period + 1)
            w = macd[start_idx : i + 1]
            v_min = float(np.min(w))
            v_range = float(np.max(w)) - v_min

            frac1[i] = (
                ((macd[i] - v_min) / v_range * 100.0) if v_range > 0.0 else frac1[i - 1]
            )
            pf[i] = pf[i - 1] + (factor * (frac1[i] - pf[i - 1]))

        return pf

    @staticmethod
    def _run_second_cycle(
        pf: np.ndarray[Any, Any], stoch_period: int, slow_period: int, factor: float
    ) -> np.ndarray[Any, Any]:
        n = len(pf)
        frac2 = np.zeros(n, dtype=np.float64)
        stc = np.zeros(n, dtype=np.float64)

        for i in range(slow_period, n):
            start_idx = max(0, i - stoch_period + 1)
            w = pf[start_idx : i + 1]
            v3 = float(np.min(w))
            v4 = float(np.max(w)) - v3

            frac2[i] = ((pf[i] - v3) / v4 * 100.0) if v4 > 0.0 else frac2[i - 1]
            stc[i] = stc[i - 1] + (factor * (frac2[i] - stc[i - 1]))

        return np.clip(stc, 0.0, 100.0)

    @staticmethod
    def is_above_level(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 75.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC is strictly above level."""
        logger.info("Evaluating STC is_above_level at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        idx = len(s) - 1 - shift
        if idx < 0 or idx >= len(s) or np.isnan(s[idx]):
            return False
        return bool(s[idx] > level)

    @staticmethod
    def is_below_level(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 25.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC is strictly below level."""
        logger.info("Evaluating STC is_below_level at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        idx = len(s) - 1 - shift
        if idx < 0 or idx >= len(s) or np.isnan(s[idx]):
            return False
        return bool(s[idx] < level)

    @staticmethod
    def crosses_above(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 25.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC crossed above a threshold level."""
        logger.info("Evaluating STC crosses_above at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[prev] <= level and s[curr] > level)

    @staticmethod
    def crosses_below(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 75.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC crossed below a threshold level."""
        logger.info("Evaluating STC crosses_below at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[prev] >= level and s[curr] < level)

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if STC is rising."""
        logger.info("Evaluating STC is_rising at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] > s[prev])

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if STC is falling."""
        logger.info("Evaluating STC is_falling at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] < s[prev])
