"""Commitment of Traders (COT) Positioning Indicator Block.

Description:
    Calculates Commitment of Traders (COT) positioning indexes, cross-field
    spreads, multi-field combinations, momentum series, and composite regime
    scores. Compresses commercial hedger, large speculator, and small speculator
    net positions into percentile rank indexes (CPI/CTI) and evaluates all
    multi-window divergence, accumulation, crowding unwind, exhaustion,
    seasonal, Z-score, and regime shift conditions.

Purpose:
    FEAT-SERVICES-INDICATOR-COT: COT positioning indexes and condition blocks.

Key Capabilities:
    - FR-SERVICES-COT-CALCULATE: Computes Composite Score, Hedger/Speculator/Small
      CPI/CTI, cross-field spreads, momentum, and multi-field combos.
    - FR-SERVICES-COT-CONDITIONS: Evaluates regime extremes, zero crosses, shifts,
      accumulation, crowding unwinds, Z-score spreads, and seasonal divergences.

Python API Usage:
    ```python
    from app.services.indicators.volume.cot import COT

    cot_metrics = COT.calculate(
        commercial_net,
        speculator_net,
        period_fast=52,
        period_slow=156,
    )
    score = cot_metrics["composite_score"]
    cpi_hedg = cot_metrics["cpi_hedger"]
    is_bull = COT.is_bullish_regime(score, shift=0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "cot"
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_FAST_PERIOD: int = 52
DEFAULT_SLOW_PERIOD: int = 156
MIN_COT_PERIOD: int = 2
BULLISH_EXTREME_DEFAULT: float = 0.60
BEARISH_EXTREME_DEFAULT: float = -0.60

type _SeriesInput = IndicatorSeries | Sequence[float] | np.ndarray[Any, Any]

_COT_SERIES_NAMES: dict[str, str] = {
    "composite_score": "COTScore",
    "cpi_hedger": "COTHedgerCPI",
    "cpi_speculator": "COTSpeculatorCPI",
    "cpi_small": "COTSmallCPI",
    "cpi_hedger_slow": "COTHedgerSlowCPI",
    "cpi_speculator_slow": "COTSpeculatorSlowCPI",
    "cti_hedger": "COTHedgerCTI",
    "cti_speculator": "COTSpeculatorCTI",
    "hedger_spec_spread": "COTSpread",
}


class COT(BaseIndicator):
    """Commitment of Traders indicator computing CPI/CTI, scores, and conditions."""

    @classmethod
    @override
    def calculate(
        cls,
        commercial_net: _SeriesInput,
        speculator_net: _SeriesInput,
        *,
        small_spec_net: _SeriesInput | None = None,
        open_interest: _SeriesInput | None = None,
        period_fast: int = DEFAULT_FAST_PERIOD,
        period_slow: int = DEFAULT_SLOW_PERIOD,
    ) -> dict[str, IndicatorSeries]:
        """Compute COT Composite Score, CPI/CTI series, and hedger-spec spreads."""
        c_arr = cls.to_numpy(commercial_net)
        s_arr = cls.to_numpy(speculator_net)
        n = min(len(c_arr), len(s_arr))
        sm_arr = (
            cls.to_numpy(small_spec_net)
            if small_spec_net is not None
            else -(c_arr[:n] + s_arr[:n])
        )
        n = min(n, len(sm_arr))
        oi_arr = (
            np.maximum(cls.to_numpy(open_interest)[:n], 1e-9)
            if open_interest is not None
            else np.maximum(np.abs(c_arr[:n]) + np.abs(s_arr[:n]) + 1.0, 1.0)
        )

        if period_fast > period_slow:
            period_fast, period_slow = period_slow, period_fast
        period_fast = max(period_fast, MIN_COT_PERIOD)
        period_slow = max(period_slow, MIN_COT_PERIOD)
        arrays = {k: np.full(n, np.nan, dtype=np.float64) for k in _COT_SERIES_NAMES}

        if n < period_fast:
            logger.info(
                "FR-SERVICES-COT-CALCULATE: Insufficient bars (%d < %d)", n, period_fast
            )
            return {
                k: IndicatorSeries(arrays[k], name=v)
                for k, v in _COT_SERIES_NAMES.items()
            }

        cpi_h_fast = cls._percent_rank_rolling(c_arr[:n], period_fast)
        cpi_s_fast = cls._percent_rank_rolling(s_arr[:n], period_fast)
        cpi_sm_fast = cls._percent_rank_rolling(sm_arr[:n], period_fast)
        cti_h = cls._percent_rank_rolling(c_arr[:n] / oi_arr, period_fast)
        cti_s = cls._percent_rank_rolling(s_arr[:n] / oi_arr, period_fast)
        cpi_h_slow = (
            cls._percent_rank_rolling(c_arr[:n], period_slow)
            if n >= period_slow
            else cpi_h_fast.copy()
        )
        cpi_s_slow = (
            cls._percent_rank_rolling(s_arr[:n], period_slow)
            if n >= period_slow
            else cpi_s_fast.copy()
        )

        for i in range(period_fast - 1, n):
            h_slow = cpi_h_slow[i] if not np.isnan(cpi_h_slow[i]) else cpi_h_fast[i]
            s_slow = cpi_s_slow[i] if not np.isnan(cpi_s_slow[i]) else cpi_s_fast[i]
            arrays["cpi_hedger"][i] = cpi_h_fast[i]
            arrays["cpi_speculator"][i] = cpi_s_fast[i]
            arrays["cpi_small"][i] = cpi_sm_fast[i]
            arrays["cpi_hedger_slow"][i] = h_slow
            arrays["cpi_speculator_slow"][i] = s_slow
            arrays["cti_hedger"][i] = cti_h[i]
            arrays["cti_speculator"][i] = cti_s[i]
            arrays["hedger_spec_spread"][i] = cpi_h_fast[i] - cpi_s_fast[i]
            arrays["composite_score"][i] = np.clip(
                (cpi_h_fast[i] + h_slow - cpi_s_fast[i] - s_slow) / 2.0, -1.0, 1.0
            )

        logger.info(
            "FR-SERVICES-COT-CALCULATE: Computed COT(f=%d, s=%d) for %d bars",
            period_fast,
            period_slow,
            n,
        )
        return {
            k: IndicatorSeries(arrays[k], name=v) for k, v in _COT_SERIES_NAMES.items()
        }

    @classmethod
    def _percent_rank_rolling(
        cls, arr: np.ndarray[Any, Any], period: int
    ) -> np.ndarray[Any, Any]:
        """Compute rolling percentile rank (min-max normalization) in [0.0, 1.0]."""
        n = len(arr)
        out = np.full(n, np.nan, dtype=np.float64)
        for i in range(period - 1, n):
            window = arr[i - period + 1 : i + 1]
            w_min, w_max = float(np.min(window)), float(np.max(window))
            diff = w_max - w_min
            out[i] = (
                0.5
                if diff <= 0.0
                else float(np.clip((arr[i] - w_min) / diff, 0.0, 1.0))
            )
        return out

    @staticmethod
    def _as_series(s: _SeriesInput) -> IndicatorSeries:
        return s if isinstance(s, IndicatorSeries) else IndicatorSeries(s)

    @classmethod
    def field_value(cls, series: _SeriesInput, shift: int = 0) -> float:
        """Evaluate COTFieldValue / COTCpi* / COTCti* at shift."""
        val = cls._as_series(series).get(shift)
        return 0.0 if np.isnan(val) else float(val)

    @classmethod
    def cross_field_spread(
        cls, field1: _SeriesInput, field2: _SeriesInput, shift: int = 0
    ) -> float:
        """Evaluate COTCrossFieldSpread (`field1[shift] - field2[shift]`)."""
        v1, v2 = cls._as_series(field1).get(shift), cls._as_series(field2).get(shift)
        return 0.0 if (np.isnan(v1) or np.isnan(v2)) else float(v1 - v2)

    @classmethod
    def momentum(cls, series: _SeriesInput, lookback: int = 4, shift: int = 0) -> float:
        """Evaluate COTMomentum (`series[shift] - series[shift + lookback]`)."""
        s = cls._as_series(series)
        v0, v1 = s.get(shift), s.get(shift + lookback)
        return 0.0 if (np.isnan(v0) or np.isnan(v1)) else float(v0 - v1)

    @classmethod
    def multi_field_combo(
        cls,
        cpi_hedg: _SeriesInput | None = None,
        cpi_spec: _SeriesInput | None = None,
        cpi_small: _SeriesInput | None = None,
        cti_spec: _SeriesInput | None = None,
        shift: int = 0,
    ) -> float:
        """Evaluate COTMultiFieldCombo (`mean(cpi_hedg, 1 - others)`)."""
        vals: list[float] = []
        if cpi_hedg is not None and not np.isnan(
            vh := cls._as_series(cpi_hedg).get(shift)
        ):
            vals.append(float(vh))
        vals.extend(
            1.0 - float(vi)
            for inv in (cpi_spec, cpi_small, cti_spec)
            if inv is not None and not np.isnan(vi := cls._as_series(inv).get(shift))
        )
        return float(sum(vals) / len(vals)) if vals else 0.5

    # Universal & composite score conditions
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
        """Evaluate COTScoreZeroCrossUp (`score` crosses above `0.0`)."""
        return score.crosses_above(0.0, shift=shift)

    @classmethod
    def score_crosses_below_zero(cls, score: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate COTScoreZeroCrossDown (`score` crosses below `0.0`)."""
        return score.crosses_below(0.0, shift=shift)

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series is rising at shift compared to shift+1."""
        return series.is_rising(shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series is falling at shift compared to shift+1."""
        return series.is_falling(shift=shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series turns upward at shift."""
        return series.changes_up(shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if series turns downward at shift."""
        return series.changes_down(shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if series crosses above level at shift."""
        return series.crosses_above(level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Check if series crosses below level at shift."""
        return series.crosses_below(level, shift=shift)

    @classmethod
    def is_higher(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Check if series is higher than level at shift."""
        return series.is_greater(level, shift=shift)

    @classmethod
    def is_lower(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Check if series is lower than level at shift."""
        return series.is_lower(level, shift=shift)

    # Specialized COT block conditions
    @classmethod
    def shift_52_vs_156_bullish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        shift_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COT52vs156ShiftBullish (`hedg52 - hedg156 > thr`)."""
        v = [x.get(shift) for x in (hedg52, spec52, hedg156, spec156)]
        if any(np.isnan(x) for x in v):
            return False
        return (v[0] - v[2]) > shift_threshold and (v[1] - v[3]) < -shift_threshold

    @classmethod
    def shift_52_vs_156_bearish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        shift_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COT52vs156ShiftBearish (`hedg52 - hedg156 < -thr`)."""
        v = [x.get(shift) for x in (hedg52, spec52, hedg156, spec156)]
        if any(np.isnan(x) for x in v):
            return False
        return (v[0] - v[2]) < -shift_threshold and (v[1] - v[3]) > shift_threshold

    @classmethod
    def accumulation_bullish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        min_weeks: int = 3,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTAccumulationBullish (hedgers up and speculators down)."""
        return min_weeks > 0 and all(
            hedg52.is_rising(shift + i) and spec52.is_falling(shift + i)
            for i in range(min_weeks)
        )

    @classmethod
    def accumulation_bearish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        min_weeks: int = 3,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTAccumulationBearish (hedgers down and speculators up)."""
        return min_weeks > 0 and all(
            hedg52.is_falling(shift + i) and spec52.is_rising(shift + i)
            for i in range(min_weeks)
        )

    @classmethod
    def extreme_bullish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedger_threshold: float = 0.80,
        spec_threshold: float = 0.20,
        *,
        hedg156: IndicatorSeries | None = None,
        spec156: IndicatorSeries | None = None,
        hedger156_threshold: float = 0.70,
        spec156_threshold: float = 0.30,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTBullishExtreme across 52w and optional 156w CPI."""
        if not (
            hedg52.is_greater(hedger_threshold, shift)
            and spec52.is_lower(spec_threshold, shift)
        ):
            return False
        if hedg156 is not None and spec156 is not None:
            return hedg156.is_greater(hedger156_threshold, shift) and spec156.is_lower(
                spec156_threshold, shift
            )
        return True

    @classmethod
    def extreme_bearish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedger_threshold: float = 0.20,
        spec_threshold: float = 0.80,
        *,
        hedg156: IndicatorSeries | None = None,
        spec156: IndicatorSeries | None = None,
        hedger156_threshold: float = 0.30,
        spec156_threshold: float = 0.70,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTBearishExtreme across 52w and optional 156w CPI."""
        if not (
            hedg52.is_lower(hedger_threshold, shift)
            and spec52.is_greater(spec_threshold, shift)
        ):
            return False
        if hedg156 is not None and spec156 is not None:
            return hedg156.is_lower(hedger156_threshold, shift) and spec156.is_greater(
                spec156_threshold, shift
            )
        return True

    @classmethod
    def convergence(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        convergence_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTConvergence (`abs(hedg52 - spec52) < convergence_threshold`)."""
        h, s = hedg52.get(shift), spec52.get(shift)
        return not (np.isnan(h) or np.isnan(s)) and abs(h - s) < convergence_threshold

    @classmethod
    def crowding_unwind(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        direction: int = 1,
        spec_extreme: float = 0.85,
        hedger_opposing: float = 0.30,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTCrowdingUnwind."""
        s0, s1, h0 = spec52.get(shift), spec52.get(shift + 1), hedg52.get(shift)
        if any(np.isnan(x) for x in (s0, s1, h0)):
            return False
        if direction > 0:
            return s1 > spec_extreme and s0 < s1 and h0 < hedger_opposing
        return s1 < (1.0 - spec_extreme) and s0 > s1 and h0 > (1.0 - hedger_opposing)

    @classmethod
    def extreme_exit_bullish(
        cls,
        hedg52: IndicatorSeries,
        extreme_threshold: float = 0.85,
        exit_threshold: float = 0.70,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTExtremeExitBullish."""
        return hedg52.is_lower(exit_threshold, shift) and any(
            hedg52.is_greater(extreme_threshold, shift + i)
            for i in range(1, lookback_weeks + 1)
        )

    @classmethod
    def extreme_exit_bearish(
        cls,
        spec52: IndicatorSeries,
        extreme_threshold: float = 0.85,
        exit_threshold: float = 0.70,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTExtremeExitBearish."""
        return spec52.is_lower(exit_threshold, shift) and any(
            spec52.is_greater(extreme_threshold, shift + i)
            for i in range(1, lookback_weeks + 1)
        )

    @classmethod
    def extreme_persistence(
        cls,
        series: IndicatorSeries,
        extreme_threshold: float = 0.80,
        min_weeks: int = 3,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTExtremePersistence."""
        return min_weeks > 0 and all(
            not np.isnan(v := series.get(shift + i)) and v >= extreme_threshold
            for i in range(min_weeks)
        )

    @classmethod
    def extreme_unwind_bullish(
        cls,
        spec52: IndicatorSeries,
        crowded_threshold: float = 0.85,
        normalize_threshold: float = 0.75,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTExtremeUnwindBullish."""
        return (
            spec52.is_lower(normalize_threshold, shift)
            and spec52.is_falling(shift)
            and any(
                spec52.is_greater(crowded_threshold, shift + i)
                for i in range(1, lookback_weeks + 1)
            )
        )

    @classmethod
    def extreme_unwind_bearish(
        cls,
        hedg52: IndicatorSeries,
        crowded_threshold: float = 0.85,
        normalize_threshold: float = 0.75,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTExtremeUnwindBearish."""
        return (
            hedg52.is_lower(normalize_threshold, shift)
            and hedg52.is_falling(shift)
            and any(
                hedg52.is_greater(crowded_threshold, shift + i)
                for i in range(1, lookback_weeks + 1)
            )
        )

    @classmethod
    def full_cycle_long(
        cls, hedg: IndicatorSeries, entry_level: float = 0.80, shift: int = 0
    ) -> bool:
        """Evaluate COTFullCycleLong (`hedg[s+1] < entry_level <= hedg[s]`)."""
        c0, c1 = hedg.get(shift), hedg.get(shift + 1)
        return not (np.isnan(c0) or np.isnan(c1)) and c1 < entry_level <= c0

    @classmethod
    def full_cycle_short(
        cls, hedg: IndicatorSeries, entry_level: float = 0.20, shift: int = 0
    ) -> bool:
        """Evaluate COTFullCycleShort (`hedg[s+1] > entry_level >= hedg[s]`)."""
        c0, c1 = hedg.get(shift), hedg.get(shift + 1)
        return not (np.isnan(c0) or np.isnan(c1)) and c1 > entry_level >= c0

    @classmethod
    def full_cycle_exit_long(
        cls, hedg: IndicatorSeries, exit_level: float = 0.50, shift: int = 0
    ) -> bool:
        """Evaluate COTFullCycleExitLong (`hedg[shift] >= exit_level`)."""
        c0 = hedg.get(shift)
        return not np.isnan(c0) and c0 >= exit_level

    @classmethod
    def full_cycle_exit_short(
        cls, hedg: IndicatorSeries, exit_level: float = 0.50, shift: int = 0
    ) -> bool:
        """Evaluate COTFullCycleExitShort (`hedg[shift] <= exit_level`)."""
        c0 = hedg.get(shift)
        return not np.isnan(c0) and c0 <= exit_level

    @classmethod
    def hedger_accel_bullish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        accel_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTHedgerAccelBullish."""
        return cls.shift_52_vs_156_bullish(
            hedg52, spec52, hedg156, spec156, accel_threshold, shift
        )

    @classmethod
    def hedger_accel_bearish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        accel_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTHedgerAccelBearish."""
        return cls.shift_52_vs_156_bearish(
            hedg52, spec52, hedg156, spec156, accel_threshold, shift
        )

    @classmethod
    def hedger_div_conf_bullish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedger_threshold: float = 0.75,
        spec_threshold: float = 0.25,
        mom_lookback: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTHedgerDivConfBullish."""
        return (
            hedg52.is_greater(hedger_threshold, shift)
            and spec52.is_lower(spec_threshold, shift)
            and hedg52.is_higher(mom_lookback, shift)
        )

    @classmethod
    def hedger_div_conf_bearish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedger_threshold: float = 0.25,
        spec_threshold: float = 0.75,
        mom_lookback: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTHedgerDivConfBearish."""
        h0, hp = hedg52.get(shift), hedg52.get(shift + mom_lookback)
        return (
            not (np.isnan(h0) or np.isnan(hp))
            and h0 < hedger_threshold
            and spec52.is_greater(spec_threshold, shift)
            and h0 < hp
        )

    @classmethod
    def higher_low(
        cls,
        score: IndicatorSeries,
        short_window: int = 4,
        long_window: int = 12,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTHigherLow (`short_min > long_min and long_min < 0`)."""
        if short_window <= 0 or long_window <= short_window:
            return False
        vals = [score.get(shift + i) for i in range(long_window)]
        if any(np.isnan(x) for x in vals):
            return False
        s_min, l_min = min(vals[:short_window]), min(vals[short_window:])
        return s_min > l_min and l_min < 0.0

    @classmethod
    def lower_high(
        cls,
        score: IndicatorSeries,
        short_window: int = 4,
        long_window: int = 12,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTLowerHigh (`short_max < long_max and long_max > 0`)."""
        if short_window <= 0 or long_window <= short_window:
            return False
        vals = [score.get(shift + i) for i in range(long_window)]
        if any(np.isnan(x) for x in vals):
            return False
        s_max, l_max = max(vals[:short_window]), max(vals[short_window:])
        return s_max < l_max and l_max > 0.0

    @staticmethod
    def _mom_pair(
        score: IndicatorSeries, mom_period: int, shift: int
    ) -> tuple[float, float] | None:
        v = [
            score.get(shift),
            score.get(shift + mom_period),
            score.get(shift + 1),
            score.get(shift + 1 + mom_period),
        ]
        return None if any(np.isnan(x) for x in v) else (v[0] - v[1], v[2] - v[3])

    @classmethod
    def momentum_rev_bullish(
        cls, score: IndicatorSeries, mom_period: int = 4, shift: int = 0
    ) -> bool:
        """Evaluate COTMomentumRevBullish (`mom_now > 0 and mom_prev <= 0`)."""
        mp = cls._mom_pair(score, mom_period, shift)
        return mp is not None and mp[0] > 0.0 and mp[1] <= 0.0

    @classmethod
    def momentum_rev_bearish(
        cls, score: IndicatorSeries, mom_period: int = 4, shift: int = 0
    ) -> bool:
        """Evaluate COTMomentumRevBearish (`mom_now < 0 and mom_prev >= 0`)."""
        mp = cls._mom_pair(score, mom_period, shift)
        return mp is not None and mp[0] < 0.0 and mp[1] >= 0.0

    @classmethod
    def multi_window_bullish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        hedger_threshold: float = 0.75,
        hedger156_threshold: float = 0.70,
        spec_threshold: float = 0.25,
        spec156_threshold: float = 0.30,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTMultiWindowBullish."""
        return cls.extreme_bullish(
            hedg52,
            spec52,
            hedger_threshold,
            spec_threshold,
            hedg156=hedg156,
            spec156=spec156,
            hedger156_threshold=hedger156_threshold,
            spec156_threshold=spec156_threshold,
            shift=shift,
        )

    @classmethod
    def multi_window_bearish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        hedg156: IndicatorSeries,
        spec156: IndicatorSeries,
        hedger_threshold: float = 0.25,
        hedger156_threshold: float = 0.30,
        spec_threshold: float = 0.75,
        spec156_threshold: float = 0.70,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTMultiWindowBearish."""
        return cls.extreme_bearish(
            hedg52,
            spec52,
            hedger_threshold,
            spec_threshold,
            hedg156=hedg156,
            spec156=spec156,
            hedger156_threshold=hedger156_threshold,
            spec156_threshold=spec156_threshold,
            shift=shift,
        )

    @classmethod
    def neutral_zone(
        cls, score: IndicatorSeries, neutral_band: float = 0.15, shift: int = 0
    ) -> bool:
        """Evaluate COTNeutralZone (`abs(score[shift]) < neutral_band`)."""
        v = score.get(shift)
        return not np.isnan(v) and abs(v) < neutral_band

    @classmethod
    def regime_shift_bullish(
        cls, score: IndicatorSeries, shift_weeks: int = 4, shift: int = 0
    ) -> bool:
        """Evaluate COTRegimeShiftBullish (`short_avg > long_avg and short_avg > 0`)."""
        if shift_weeks <= 0:
            return False
        vals = [score.get(shift + k) for k in range(shift_weeks * 3)]
        if any(np.isnan(x) for x in vals):
            return False
        s_avg, l_avg = sum(vals[:shift_weeks]) / shift_weeks, sum(vals) / len(vals)
        return s_avg > l_avg and s_avg > 0.0

    @classmethod
    def regime_shift_bearish(
        cls, score: IndicatorSeries, shift_weeks: int = 4, shift: int = 0
    ) -> bool:
        """Evaluate COTRegimeShiftBearish (`short_avg < long_avg and short_avg < 0`)."""
        if shift_weeks <= 0:
            return False
        vals = [score.get(shift + k) for k in range(shift_weeks * 3)]
        if any(np.isnan(x) for x in vals):
            return False
        s_avg, l_avg = sum(vals[:shift_weeks]) / shift_weeks, sum(vals) / len(vals)
        return s_avg < l_avg and s_avg < 0.0

    @classmethod
    def roc_bullish(
        cls,
        score: IndicatorSeries,
        roc_period: int = 4,
        roc_threshold: float = 0.20,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTRocBullish (`score[shift] - score[s + period] > threshold`)."""
        s0, sp = score.get(shift), score.get(shift + roc_period)
        return not (np.isnan(s0) or np.isnan(sp)) and (s0 - sp) > roc_threshold

    @classmethod
    def roc_bearish(
        cls,
        score: IndicatorSeries,
        roc_period: int = 4,
        roc_threshold: float = 0.20,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTRocBearish (`score[shift] - score[s + period] < -threshold`)."""
        s0, sp = score.get(shift), score.get(shift + roc_period)
        return not (np.isnan(s0) or np.isnan(sp)) and (s0 - sp) < -roc_threshold

    @classmethod
    def score_above(
        cls, score: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate COTScoreAbove (`score[shift] > level`)."""
        return score.is_greater(level, shift=shift)

    @classmethod
    def score_below(
        cls, score: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate COTScoreBelow (`score[shift] < level`)."""
        return score.is_lower(level, shift=shift)

    @classmethod
    def score_accel_bullish(
        cls,
        score: IndicatorSeries,
        mom_period: int = 4,
        momentum_threshold: float = 0.05,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTScoreAccelBullish (`mom_now > mom_prev and mom_now > thr`)."""
        mp = cls._mom_pair(score, mom_period, shift)
        return mp is not None and mp[0] > mp[1] and mp[0] > momentum_threshold

    @classmethod
    def score_accel_bearish(
        cls,
        score: IndicatorSeries,
        mom_period: int = 4,
        momentum_threshold: float = -0.05,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTScoreAccelBearish (`mom_now < mom_prev and mom_now < thr`)."""
        mp = cls._mom_pair(score, mom_period, shift)
        return mp is not None and mp[0] < mp[1] and mp[0] < momentum_threshold

    @classmethod
    def score_momentum_above(
        cls,
        score: IndicatorSeries,
        momentum_lookback: int = 4,
        momentum_threshold: float = 0.10,
        level_threshold: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTScoreMomentumAbove."""
        return cls.roc_bullish(
            score, momentum_lookback, momentum_threshold, shift
        ) and score.is_greater(level_threshold, shift)

    @classmethod
    def score_momentum_below(
        cls,
        score: IndicatorSeries,
        momentum_lookback: int = 4,
        momentum_threshold: float = 0.10,
        level_threshold: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTScoreMomentumBelow."""
        return cls.roc_bearish(
            score, momentum_lookback, momentum_threshold, shift
        ) and score.is_lower(level_threshold, shift)

    @classmethod
    def seasonal_bullish(
        cls,
        hedg52: IndicatorSeries,
        seasonal_lookback: int = 12,
        seasonal_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSeasonalBullish (`current > avg(past) + seasonal_threshold`)."""
        if seasonal_lookback <= 0:
            return False
        cur = hedg52.get(shift)
        past = [hedg52.get(shift + i) for i in range(1, seasonal_lookback + 1)]
        return not (np.isnan(cur) or any(np.isnan(x) for x in past)) and (
            cur > (sum(past) / seasonal_lookback) + seasonal_threshold
        )

    @classmethod
    def seasonal_bearish(
        cls,
        hedg52: IndicatorSeries,
        seasonal_lookback: int = 12,
        seasonal_threshold: float = 0.15,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSeasonalBearish (`current < avg(past) - seasonal_threshold`)."""
        if seasonal_lookback <= 0:
            return False
        cur = hedg52.get(shift)
        past = [hedg52.get(shift + i) for i in range(1, seasonal_lookback + 1)]
        return not (np.isnan(cur) or any(np.isnan(x) for x in past)) and (
            cur < (sum(past) / seasonal_lookback) - seasonal_threshold
        )

    @classmethod
    def small_fade_bullish(
        cls, small52: IndicatorSeries, small_threshold: float = 0.20, shift: int = 0
    ) -> bool:
        """Evaluate COTSmallFadeBullish (`small52[shift] < small_threshold`)."""
        return small52.is_lower(small_threshold, shift=shift)

    @classmethod
    def small_fade_bearish(
        cls, small52: IndicatorSeries, small_threshold: float = 0.80, shift: int = 0
    ) -> bool:
        """Evaluate COTSmallFadeBearish (`small52[shift] > small_threshold`)."""
        return small52.is_greater(small_threshold, shift=shift)

    @classmethod
    def smart_dumb_bullish(
        cls,
        hedg52: IndicatorSeries,
        small52: IndicatorSeries,
        hedger_threshold: float = 0.75,
        small_threshold: float = 0.25,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSmartDumbBullish (`hedg52 > hedger_thr and small52 < thr`)."""
        return hedg52.is_greater(hedger_threshold, shift) and small52.is_lower(
            small_threshold, shift
        )

    @classmethod
    def smart_dumb_bearish(
        cls,
        hedg52: IndicatorSeries,
        small52: IndicatorSeries,
        hedger_threshold: float = 0.25,
        small_threshold: float = 0.75,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSmartDumbBearish (`hedg52 < hedger_thr and small52 > thr`)."""
        return hedg52.is_lower(hedger_threshold, shift) and small52.is_greater(
            small_threshold, shift
        )

    @classmethod
    def spec_exhaustion_long(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        spec_extreme: float = 0.90,
        hedger_threshold: float = 0.70,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpecExhaustionLong."""
        return (
            spec52.is_rising(shift)
            and hedg52.is_greater(hedger_threshold, shift)
            and any(
                spec52.is_lower(1.0 - spec_extreme, shift + i)
                for i in range(1, lookback_weeks + 1)
            )
        )

    @classmethod
    def spec_exhaustion_short(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        spec_extreme: float = 0.90,
        hedger_threshold: float = 0.30,
        lookback_weeks: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpecExhaustionShort."""
        return (
            spec52.is_falling(shift)
            and hedg52.is_lower(hedger_threshold, shift)
            and any(
                spec52.is_greater(spec_extreme, shift + i)
                for i in range(1, lookback_weeks + 1)
            )
        )

    @classmethod
    def spec_trend_long(  # noqa: PLR0917
        cls,
        spec52: IndicatorSeries,
        spec156: IndicatorSeries,
        spec_min: float = 0.50,
        spec_max: float = 0.85,
        spec156_threshold: float = 0.50,
        lookback: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpecTrendLong."""
        s0 = spec52.get(shift)
        return (
            not np.isnan(s0)
            and spec_min < s0 < spec_max
            and spec156.is_greater(spec156_threshold, shift)
            and spec52.is_higher(lookback, shift)
        )

    @classmethod
    def spec_trend_short(  # noqa: PLR0917
        cls,
        spec52: IndicatorSeries,
        spec156: IndicatorSeries,
        spec_min: float = 0.15,
        spec_max: float = 0.50,
        spec156_threshold: float = 0.50,
        lookback: int = 4,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpecTrendShort."""
        s0, sp = spec52.get(shift), spec52.get(shift + lookback)
        return (
            not (np.isnan(s0) or np.isnan(sp))
            and spec_min < s0 < spec_max
            and spec156.is_lower(spec156_threshold, shift)
            and s0 < sp
        )

    @staticmethod
    def _spread_zscore(
        hedg52: IndicatorSeries, spec52: IndicatorSeries, period: int, shift: int
    ) -> float | None:
        if period <= 1:
            return None
        sp = [hedg52.get(shift + i) - spec52.get(shift + i) for i in range(period)]
        if any(np.isnan(x) for x in sp):
            return None
        mean = sum(sp) / period
        var = (sum(x * x for x in sp) / period) - (mean * mean)
        return None if var <= 0.0 else (sp[0] - mean) / float(np.sqrt(var))

    @classmethod
    def spread_zscore_bullish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        period: int = 26,
        z_threshold: float = 1.5,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpreadZScoreBullish (`z_score > z_threshold`)."""
        z = cls._spread_zscore(hedg52, spec52, period, shift)
        return z is not None and z > z_threshold

    @classmethod
    def spread_zscore_bearish(
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        period: int = 26,
        z_threshold: float = 1.5,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTSpreadZScoreBearish (`z_score < -z_threshold`)."""
        z = cls._spread_zscore(hedg52, spec52, period, shift)
        return z is not None and z < -z_threshold

    @classmethod
    def triple_div_bullish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        small52: IndicatorSeries,
        hedger_threshold: float = 0.75,
        spec_threshold: float = 0.25,
        small_threshold: float = 0.25,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTTripleDivBullish."""
        return (
            hedg52.is_greater(hedger_threshold, shift)
            and spec52.is_lower(spec_threshold, shift)
            and small52.is_lower(small_threshold, shift)
        )

    @classmethod
    def triple_div_bearish(  # noqa: PLR0917
        cls,
        hedg52: IndicatorSeries,
        spec52: IndicatorSeries,
        small52: IndicatorSeries,
        hedger_threshold: float = 0.25,
        spec_threshold: float = 0.75,
        small_threshold: float = 0.75,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTTripleDivBearish."""
        return (
            hedg52.is_lower(hedger_threshold, shift)
            and spec52.is_greater(spec_threshold, shift)
            and small52.is_greater(small_threshold, shift)
        )

    @classmethod
    def vix_proxy_bullish(
        cls,
        hedg: IndicatorSeries,
        spec: IndicatorSeries,
        hedger_threshold: float = 0.75,
        spec_threshold: float = 0.25,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTVixProxyBullish (`hedg > hedger_thr and spec < spec_thr`)."""
        return hedg.is_greater(hedger_threshold, shift) and spec.is_lower(
            spec_threshold, shift
        )

    @classmethod
    def vix_proxy_bearish(
        cls,
        hedg: IndicatorSeries,
        spec: IndicatorSeries,
        hedger_threshold: float = 0.25,
        spec_threshold: float = 0.75,
        shift: int = 0,
    ) -> bool:
        """Evaluate COTVixProxyBearish (`hedg < hedger_thr and spec > spec_thr`)."""
        return hedg.is_lower(hedger_threshold, shift) and spec.is_greater(
            spec_threshold, shift
        )
