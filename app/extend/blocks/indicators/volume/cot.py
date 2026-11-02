"""COT volume indicator strategy block.

Description:
    Calculates Commitments of Traders (COT) commercial/non-commercial positioning.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Commitments of Traders positioning calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.cot import COT
    res = COT().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import is_falling as series_is_falling
from app.extend.blocks.comparisons import is_lower as series_is_lower
from app.extend.blocks.comparisons import is_rising as series_is_rising
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.series import IndicatorSeries as Series
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_FAST_PERIOD: int = 52
DEFAULT_SLOW_PERIOD: int = 156
MIN_COT_PERIOD: int = 2
BULLISH_EXTREME_DEFAULT: float = 0.6
BEARISH_EXTREME_DEFAULT: float = -0.6
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
type _SeriesInput = IndicatorSeries | Sequence[float] | np.ndarray[Any, Any]


def _as_series(s: _SeriesInput) -> Series:
    """Resolve a positioning series without copying an existing wrapper."""
    return s if isinstance(s, IndicatorSeries) else IndicatorSeries(s)


def _mom_pair(score: Series, mom_period: int, shift: int) -> tuple[float, float] | None:
    """Resolve current and prior momentum, preserving missing-data validity."""
    v = [
        score.get(shift),
        score.get(shift + mom_period),
        score.get(shift + 1),
        score.get(shift + 1 + mom_period),
    ]
    return None if any(np.isnan(x) for x in v) else (v[0] - v[1], v[2] - v[3])


def _spread_zscore(
    hedg52: Series, spec52: Series, period: int, shift: int
) -> float | None:
    """Compute a positioning spread z-score when sufficient data is available."""
    if period <= 1:
        return None
    sp = [hedg52.get(shift + i) - spec52.get(shift + i) for i in range(period)]
    if any(np.isnan(x) for x in sp):
        return None
    mean = sum(sp) / period
    var = sum(x * x for x in sp) / period - mean * mean
    return None if var <= 0.0 else (sp[0] - mean) / float(np.sqrt(var))


class COT(BaseIndicator):
    """Commitment of Traders indicator computing CPI/CTI, scores, and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.cot",
        name="COT",
        category="volume",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("commercial_net", PortType.SERIES, required=True),
            InputPort("speculator_net", PortType.SERIES, required=True),
            InputPort("small_spec_net", PortType.SERIES, required=False),
            InputPort("open_interest", PortType.SERIES, required=False),
        ),
        outputs=tuple(OutputPort(name, PortType.SERIES) for name in _COT_SERIES_NAMES),
        required_market_inputs=("commercial_net", "speculator_net"),
        parameter_search_space={
            "period_fast": {"type": "int", "min": 2, "max": 208, "default": 52},
            "period_slow": {"type": "int", "min": 2, "max": 624, "default": 156},
        },
        is_causal=True,
        is_generation_eligible=False,
        required_history_lookback=156,
    )
    period_fast: int = Field(default=DEFAULT_FAST_PERIOD, ge=2)
    period_slow: int = Field(default=DEFAULT_SLOW_PERIOD, ge=2)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject reversed windows rather than silently swapping configured periods."""
        if self.period_fast > self.period_slow:
            raise ValueError("period_fast must not exceed period_slow")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.period_fast, self.period_slow)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        commercial_net = bars.input("commercial_net", required=True)
        speculator_net = bars.input("speculator_net", required=True)
        small_spec_net = bars.input("small_spec_net", required=False)
        open_interest = bars.input("open_interest", required=False)
        period_fast = self.period_fast
        period_slow = self.period_slow
        c_arr = to_numpy(commercial_net)
        s_arr = to_numpy(speculator_net)
        n = min(len(c_arr), len(s_arr))
        sm_arr = (
            to_numpy(small_spec_net)
            if small_spec_net is not None
            else -(c_arr[:n] + s_arr[:n])
        )
        n = min(n, len(sm_arr))
        oi_arr = (
            np.maximum(to_numpy(open_interest)[:n], 1e-09)
            if open_interest is not None
            else np.maximum(np.abs(c_arr[:n]) + np.abs(s_arr[:n]) + 1.0, 1.0)
        )
        arrays = {k: np.full(n, np.nan, dtype=np.float64) for k in _COT_SERIES_NAMES}
        if n < period_fast:
            logger.info(
                "FR-SERVICES-COT-CALCULATE: Insufficient bars (%d < %d)", n, period_fast
            )
            return {
                k: IndicatorSeries(arrays[k], name=v)
                for k, v in _COT_SERIES_NAMES.items()
            }
        cpi_h_fast = COT._percent_rank_rolling(c_arr[:n], period_fast)
        cpi_s_fast = COT._percent_rank_rolling(s_arr[:n], period_fast)
        cpi_sm_fast = COT._percent_rank_rolling(sm_arr[:n], period_fast)
        cti_h = COT._percent_rank_rolling(c_arr[:n] / oi_arr, period_fast)
        cti_s = COT._percent_rank_rolling(s_arr[:n] / oi_arr, period_fast)
        cpi_h_slow = (
            COT._percent_rank_rolling(c_arr[:n], period_slow)
            if n >= period_slow
            else cpi_h_fast.copy()
        )
        cpi_s_slow = (
            COT._percent_rank_rolling(s_arr[:n], period_slow)
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

    @staticmethod
    def _percent_rank_rolling(
        arr: np.ndarray[Any, Any], period: int
    ) -> np.ndarray[Any, Any]:
        """Compute rolling percentile rank (min-max normalization) in [0.0, 1.0]."""
        n = len(arr)
        out = np.full(n, np.nan, dtype=np.float64)
        for i in range(period - 1, n):
            window = arr[i - period + 1 : i + 1]
            w_min, w_max = (float(np.min(window)), float(np.max(window)))
            diff = w_max - w_min
            out[i] = (
                0.5
                if diff <= 0.0
                else float(np.clip((arr[i] - w_min) / diff, 0.0, 1.0))
            )
        return out


def extreme_persistence(
    series: Series, extreme_threshold: float = 0.8, min_weeks: int = 3, shift: int = 0
) -> bool:
    """Evaluate COTExtremePersistence."""
    return min_weeks > 0 and all(
        not np.isnan(v := series.get(shift + i)) and v >= extreme_threshold
        for i in range(min_weeks)
    )


def extreme_unwind_bullish(
    spec52: Series,
    crowded_threshold: float = 0.85,
    normalize_threshold: float = 0.75,
    lookback_weeks: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTExtremeUnwindBullish."""
    return (
        series_is_lower(spec52, normalize_threshold, shift1=shift)
        and series_is_falling(spec52, shift=shift)
        and any(
            is_greater(spec52, crowded_threshold, shift1=shift + i)
            for i in range(1, lookback_weeks + 1)
        )
    )


def extreme_unwind_bearish(
    hedg52: Series,
    crowded_threshold: float = 0.85,
    normalize_threshold: float = 0.75,
    lookback_weeks: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTExtremeUnwindBearish."""
    return extreme_unwind_bullish(
        hedg52, crowded_threshold, normalize_threshold, lookback_weeks, shift
    )


def full_cycle_long(hedg: Series, entry_level: float = 0.8, shift: int = 0) -> bool:
    """Evaluate COTFullCycleLong (`hedg[s+1] < entry_level <= hedg[s]`)."""
    c0, c1 = (hedg.get(shift), hedg.get(shift + 1))
    return not (np.isnan(c0) or np.isnan(c1)) and c1 < entry_level <= c0


def full_cycle_short(hedg: Series, entry_level: float = 0.2, shift: int = 0) -> bool:
    """Evaluate COTFullCycleShort (`hedg[s+1] > entry_level >= hedg[s]`)."""
    c0, c1 = (hedg.get(shift), hedg.get(shift + 1))
    return not (np.isnan(c0) or np.isnan(c1)) and c1 > entry_level >= c0


def full_cycle_exit_long(hedg: Series, exit_level: float = 0.5, shift: int = 0) -> bool:
    """Evaluate COTFullCycleExitLong (`hedg[shift] >= exit_level`)."""
    c0 = hedg.get(shift)
    return not np.isnan(c0) and c0 >= exit_level


def full_cycle_exit_short(
    hedg: Series, exit_level: float = 0.5, shift: int = 0
) -> bool:
    """Evaluate COTFullCycleExitShort (`hedg[shift] <= exit_level`)."""
    c0 = hedg.get(shift)
    return not np.isnan(c0) and c0 <= exit_level


def hedger_accel_bullish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    accel_threshold: float = 0.15,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTHedgerAccelBullish."""
    return shift_52_vs_156_bullish(
        hedg52, spec52, hedg156, spec156, accel_threshold, shift=shift
    )


def hedger_accel_bearish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    accel_threshold: float = 0.15,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTHedgerAccelBearish."""
    return shift_52_vs_156_bearish(
        hedg52, spec52, hedg156, spec156, accel_threshold, shift=shift
    )


def hedger_div_conf_bullish(
    hedg52: Series,
    spec52: Series,
    hedger_threshold: float = 0.75,
    spec_threshold: float = 0.25,
    mom_lookback: int = 4,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTHedgerDivConfBullish."""
    return (
        is_greater(hedg52, hedger_threshold, shift1=shift)
        and series_is_lower(spec52, spec_threshold, shift1=shift)
        and is_greater(hedg52, hedg52, shift1=shift, shift2=shift + mom_lookback)
    )


def hedger_div_conf_bearish(
    hedg52: Series,
    spec52: Series,
    hedger_threshold: float = 0.25,
    spec_threshold: float = 0.75,
    mom_lookback: int = 4,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTHedgerDivConfBearish."""
    return (
        series_is_lower(hedg52, hedger_threshold, shift1=shift)
        and is_greater(spec52, spec_threshold, shift1=shift)
        and series_is_lower(hedg52, hedg52, shift1=shift, shift2=shift + mom_lookback)
    )


def higher_low(
    score: Series, short_window: int = 4, long_window: int = 12, shift: int = 0
) -> bool:
    """Evaluate COTHigherLow (`short_min > long_min and long_min < 0`)."""
    if short_window <= 0 or long_window <= short_window:
        return False
    vals = [score.get(shift + i) for i in range(long_window)]
    if any(np.isnan(x) for x in vals):
        return False
    s_min, l_min = (min(vals[:short_window]), min(vals[short_window:]))
    return s_min > l_min and l_min < 0.0


def lower_high(
    score: Series, short_window: int = 4, long_window: int = 12, shift: int = 0
) -> bool:
    """Evaluate COTLowerHigh (`short_max < long_max and long_max > 0`)."""
    if short_window <= 0 or long_window <= short_window:
        return False
    vals = [score.get(shift + i) for i in range(long_window)]
    if any(np.isnan(x) for x in vals):
        return False
    s_max, l_max = (max(vals[:short_window]), max(vals[short_window:]))
    return s_max < l_max and l_max > 0.0


def momentum_rev_bullish(score: Series, mom_period: int = 4, shift: int = 0) -> bool:
    """Evaluate COTMomentumRevBullish (`mom_now > 0 and mom_prev <= 0`)."""
    mp = _mom_pair(score, mom_period, shift)
    return mp is not None and mp[0] > 0.0 and (mp[1] <= 0.0)


def momentum_rev_bearish(score: Series, mom_period: int = 4, shift: int = 0) -> bool:
    """Evaluate COTMomentumRevBearish (`mom_now < 0 and mom_prev >= 0`)."""
    mp = _mom_pair(score, mom_period, shift)
    return mp is not None and mp[0] < 0.0 and (mp[1] >= 0.0)


def multi_window_bullish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    hedger_threshold: float = 0.75,
    *,
    hedger156_threshold: float = 0.7,
    spec_threshold: float = 0.25,
    spec156_threshold: float = 0.3,
    shift: int = 0,
) -> bool:
    """Evaluate COTMultiWindowBullish."""
    return extreme_bullish(
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


def multi_window_bearish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    hedger_threshold: float = 0.25,
    *,
    hedger156_threshold: float = 0.3,
    spec_threshold: float = 0.75,
    spec156_threshold: float = 0.7,
    shift: int = 0,
) -> bool:
    """Evaluate COTMultiWindowBearish."""
    return extreme_bearish(
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


def neutral_zone(score: Series, neutral_band: float = 0.15, shift: int = 0) -> bool:
    """Evaluate COTNeutralZone (`abs(score[shift]) < neutral_band`)."""
    v = score.get(shift)
    return not np.isnan(v) and abs(v) < neutral_band


def regime_shift_bullish(score: Series, shift_weeks: int = 4, shift: int = 0) -> bool:
    """Evaluate COTRegimeShiftBullish (`short_avg > long_avg and short_avg > 0`)."""
    if shift_weeks <= 0:
        return False
    vals = [score.get(shift + k) for k in range(shift_weeks * 3)]
    if any(np.isnan(x) for x in vals):
        return False
    s_avg, l_avg = (sum(vals[:shift_weeks]) / shift_weeks, sum(vals) / len(vals))
    return s_avg > l_avg and s_avg > 0.0


def regime_shift_bearish(score: Series, shift_weeks: int = 4, shift: int = 0) -> bool:
    """Evaluate COTRegimeShiftBearish (`short_avg < long_avg and short_avg < 0`)."""
    if shift_weeks <= 0:
        return False
    vals = [score.get(shift + k) for k in range(shift_weeks * 3)]
    if any(np.isnan(x) for x in vals):
        return False
    s_avg, l_avg = (sum(vals[:shift_weeks]) / shift_weeks, sum(vals) / len(vals))
    return s_avg < l_avg and s_avg < 0.0


def roc_bullish(
    score: Series, roc_period: int = 4, roc_threshold: float = 0.2, shift: int = 0
) -> bool:
    """Evaluate COTRocBullish (`score[shift] - score[s + period] > threshold`)."""
    s0, sp = (score.get(shift), score.get(shift + roc_period))
    return not (np.isnan(s0) or np.isnan(sp)) and s0 - sp > roc_threshold


def roc_bearish(
    score: Series, roc_period: int = 4, roc_threshold: float = 0.2, shift: int = 0
) -> bool:
    """Evaluate COTRocBearish (`score[shift] - score[s + period] < -threshold`)."""
    s0, sp = (score.get(shift), score.get(shift + roc_period))
    return not (np.isnan(s0) or np.isnan(sp)) and s0 - sp < -roc_threshold


def score_accel_bullish(
    score: Series, mom_period: int = 4, momentum_threshold: float = 0.05, shift: int = 0
) -> bool:
    """Evaluate COTScoreAccelBullish (`mom_now > mom_prev and mom_now > thr`)."""
    mp = _mom_pair(score, mom_period, shift)
    return mp is not None and mp[0] > mp[1] and (mp[0] > momentum_threshold)


def score_accel_bearish(
    score: Series,
    mom_period: int = 4,
    momentum_threshold: float = -0.05,
    shift: int = 0,
) -> bool:
    """Evaluate COTScoreAccelBearish (`mom_now < mom_prev and mom_now < thr`)."""
    mp = _mom_pair(score, mom_period, shift)
    return mp is not None and mp[0] < mp[1] and (mp[0] < momentum_threshold)


def score_momentum_above(
    score: Series,
    momentum_lookback: int = 4,
    momentum_threshold: float = 0.1,
    level_threshold: float = 0.0,
    shift: int = 0,
) -> bool:
    """Evaluate COTScoreMomentumAbove."""
    return roc_bullish(
        score, momentum_lookback, momentum_threshold, shift
    ) and is_greater(score, level_threshold, shift1=shift)


def score_momentum_below(
    score: Series,
    momentum_lookback: int = 4,
    momentum_threshold: float = 0.1,
    level_threshold: float = 0.0,
    shift: int = 0,
) -> bool:
    """Evaluate COTScoreMomentumBelow."""
    return roc_bearish(
        score, momentum_lookback, momentum_threshold, shift
    ) and series_is_lower(score, level_threshold, shift1=shift)


def seasonal_bullish(
    hedg52: Series,
    seasonal_lookback: int = 12,
    seasonal_threshold: float = 0.15,
    shift: int = 0,
) -> bool:
    """Evaluate COTSeasonalBullish (`current > avg(past) + seasonal_threshold`)."""
    if seasonal_lookback <= 0:
        return False
    cur = hedg52.get(shift)
    past = [hedg52.get(shift + i) for i in range(1, seasonal_lookback + 1)]
    return (
        not (np.isnan(cur) or any(np.isnan(x) for x in past))
        and cur > sum(past) / seasonal_lookback + seasonal_threshold
    )


def seasonal_bearish(
    hedg52: Series,
    seasonal_lookback: int = 12,
    seasonal_threshold: float = 0.15,
    shift: int = 0,
) -> bool:
    """Evaluate COTSeasonalBearish (`current < avg(past) - seasonal_threshold`)."""
    if seasonal_lookback <= 0:
        return False
    cur = hedg52.get(shift)
    past = [hedg52.get(shift + i) for i in range(1, seasonal_lookback + 1)]
    return (
        not (np.isnan(cur) or any(np.isnan(x) for x in past))
        and cur < sum(past) / seasonal_lookback - seasonal_threshold
    )


def smart_dumb_bullish(
    hedg52: Series,
    small52: Series,
    hedger_threshold: float = 0.75,
    small_threshold: float = 0.25,
    shift: int = 0,
) -> bool:
    """Evaluate COTSmartDumbBullish (`hedg52 > hedger_thr and small52 < thr`)."""
    return is_greater(hedg52, hedger_threshold, shift1=shift) and series_is_lower(
        small52, small_threshold, shift1=shift
    )


def smart_dumb_bearish(
    hedg52: Series,
    small52: Series,
    hedger_threshold: float = 0.25,
    small_threshold: float = 0.75,
    shift: int = 0,
) -> bool:
    """Evaluate COTSmartDumbBearish (`hedg52 < hedger_thr and small52 > thr`)."""
    return series_is_lower(hedg52, hedger_threshold, shift1=shift) and is_greater(
        small52, small_threshold, shift1=shift
    )


def spec_exhaustion_long(
    hedg52: Series,
    spec52: Series,
    spec_extreme: float = 0.9,
    hedger_threshold: float = 0.7,
    lookback_weeks: int = 4,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpecExhaustionLong."""
    return (
        series_is_rising(spec52, shift=shift)
        and is_greater(hedg52, hedger_threshold, shift1=shift)
        and any(
            series_is_lower(spec52, 1.0 - spec_extreme, shift1=shift + i)
            for i in range(1, lookback_weeks + 1)
        )
    )


def spec_exhaustion_short(
    hedg52: Series,
    spec52: Series,
    spec_extreme: float = 0.9,
    hedger_threshold: float = 0.3,
    lookback_weeks: int = 4,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpecExhaustionShort."""
    return (
        series_is_falling(spec52, shift=shift)
        and series_is_lower(hedg52, hedger_threshold, shift1=shift)
        and any(
            is_greater(spec52, spec_extreme, shift1=shift + i)
            for i in range(1, lookback_weeks + 1)
        )
    )


def spec_trend_long(
    spec52: Series,
    spec156: Series,
    spec_min: float = 0.5,
    spec_max: float = 0.85,
    spec156_threshold: float = 0.5,
    *,
    lookback: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpecTrendLong."""
    s0 = spec52.get(shift)
    return (
        not np.isnan(s0)
        and spec_min < s0 < spec_max
        and is_greater(spec156, spec156_threshold, shift1=shift)
        and is_greater(spec52, spec52, shift1=shift, shift2=shift + lookback)
    )


def spec_trend_short(
    spec52: Series,
    spec156: Series,
    spec_min: float = 0.15,
    spec_max: float = 0.5,
    spec156_threshold: float = 0.5,
    *,
    lookback: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpecTrendShort."""
    s0 = spec52.get(shift)
    return (
        not np.isnan(s0)
        and spec_min < s0 < spec_max
        and series_is_lower(spec156, spec156_threshold, shift1=shift)
        and series_is_lower(spec52, spec52, shift1=shift, shift2=shift + lookback)
    )


def spread_zscore_bullish(
    hedg52: Series,
    spec52: Series,
    period: int = 26,
    z_threshold: float = 1.5,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpreadZScoreBullish (`z_score > z_threshold`)."""
    z = _spread_zscore(hedg52, spec52, period, shift)
    return z is not None and z > z_threshold


def spread_zscore_bearish(
    hedg52: Series,
    spec52: Series,
    period: int = 26,
    z_threshold: float = 1.5,
    shift: int = 0,
) -> bool:
    """Evaluate COTSpreadZScoreBearish (`z_score < -z_threshold`)."""
    z = _spread_zscore(hedg52, spec52, period, shift)
    return z is not None and z < -z_threshold


def triple_div_bullish(
    hedg52: Series,
    spec52: Series,
    small52: Series,
    hedger_threshold: float = 0.75,
    spec_threshold: float = 0.25,
    *,
    small_threshold: float = 0.25,
    shift: int = 0,
) -> bool:
    """Evaluate COTTripleDivBullish."""
    return (
        is_greater(hedg52, hedger_threshold, shift1=shift)
        and series_is_lower(spec52, spec_threshold, shift1=shift)
        and series_is_lower(small52, small_threshold, shift1=shift)
    )


def triple_div_bearish(
    hedg52: Series,
    spec52: Series,
    small52: Series,
    hedger_threshold: float = 0.25,
    spec_threshold: float = 0.75,
    *,
    small_threshold: float = 0.75,
    shift: int = 0,
) -> bool:
    """Evaluate COTTripleDivBearish."""
    return (
        series_is_lower(hedg52, hedger_threshold, shift1=shift)
        and is_greater(spec52, spec_threshold, shift1=shift)
        and is_greater(small52, small_threshold, shift1=shift)
    )


def field_value(series: _SeriesInput, shift: int = 0) -> float:
    """Evaluate COTFieldValue / COTCpi* / COTCti* at shift."""
    val = _as_series(series).get(shift)
    return 0.0 if np.isnan(val) else float(val)


def cross_field_spread(
    field1: _SeriesInput, field2: _SeriesInput, shift: int = 0
) -> float:
    """Evaluate COTCrossFieldSpread (`field1[shift] - field2[shift]`)."""
    v1, v2 = (_as_series(field1).get(shift), _as_series(field2).get(shift))
    return 0.0 if np.isnan(v1) or np.isnan(v2) else float(v1 - v2)


def momentum(series: _SeriesInput, lookback: int = 4, shift: int = 0) -> float:
    """Evaluate COTMomentum (`series[shift] - series[shift + lookback]`)."""
    s = _as_series(series)
    v0, v1 = (s.get(shift), s.get(shift + lookback))
    return 0.0 if np.isnan(v0) or np.isnan(v1) else float(v0 - v1)


def multi_field_combo(
    cpi_hedg: _SeriesInput | None = None,
    cpi_spec: _SeriesInput | None = None,
    cpi_small: _SeriesInput | None = None,
    cti_spec: _SeriesInput | None = None,
    shift: int = 0,
) -> float:
    """Evaluate COTMultiFieldCombo (`mean(cpi_hedg, 1 - others)`)."""
    vals: list[float] = []
    if cpi_hedg is not None and (not np.isnan(vh := _as_series(cpi_hedg).get(shift))):
        vals.append(float(vh))
    vals.extend(
        1.0 - float(vi)
        for inv in (cpi_spec, cpi_small, cti_spec)
        if inv is not None and (not np.isnan(vi := _as_series(inv).get(shift)))
    )
    return float(sum(vals) / len(vals)) if vals else 0.5


def shift_52_vs_156_bullish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    shift_threshold: float = 0.15,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COT52vs156ShiftBullish (`hedg52 - hedg156 > thr`)."""
    v = [x.get(shift) for x in (hedg52, spec52, hedg156, spec156)]
    if any(np.isnan(x) for x in v):
        return False
    return v[0] - v[2] > shift_threshold and v[1] - v[3] < -shift_threshold


def shift_52_vs_156_bearish(
    hedg52: Series,
    spec52: Series,
    hedg156: Series,
    spec156: Series,
    shift_threshold: float = 0.15,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COT52vs156ShiftBearish (`hedg52 - hedg156 < -thr`)."""
    return shift_52_vs_156_bullish(
        spec52, hedg52, spec156, hedg156, shift_threshold, shift=shift
    )


def accumulation_bullish(
    hedg52: Series, spec52: Series, min_weeks: int = 3, shift: int = 0
) -> bool:
    """Evaluate COTAccumulationBullish (hedgers up and speculators down)."""
    return min_weeks > 0 and all(
        series_is_rising(hedg52, shift=shift + i)
        and series_is_falling(spec52, shift=shift + i)
        for i in range(min_weeks)
    )


def accumulation_bearish(
    hedg52: Series, spec52: Series, min_weeks: int = 3, shift: int = 0
) -> bool:
    """Evaluate COTAccumulationBearish (hedgers down and speculators up)."""
    return accumulation_bullish(spec52, hedg52, min_weeks, shift)


def extreme_bullish(
    hedg52: Series,
    spec52: Series,
    hedger_threshold: float = 0.8,
    spec_threshold: float = 0.2,
    *,
    hedg156: Series | None = None,
    spec156: Series | None = None,
    hedger156_threshold: float = 0.7,
    spec156_threshold: float = 0.3,
    shift: int = 0,
) -> bool:
    """Evaluate COTBullishExtreme across 52w and optional 156w CPI."""
    if not (
        is_greater(hedg52, hedger_threshold, shift1=shift)
        and series_is_lower(spec52, spec_threshold, shift1=shift)
    ):
        return False
    if hedg156 is not None and spec156 is not None:
        return is_greater(
            hedg156, hedger156_threshold, shift1=shift
        ) and series_is_lower(spec156, spec156_threshold, shift1=shift)
    return True


def extreme_bearish(
    hedg52: Series,
    spec52: Series,
    hedger_threshold: float = 0.2,
    spec_threshold: float = 0.8,
    *,
    hedg156: Series | None = None,
    spec156: Series | None = None,
    hedger156_threshold: float = 0.3,
    spec156_threshold: float = 0.7,
    shift: int = 0,
) -> bool:
    """Evaluate COTBearishExtreme across 52w and optional 156w CPI."""
    if not (
        series_is_lower(hedg52, hedger_threshold, shift1=shift)
        and is_greater(spec52, spec_threshold, shift1=shift)
    ):
        return False
    if hedg156 is not None and spec156 is not None:
        return series_is_lower(
            hedg156, hedger156_threshold, shift1=shift
        ) and is_greater(spec156, spec156_threshold, shift1=shift)
    return True


def convergence(
    hedg52: Series, spec52: Series, convergence_threshold: float = 0.15, shift: int = 0
) -> bool:
    """Evaluate COTConvergence (`abs(hedg52 - spec52) < convergence_threshold`)."""
    h, s = (hedg52.get(shift), spec52.get(shift))
    return not (np.isnan(h) or np.isnan(s)) and abs(h - s) < convergence_threshold


def crowding_unwind(
    hedg52: Series,
    spec52: Series,
    direction: int = 1,
    spec_extreme: float = 0.85,
    hedger_opposing: float = 0.3,
    *,
    shift: int = 0,
) -> bool:
    """Evaluate COTCrowdingUnwind."""
    s0, s1, h0 = (spec52.get(shift), spec52.get(shift + 1), hedg52.get(shift))
    if any(np.isnan(x) for x in (s0, s1, h0)):
        return False
    if direction > 0:
        return s1 > spec_extreme and s0 < s1 and (h0 < hedger_opposing)
    return s1 < 1.0 - spec_extreme and s0 > s1 and (h0 > 1.0 - hedger_opposing)


def extreme_exit_bullish(
    hedg52: Series,
    extreme_threshold: float = 0.85,
    exit_threshold: float = 0.7,
    lookback_weeks: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTExtremeExitBullish."""
    return series_is_lower(hedg52, exit_threshold, shift1=shift) and any(
        is_greater(hedg52, extreme_threshold, shift1=shift + i)
        for i in range(1, lookback_weeks + 1)
    )


def extreme_exit_bearish(
    spec52: Series,
    extreme_threshold: float = 0.85,
    exit_threshold: float = 0.7,
    lookback_weeks: int = 4,
    shift: int = 0,
) -> bool:
    """Evaluate COTExtremeExitBearish."""
    return series_is_lower(spec52, exit_threshold, shift1=shift) and any(
        is_greater(spec52, extreme_threshold, shift1=shift + i)
        for i in range(1, lookback_weeks + 1)
    )


def vix_proxy_bullish(
    hedg: Series,
    spec: Series,
    hedger_threshold: float = 0.75,
    spec_threshold: float = 0.25,
    shift: int = 0,
) -> bool:
    """Evaluate COTVixProxyBullish (`hedg > hedger_thr and spec < spec_thr`)."""
    return is_greater(hedg, hedger_threshold, shift1=shift) and series_is_lower(
        spec, spec_threshold, shift1=shift
    )


def vix_proxy_bearish(
    hedg: Series,
    spec: Series,
    hedger_threshold: float = 0.25,
    spec_threshold: float = 0.75,
    shift: int = 0,
) -> bool:
    """Evaluate COTVixProxyBearish (`hedg < hedger_thr and spec > spec_thr`)."""
    return series_is_lower(hedg, hedger_threshold, shift1=shift) and is_greater(
        spec, spec_threshold, shift1=shift
    )
