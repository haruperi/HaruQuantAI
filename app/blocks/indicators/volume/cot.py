"""Commitment of Traders (COT) Positioning Indicator Block.

Description:
    Calculates Commitment of Traders (COT) positioning indexes and composite
    regime scores. Compresses commercial hedger and non-commercial speculator
    net positions into percentile rank indexes (CPI) and evaluates multi-window
    divergence scores bounded between -1.0 (bearish) and +1.0 (bullish).

Purpose:
    FEAT-BLOCKS-INDICATOR-COT

Key Capabilities:
    - FR-BLOCKS-COT-CALCULATE: Computes Composite Score, Hedger CPI, and Speculator CPI.
    - FR-BLOCKS-COT-CONDITIONS: Evaluates regime extremes, zero crosses, and
      trend slope.

Python API Usage:
    ```python
    from app.blocks.indicators.cot import COT

    cot_metrics = COT.calculate(
        commercial_net,
        speculator_net,
        period_fast=52,
        period_slow=156,
    )
    score = cot_metrics["composite_score"]
    cpi_hedg = cot_metrics["cpi_hedger"]

    # Condition checks
    is_bull = COT.is_bullish_regime(score, shift=0)
    is_extreme = COT.is_bullish_extreme(score, threshold=0.60, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

DEFAULT_FAST_PERIOD: int = 52
DEFAULT_SLOW_PERIOD: int = 156
MIN_COT_PERIOD: int = 2
BULLISH_EXTREME_DEFAULT: float = 0.60
BEARISH_EXTREME_DEFAULT: float = -0.60


class COT(BaseIndicator):
    """Commitment of Traders indicator computing Composite Score and CPI indexes."""

    @classmethod
    @override
    def calculate(
        cls,
        commercial_net: IndicatorSeries | np.ndarray[Any, Any],
        speculator_net: IndicatorSeries | np.ndarray[Any, Any],
        *,
        period_fast: int = DEFAULT_FAST_PERIOD,
        period_slow: int = DEFAULT_SLOW_PERIOD,
    ) -> dict[str, IndicatorSeries]:
        """Compute COT Composite Score, Hedger CPI, and Speculator CPI series.

        Formula:
            CPI(net, period) = (net[i] - min(net)) / (max(net) - min(net))
            COTScore = avg(cpi_h_fast, cpi_h_slow) - avg(cpi_s_fast, cpi_s_slow)

        Args:
            commercial_net: Commercial hedgers net positioning array.
            speculator_net: Large speculators non-commercial net positioning array.
            period_fast: Short lookback window (default 52 bars/weeks).
            period_slow: Long lookback window (default 156 bars/weeks).

        Returns:
            Dictionary containing 'composite_score', 'cpi_hedger', 'cpi_speculator',
            and 'hedger_spec_spread' IndicatorSeries.
        """
        c_arr = cls._to_numpy(commercial_net)
        s_arr = cls._to_numpy(speculator_net)
        n = min(len(c_arr), len(s_arr))

        if period_fast > period_slow:
            period_fast, period_slow = period_slow, period_fast
        period_fast = max(period_fast, MIN_COT_PERIOD)
        period_slow = max(period_slow, MIN_COT_PERIOD)

        score_out = np.full(n, np.nan, dtype=np.float64)
        cpi_hedg_out = np.full(n, np.nan, dtype=np.float64)
        cpi_spec_out = np.full(n, np.nan, dtype=np.float64)
        spread_out = np.full(n, np.nan, dtype=np.float64)

        if n < period_fast:
            logger.info(
                "FR-BLOCKS-COT-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period_fast,
            )
            return {
                "composite_score": IndicatorSeries(score_out, name="COTScore"),
                "cpi_hedger": IndicatorSeries(cpi_hedg_out, name="COTHedgerCPI"),
                "cpi_speculator": IndicatorSeries(
                    cpi_spec_out, name="COTSpeculatorCPI"
                ),
                "hedger_spec_spread": IndicatorSeries(spread_out, name="COTSpread"),
            }

        # Calculate fast and slow percentile ranks
        cpi_h_fast = cls._percent_rank_rolling(c_arr[:n], period_fast)
        cpi_s_fast = cls._percent_rank_rolling(s_arr[:n], period_fast)

        if n >= period_slow:
            cpi_h_slow = cls._percent_rank_rolling(c_arr[:n], period_slow)
            cpi_s_slow = cls._percent_rank_rolling(s_arr[:n], period_slow)
        else:
            # Fallback if series shorter than period_slow
            cpi_h_slow = cpi_h_fast
            cpi_s_slow = cpi_s_fast

        for i in range(period_fast - 1, n):
            h_slow = cpi_h_slow[i]
            s_slow = cpi_s_slow[i]
            h_val = (
                cpi_h_fast[i] if np.isnan(h_slow) else (cpi_h_fast[i] + h_slow) / 2.0
            )
            s_val = (
                cpi_s_fast[i] if np.isnan(s_slow) else (cpi_s_fast[i] + s_slow) / 2.0
            )

            cpi_hedg_out[i] = cpi_h_fast[i]
            cpi_spec_out[i] = cpi_s_fast[i]
            spread_out[i] = cpi_h_fast[i] - cpi_s_fast[i]
            score_out[i] = np.clip(h_val - s_val, -1.0, 1.0)

        logger.info(
            "FR-BLOCKS-COT-CALCULATE: Computed COT(f=%d, s=%d) for %d bars",
            period_fast,
            period_slow,
            n,
        )
        return {
            "composite_score": IndicatorSeries(score_out, name="COTScore"),
            "cpi_hedger": IndicatorSeries(cpi_hedg_out, name="COTHedgerCPI"),
            "cpi_speculator": IndicatorSeries(cpi_spec_out, name="COTSpeculatorCPI"),
            "hedger_spec_spread": IndicatorSeries(spread_out, name="COTSpread"),
        }

    @classmethod
    def _percent_rank_rolling(
        cls,
        arr: np.ndarray[Any, Any],
        period: int,
    ) -> np.ndarray[Any, Any]:
        """Compute rolling percentile rank (min-max normalization) in [0.0, 1.0]."""
        n = len(arr)
        out = np.full(n, np.nan, dtype=np.float64)
        for i in range(period - 1, n):
            window = arr[i - period + 1 : i + 1]
            w_min = float(np.min(window))
            w_max = float(np.max(window))
            diff = w_max - w_min
            if diff <= 0.0:
                out[i] = 0.5
            else:
                out[i] = np.clip((arr[i] - w_min) / diff, 0.0, 1.0)
        return out

    @classmethod
    def is_bullish_extreme(
        cls,
        score: IndicatorSeries,
        threshold: float = BULLISH_EXTREME_DEFAULT,
        shift: int = 0,
    ) -> bool:
        """Check if score is above bullish extreme threshold (default 0.60)."""
        return score.is_greater(threshold, shift=shift)

    @classmethod
    def is_bearish_extreme(
        cls,
        score: IndicatorSeries,
        threshold: float = BEARISH_EXTREME_DEFAULT,
        shift: int = 0,
    ) -> bool:
        """Check if score is below bearish extreme threshold (default -0.60)."""
        return score.is_lower(threshold, shift=shift)

    @classmethod
    def is_bullish_regime(cls, score: IndicatorSeries, shift: int = 0) -> bool:
        """Check if composite score is in positive/bullish regime (> 0.0)."""
        return score.is_greater(0.0, shift=shift)

    @classmethod
    def is_bearish_regime(cls, score: IndicatorSeries, shift: int = 0) -> bool:
        """Check if composite score is in negative/bearish regime (< 0.0)."""
        return score.is_lower(0.0, shift=shift)

    @classmethod
    def score_crosses_above_zero(cls, score: IndicatorSeries, shift: int = 0) -> bool:
        """Check if composite score crosses above zero."""
        return score.crosses_above(0.0, shift=shift)

    @classmethod
    def score_crosses_below_zero(cls, score: IndicatorSeries, shift: int = 0) -> bool:
        """Check if composite score crosses below zero."""
        return score.crosses_below(0.0, shift=shift)

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series is rising at shift compared to shift+1."""
        return series.is_rising(shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series is falling at shift compared to shift+1."""
        return series.is_falling(shift=shift)
