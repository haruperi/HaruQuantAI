"""Trend Regime Classifier Indicator Block.

Description:
    Evaluates market macro and micro trend regimes by comparing price action
    against configurable moving average baselines (e.g. SMA-200, EMA-50).
    Provides condition evaluators for uptrend/downtrend states and transitions.

Purpose:
    FEAT-SERVICES-INDICATOR-TREND

Key Capabilities:
    - FR-SERVICES-TREND-CALCULATE: Computes trend state and baseline MA.
    - FR-SERVICES-TREND-CONDITIONS: Evaluates active uptrend/downtrend states.

Python API Usage:
    ```python
    from app.services.indicators.trend.trend import Trend

    res = Trend.calculate(close, period=200, method="sma")
    trend = res["trend"]
    baseline = res["baseline"]

    # Condition checks
    is_up = Trend.is_uptrend(close, baseline, shift=0)
    is_down = Trend.is_downtrend(close, baseline, shift=0)
    turns_up = Trend.turns_uptrend(close, baseline, shift=0)
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


class Trend(BaseIndicator):
    """Trend regime classifier evaluating price position relative to baseline."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        period: int = 200,
        method: str = "sma",
    ) -> dict[str, IndicatorSeries]:
        """Compute trend regime state and baseline moving average.

        Args:
            price: Input price series (typically Close).
            period: Baseline smoothing period (default 200).
            method: Smoothing method ('sma' or 'ema').

        Returns:
            Dictionary containing:
                - 'trend': 1.0 for Uptrend, -1.0 for Downtrend.
                - 'baseline': Moving average baseline series.

        Raises:
            ValueError: If period < 1, unknown method, or series is empty.
        """
        logger.info(
            "Trend calculation initiated with period=%d, method=%s",
            period,
            method,
            extra={"period": period, "method": method},
        )
        if period < 1:
            raise ValueError(f"Period must be >= 1, got {period}")

        clean_method = method.strip().lower()
        if clean_method not in ("sma", "ema"):
            raise ValueError(f"Unsupported method '{method}'; choose 'sma' or 'ema'")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        if n < period:
            return {
                "trend": IndicatorSeries(np.zeros(n), name=f"Trend({period})"),
                "baseline": IndicatorSeries(
                    np.full(n, np.nan), name=f"TrendBaseline({period})"
                ),
            }

        baseline_vals = cls._compute_baseline(p_arr, period, clean_method)
        trend_vals = cls._classify_trend(p_arr, baseline_vals, period)

        logger.info(
            "Trend calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )

        return {
            "trend": IndicatorSeries(trend_vals, name=f"Trend({period})"),
            "baseline": IndicatorSeries(baseline_vals, name=f"TrendBaseline({period})"),
        }

    @staticmethod
    def _compute_baseline(
        p_arr: np.ndarray[Any, Any],
        period: int,
        method: str,
    ) -> np.ndarray[Any, Any]:
        """Compute moving average baseline values."""
        n = len(p_arr)
        baseline = np.full(n, np.nan, dtype=np.float64)

        if method == "sma":
            for i in range(period - 1, n):
                baseline[i] = np.mean(p_arr[i - period + 1 : i + 1])
        else:
            alpha = 2.0 / (period + 1.0)
            baseline[period - 1] = np.mean(p_arr[:period])
            for i in range(period, n):
                baseline[i] = (alpha * p_arr[i]) + ((1.0 - alpha) * baseline[i - 1])

        return baseline

    @staticmethod
    def _classify_trend(
        p_arr: np.ndarray[Any, Any],
        baseline: np.ndarray[Any, Any],
        period: int,
    ) -> np.ndarray[Any, Any]:
        """Classify trend state based on price vs baseline position."""
        n = len(p_arr)
        trend = np.zeros(n, dtype=np.float64)

        for i in range(period - 1, n):
            base_val = baseline[i]
            if np.isnan(base_val):
                continue
            if p_arr[i] > base_val:
                trend[i] = 1.0
            elif p_arr[i] < base_val:
                trend[i] = -1.0

        return trend

    @staticmethod
    def is_uptrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly above the baseline (Uptrend).

        Formula:
            price[shift] > baseline[shift]
        """
        logger.info(
            "Evaluating Trend is_uptrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(price, baseline, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def is_downtrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly below the baseline (Downtrend).

        Formula:
            price[shift] < baseline[shift]
        """
        logger.info(
            "Evaluating Trend is_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(price, baseline, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def turns_uptrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed from below or equal baseline to above baseline."""
        logger.info(
            "Evaluating Trend turns_uptrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return crosses_above(price, baseline, shift=shift, round_digits=8)

    @staticmethod
    def turns_downtrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed from above or equal baseline to below baseline."""
        logger.info(
            "Evaluating Trend turns_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return crosses_below(price, baseline, shift=shift, round_digits=8)
