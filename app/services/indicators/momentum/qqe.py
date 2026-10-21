"""Quantitative Qualitative Estimation (QQE) Indicator Block.

Description:
    Implements the Quantitative Qualitative Estimation (QQE) indicator,
    combining a smoothed Relative Strength Index (Value1) with a dynamic
    trailing volatility stop line (Value2) derived from Wilder's double-smoothed
    ATR of RSI. Provides condition evaluators for signal crossovers, level
    thresholds, direction changes, and slopes.

Purpose:
    FEAT-SERVICES-INDICATOR-QQE: QQE calculation and condition evaluators.

Key Capabilities:
    - FR-SERVICES-QQE-CALCULATE: Computes QQE Value1 (Fast) and Value2 (Slow).
    - FR-SERVICES-QQE-CONDITIONS: Evaluates crossovers, levels, and slopes.

Python API Usage:
    ```python
    from app.services.indicators.momentum.qqe import QQE

    qqe_res = QQE.calculate(close, rsi_period=14, sf=5, wf=4.236)
    val1 = qqe_res["value1"]
    val2 = qqe_res["value2"]

    cross_up = QQE.value1_crosses_above_value2(val1, val2, shift=0)
    is_rising = QQE.value1_is_rising(val1, shift=0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "qqe"
    ```
"""

from __future__ import annotations

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_RSI_PERIOD: int = 2
DEFAULT_RSI_PERIOD: int = 14
DEFAULT_SF: int = 5
DEFAULT_WF: float = 4.236


class QQE(BaseIndicator):
    """Quantitative Qualitative Estimation indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        rsi_period: int = DEFAULT_RSI_PERIOD,
        sf: int = DEFAULT_SF,
        wf: float = DEFAULT_WF,
    ) -> dict[str, IndicatorSeries]:
        """Compute QQE Value1 (Fast smoothed RSI) and Value2 (Slow trailing stop)."""
        logger.info(
            "QQE calculation initiated: rsi_period=%d, sf=%d, wf=%.3f",
            rsi_period,
            sf,
            wf,
            extra={"rsi_period": rsi_period, "sf": sf, "wf": wf},
        )
        if rsi_period < MIN_RSI_PERIOD:
            raise ValueError(f"rsi_period must be >= 2, got {rsi_period}")
        if sf < 1:
            raise ValueError(f"sf must be >= 1, got {sf}")
        if wf <= 0.0:
            raise ValueError(f"wf must be > 0.0, got {wf}")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        if n < rsi_period + 1:
            nan_arr = np.full(n, np.nan)
            return {
                "value1": IndicatorSeries(nan_arr, name=f"QQE1({rsi_period})"),
                "value2": IndicatorSeries(nan_arr, name=f"QQE2({rsi_period})"),
            }

        raw_rsi = cls._calc_raw_rsi(p_arr, rsi_period)
        val1 = cls._calc_ema(raw_rsi, sf)

        wilders_period = (rsi_period * 2) - 1
        atr_rsi = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            atr_rsi[i] = abs(val1[i] - val1[i - 1])

        smoothed_atr1 = cls._calc_ema(atr_rsi, wilders_period)
        smoothed_atr2 = cls._calc_ema(smoothed_atr1, wilders_period)
        dar = smoothed_atr2 * wf

        val2 = cls._calc_trailing_stop(val1, dar, rsi_period)

        logger.info(
            "QQE calculation complete: bars=%d, rsi_period=%d",
            n,
            rsi_period,
            extra={"bars": n, "rsi_period": rsi_period},
        )
        return {
            "value1": IndicatorSeries(val1, name=f"QQE_Value1({rsi_period})"),
            "value2": IndicatorSeries(val2, name=f"QQE_Value2({rsi_period})"),
        }

    @staticmethod
    def _calc_raw_rsi(p_arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        """Compute standard Wilder's RSI."""
        n = len(p_arr)
        rsi = np.full(n, 50.0, dtype=np.float64)
        diff = np.diff(p_arr)

        gains = np.maximum(diff, 0.0)
        losses = np.maximum(-diff, 0.0)

        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))

        alpha = 1.0 / period
        for i in range(period, n - 1):
            avg_gain = (alpha * gains[i]) + ((1.0 - alpha) * avg_gain)
            avg_loss = (alpha * losses[i]) + ((1.0 - alpha) * avg_loss)
            if avg_loss == 0.0:
                rsi[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    @staticmethod
    def _calc_ema(arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        """Compute Exponential Moving Average."""
        n = len(arr)
        ema = np.zeros(n, dtype=np.float64)
        if n == 0:
            return ema

        alpha = 2.0 / (period + 1.0)
        ema[0] = arr[0]
        for i in range(1, n):
            ema[i] = (alpha * arr[i]) + ((1.0 - alpha) * ema[i - 1])
        return ema

    @staticmethod
    def _calc_trailing_stop(
        val1: np.ndarray[Any, Any],
        dar: np.ndarray[Any, Any],
        start_idx: int,
    ) -> np.ndarray[Any, Any]:
        """Compute dynamic trailing stop line Value2."""
        n = len(val1)
        val2 = np.full(n, 50.0, dtype=np.float64)
        tr = 50.0

        for i in range(start_idx, n):
            dv = tr
            rsi0 = val1[i]
            rsi1 = val1[i - 1]
            curr_dar = dar[i]

            if rsi0 < tr:
                tr = rsi0 + curr_dar
                if rsi1 < dv and tr > dv:
                    tr = dv
            elif rsi0 > tr:
                tr = rsi0 - curr_dar
                if rsi1 > dv and tr < dv:
                    tr = dv

            val2[i] = tr

        return val2

    @staticmethod
    def _as_series(s: IndicatorSeries | np.ndarray[Any, Any]) -> IndicatorSeries:
        return (
            s
            if isinstance(s, IndicatorSeries)
            else IndicatorSeries(BaseIndicator.to_numpy(s))
        )

    @staticmethod
    def value1_crosses_above_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossAboveValue2."""
        logger.info("Evaluating QQE value1_crosses_above_value2 at shift=%d", shift)
        return QQE._as_series(value1).crosses_above(QQE._as_series(value2), shift)

    @staticmethod
    def value1_crosses_below_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossBelowValue2."""
        logger.info("Evaluating QQE value1_crosses_below_value2 at shift=%d", shift)
        return QQE._as_series(value1).crosses_below(QQE._as_series(value2), shift)

    @staticmethod
    def value1_higher_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1HigherValue2."""
        logger.info("Evaluating QQE value1_higher_value2 at shift=%d", shift)
        return QQE._as_series(value1).is_greater(QQE._as_series(value2), shift)

    @staticmethod
    def value1_lower_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1LowerValue2."""
        logger.info("Evaluating QQE value1_lower_value2 at shift=%d", shift)
        return QQE._as_series(value1).is_lower(QQE._as_series(value2), shift)

    @staticmethod
    def value1_is_rising(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1Rising."""
        logger.info("Evaluating QQE value1_is_rising at shift=%d", shift)
        return QQE._as_series(value1).is_rising(shift)

    @staticmethod
    def value1_is_falling(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1Falling."""
        logger.info("Evaluating QQE value1_is_falling at shift=%d", shift)
        return QQE._as_series(value1).is_falling(shift)

    @staticmethod
    def value1_changes_up(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1ChangesUp."""
        return QQE._as_series(value1).changes_up(shift)

    @staticmethod
    def value1_changes_down(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1ChangesDown."""
        return QQE._as_series(value1).changes_down(shift)

    @staticmethod
    def value1_crosses_above(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        level: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossAbove level."""
        return QQE._as_series(value1).crosses_above(level, shift)

    @staticmethod
    def value1_crosses_below(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        level: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossBelow level."""
        return QQE._as_series(value1).crosses_below(level, shift)

    @staticmethod
    def value1_is_higher(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        level: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1Higher than level."""
        return QQE._as_series(value1).is_greater(level, shift)

    @staticmethod
    def value1_is_lower(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        level: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1Lower than level."""
        return QQE._as_series(value1).is_lower(level, shift)

    @staticmethod
    def value2_is_rising(
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue2Rising."""
        return QQE._as_series(value2).is_rising(shift)

    @staticmethod
    def value2_is_falling(
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue2Falling."""
        return QQE._as_series(value2).is_falling(shift)
