"""Bar Range (BarRange) indicator family implementation.

Description:
    Computes the price range of each bar calculated as High minus Low, plus
    intraday time-window price extrema (HighestInRange, LowestInRange) and
    fixed-pips price conversion (FixedPips). Provides condition helpers for
    range expansion/contraction analysis, including biggest range in period,
    smallest range in period, and relative range comparisons.

Purpose:
    FEAT-SERVICES-INDICATOR-BARRANGE: Bar range calculation and conditions.

Key Capabilities:
    - FR-SERVICES-BARRANGE-CALCULATE: Compute bar ranges and time-window extrema.
      Associated: `BarRange.calculate()`, `BarRange.highest_in_range()`,
      `BarRange.lowest_in_range()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-BARRANGE-CONDITIONS: Evaluate range conditions and fixed pips.
      Associated: `BarRange.is_biggest_range()`, `BarRange.is_smallest_range()`,
      `BarRange.fixed_pips()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.bar_range import BarRange

    high = np.array([10.0, 11.5, 12.0, 13.0, 14.0])
    low = np.array([9.0, 10.0, 10.5, 11.0, 12.5])
    rng = BarRange.calculate(high, low)
    val = rng.get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "bar_range"
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

_DAY_MS: int = 24 * 60 * 60 * 1000
_HOUR_MS: int = 60 * 60 * 1000
_MIN_MS: int = 60 * 1000
_SEC_TO_MS_CUTOFF: float = 1e11


class BarRange(BaseIndicator):
    """Bar Range indicator family."""

    name: str = "BarRange"
    category: str = "Ranges"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
    ) -> IndicatorSeries:
        """Compute the bar range series (High - Low)."""
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)

        res = high_arr - low_arr

        logger.info(
            "FR-SERVICES-BARRANGE-CALCULATE: Computed BarRange for %d bars",
            n,
        )
        return IndicatorSeries(res, name="BarRange")

    @staticmethod
    def _to_ms(ts: np.ndarray) -> np.ndarray:
        """Normalize timestamps array to milliseconds."""
        if len(ts) > 0 and float(np.max(np.abs(ts))) < _SEC_TO_MS_CUTOFF:
            return (ts * 1000.0).astype(np.int64)
        return ts.astype(np.int64)

    @staticmethod
    def _hhmm_offset_ms(hhmm: int) -> int:
        return (hhmm // 100) * _HOUR_MS + (hhmm % 100) * _MIN_MS

    @staticmethod
    def _roll_window_bounds(
        cur_t: int,
        time_from: int,
        time_to: int,
        from_off: int,
        to_off: int,
    ) -> tuple[int, int]:
        day_start = (cur_t // _DAY_MS) * _DAY_MS
        t_from = day_start + from_off
        t_to = day_start + to_off
        if t_to <= cur_t:
            if time_to < time_from:
                t_to += _DAY_MS
            else:
                t_from += _DAY_MS
                t_to += _DAY_MS
        return t_from, t_to

    @classmethod
    def highest_in_range(
        cls,
        timestamps: Sequence[int | float] | np.ndarray,
        high: Sequence[float] | np.ndarray,
        time_from: int = 0,
        time_to: int = 0,
    ) -> IndicatorSeries:
        """Compute HighestInRange series across a daily HHMM time window."""
        ts_ms = cls._to_ms(np.asarray(timestamps, dtype=np.float64))
        h_arr = np.asarray(high, dtype=np.float64)
        n = min(len(ts_ms), len(h_arr))
        out = np.zeros(n, dtype=np.float64)
        if n == 0:
            return IndicatorSeries(out, name=f"HighestInRange({time_from},{time_to})")

        from_off = cls._hhmm_offset_ms(time_from)
        to_off = cls._hhmm_offset_ms(time_to)
        day0 = (int(ts_ms[0]) // _DAY_MS) * _DAY_MS
        t_from = day0 + from_off
        t_to = day0 + to_off + (_DAY_MS if to_off < from_off else 0)
        highest_val = 0.0
        last_val = 0.0
        last_usable = 0.0

        for i in range(n):
            cur_t = int(ts_ms[i])
            if cur_t >= t_to:
                t_from, t_to = cls._roll_window_bounds(
                    cur_t, time_from, time_to, from_off, to_off
                )
                last_val = highest_val
                highest_val = float(h_arr[i]) if t_from <= cur_t else 0.0
            elif cur_t >= t_from:
                highest_val = max(highest_val, float(h_arr[i]))
            else:
                highest_val = 0.0

            if last_val > 0.0:
                last_usable = last_val
            out[i] = last_val if last_val > 0.0 else last_usable

        logger.info(
            "FR-SERVICES-BARRANGE-CALCULATE: HighestInRange(%d,%d) for %d bars",
            time_from,
            time_to,
            n,
        )
        return IndicatorSeries(out, name=f"HighestInRange({time_from},{time_to})")

    @classmethod
    def lowest_in_range(
        cls,
        timestamps: Sequence[int | float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        time_from: int = 0,
        time_to: int = 0,
    ) -> IndicatorSeries:
        """Compute LowestInRange series across a daily HHMM time window."""
        ts_ms = cls._to_ms(np.asarray(timestamps, dtype=np.float64))
        l_arr = np.asarray(low, dtype=np.float64)
        n = min(len(ts_ms), len(l_arr))
        out = np.zeros(n, dtype=np.float64)
        if n == 0:
            return IndicatorSeries(out, name=f"LowestInRange({time_from},{time_to})")

        from_off = cls._hhmm_offset_ms(time_from)
        to_off = cls._hhmm_offset_ms(time_to)
        day0 = (int(ts_ms[0]) // _DAY_MS) * _DAY_MS
        t_from = day0 + from_off
        t_to = day0 + to_off + (_DAY_MS if to_off < from_off else 0)
        max_float = float("inf")
        lowest_val = max_float
        last_val = max_float
        last_usable = 0.0

        for i in range(n):
            cur_t = int(ts_ms[i])
            if cur_t >= t_to:
                t_from, t_to = cls._roll_window_bounds(
                    cur_t, time_from, time_to, from_off, to_off
                )
                last_val = lowest_val
                lowest_val = float(l_arr[i]) if t_from <= cur_t else max_float
            elif cur_t >= t_from:
                lowest_val = min(lowest_val, float(l_arr[i]))
            else:
                lowest_val = max_float

            if last_val < max_float:
                last_usable = last_val
            out[i] = last_val if last_val < max_float else last_usable

        logger.info(
            "FR-SERVICES-BARRANGE-CALCULATE: LowestInRange(%d,%d) for %d bars",
            time_from,
            time_to,
            n,
        )
        return IndicatorSeries(out, name=f"LowestInRange({time_from},{time_to})")

    @classmethod
    def fixed_pips(cls, value: float, pip_size: float = 0.0001) -> float:
        """Convert a fixed pips value into a price range (`Value * pip_size`)."""
        return float(value * pip_size)

    # Unified condition helpers
    @classmethod
    def is_biggest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the highest among past period bars."""
        if lookback is not None:
            period = lookback
        val = series.get(shift)
        if np.isnan(val) or period <= 1:
            return False
        for s in range(shift + 1, shift + period):
            other = series.get(s)
            if np.isnan(other) or val <= other:
                return False
        return True

    @classmethod
    def is_smallest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the lowest among past period bars."""
        if lookback is not None:
            period = lookback
        val = series.get(shift)
        if np.isnan(val) or period <= 1:
            return False
        for s in range(shift + 1, shift + period):
            other = series.get(s)
            if np.isnan(other) or val >= other:
                return False
        return True

    @classmethod
    def is_highest_in_range(
        cls,
        series: IndicatorSeries | Sequence[float] | np.ndarray,
        lookback: int = 1,
        shift: int = 0,
    ) -> bool:
        """Evaluate if range at shift is higher than range lookback bars ago."""
        if not isinstance(series, IndicatorSeries):
            series = IndicatorSeries(series, name="Series")
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lowest_in_range(
        cls,
        series: IndicatorSeries | Sequence[float] | np.ndarray,
        lookback: int = 1,
        shift: int = 0,
    ) -> bool:
        """Evaluate if range at shift is lower than range lookback bars ago."""
        if not isinstance(series, IndicatorSeries):
            series = IndicatorSeries(series, name="Series")
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def in_range_pips(
        cls,
        series: IndicatorSeries,
        min_pips: float,
        max_pips: float,
        pip_size: float = 0.0001,
        shift: int = 0,
    ) -> bool:
        """Evaluate if bar range in pips is between min_pips and max_pips."""
        val = series.get(shift)
        if np.isnan(val) or pip_size <= 0:
            return False
        pips = val / pip_size
        return min_pips <= pips <= max_pips

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate range is rising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate range is falling condition."""
        return series.is_falling(shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate range is greater than level condition."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate range is lower than level condition."""
        return series.is_lower(level, shift)
