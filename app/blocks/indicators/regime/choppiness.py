"""Choppiness Index Regime Indicator Block.

Description:
    Computes the Choppiness Index (CHOP) indicator measuring whether a market
    is trending (directional) or consolidating (choppy / mean-reverting).
    Formula: 100 * LOG10(Sum(TR, n) / (Max(H, n) - Min(L, n))) / LOG10(n).
    Values below lower_threshold indicate strong directional trend; values
    above upper_threshold indicate consolidation.

Purpose:
    FEAT-BLOCKS-INDICATOR-CHOPPINESS

Key Capabilities:
    - FR-BLOCKS-CHOPPINESS-CALCULATE: Computes rolling Choppiness Index series.
    - FR-BLOCKS-CHOPPINESS-CONDITIONS: Evaluates trend, chop, and transition states.

Python API Usage:
    ```python
    from app.blocks.indicators.regime.choppiness import ChoppinessIndex

    res = ChoppinessIndex.calculate(high, low, close, period=14)
    chop = res["chop"]
    regime = res["regime"]

    trending = ChoppinessIndex.is_trending(chop, lower_threshold=38.2, shift=0)
    choppy = ChoppinessIndex.is_choppy(chop, upper_threshold=61.8, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

import math
from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

REGIME_DIRECTIONAL: float = 0.0
REGIME_TRANSITION: float = 1.0
REGIME_CHOPPY: float = 2.0

MIN_CHOP_PERIOD: int = 2
DEFAULT_PERIOD: int = 14
DEFAULT_LOWER_THRESHOLD: float = 38.2
DEFAULT_UPPER_THRESHOLD: float = 61.8
DEFAULT_MID_CHOP: float = 50.0
SCALE_FACTOR: float = 100.0
EPSILON: float = 1e-12


class ChoppinessIndex(BaseIndicator):
    """Choppiness Index indicator and market trend regime classifier."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_PERIOD,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling Choppiness Index and discrete regime state series.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Lookback window (>= 2).
            lower_threshold: Threshold below which market is directional.
            upper_threshold: Threshold above which market is choppy.

        Returns:
            Dictionary with 'chop' and 'regime' IndicatorSeries.
        """
        logger.info(
            "ChoppinessIndex initiated: period=%d, lower=%.1f, upper=%.1f",
            period,
            lower_threshold,
            upper_threshold,
        )
        if period < MIN_CHOP_PERIOD:
            raise ValueError(f"period must be >= {MIN_CHOP_PERIOD}, got {period}")
        if lower_threshold >= upper_threshold:
            raise ValueError(
                "lower_threshold must be strictly less than upper_threshold"
            )

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Price arrays cannot be empty and lengths must match")

        chop_vals, regime_vals = cls._compute_chop_arrays(
            h_arr,
            l_arr,
            c_arr,
            period=period,
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )

        return {
            "chop": IndicatorSeries(chop_vals, name=f"CHOP({period})"),
            "regime": IndicatorSeries(regime_vals, name=f"CHOP_Regime({period})"),
        }

    @classmethod
    def _compute_chop_arrays(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        *,
        period: int,
        lower_threshold: float,
        upper_threshold: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Compute rolling True Range sum and log span ratios."""
        n = len(c_arr)
        chop_vals = np.full(n, DEFAULT_MID_CHOP, dtype=np.float64)
        regime_vals = np.full(n, REGIME_TRANSITION, dtype=np.float64)
        if n < period:
            return chop_vals, regime_vals

        tr = np.zeros(n, dtype=np.float64)
        tr[0] = h_arr[0] - l_arr[0]
        for i in range(1, n):
            hl = h_arr[i] - l_arr[i]
            hc = abs(h_arr[i] - c_arr[i - 1])
            lc = abs(l_arr[i] - c_arr[i - 1])
            tr[i] = max(hl, hc, lc)

        log10_period = math.log10(period)
        for i in range(period - 1, n):
            start = i - period + 1
            sum_tr = float(np.sum(tr[start : i + 1]))
            max_h = float(np.max(h_arr[start : i + 1]))
            min_l = float(np.min(l_arr[start : i + 1]))
            span = max_h - min_l

            chop = DEFAULT_MID_CHOP
            if span > EPSILON and sum_tr > 0.0:
                ratio = sum_tr / span
                if ratio > 0.0:
                    raw_chop = SCALE_FACTOR * math.log10(ratio) / log10_period
                    chop = max(0.0, min(SCALE_FACTOR, raw_chop))

            chop_vals[i] = chop
            regime_vals[i] = cls._classify_regime(
                chop, lower_threshold, upper_threshold
            )

        return chop_vals, regime_vals

    @staticmethod
    def _classify_regime(
        chop: float, lower_threshold: float, upper_threshold: float
    ) -> float:
        """Map choppiness index value to discrete regime code."""
        if chop <= lower_threshold:
            return REGIME_DIRECTIONAL
        if chop >= upper_threshold:
            return REGIME_CHOPPY
        return REGIME_TRANSITION

    @classmethod
    def is_trending(
        cls,
        chop: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is in a strong directional trend."""
        logger.info("Evaluating Choppiness is_trending at shift=%d", shift)
        val = chop.get(shift)
        return not np.isnan(val) and val <= lower_threshold

    @classmethod
    def is_choppy(
        cls,
        chop: IndicatorSeries,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is choppy / consolidating."""
        logger.info("Evaluating Choppiness is_choppy at shift=%d", shift)
        val = chop.get(shift)
        return not np.isnan(val) and val >= upper_threshold

    @classmethod
    def is_in_transition(
        cls,
        chop: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is in transition between trend and consolidation."""
        logger.info("Evaluating Choppiness is_in_transition at shift=%d", shift)
        val = chop.get(shift)
        return not np.isnan(val) and (lower_threshold < val < upper_threshold)

    @classmethod
    def crosses_above(cls, chop: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if Choppiness crosses above specified level."""
        logger.info(
            "Evaluating CHOP crosses_above level=%.2f at shift=%d", level, shift
        )
        curr = chop.get(shift)
        prev = chop.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(cls, chop: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if Choppiness crosses below specified level."""
        logger.info(
            "Evaluating CHOP crosses_below level=%.2f at shift=%d", level, shift
        )
        curr = chop.get(shift)
        prev = chop.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)
