"""ZigZag Structural Price Action Indicator Block.

Description:
    Identifies significant swing highs (peaks) and swing lows (troughs) by
    filtering out price fluctuations smaller than a specified percentage
    deviation threshold. Constructs the ZigZag trend line connecting
    consecutive swing points.

Purpose:
    FEAT-SERVICES-INDICATOR-ZIGZAG

Key Capabilities:
    - FR-SERVICES-ZIGZAG-CALCULATE: Computes swing points, swing types, and zigzag.
      Associated: `ZigZag.calculate()`
      Logging: INFO level logging of deviation, depth, and swing point count.
    - FR-SERVICES-ZIGZAG-CONDITIONS: Evaluates peak, trough, and leg direction states.
      Associated: `ZigZag.is_peak()`, `ZigZag.is_trough()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.price_action.zigzag import ZigZag

    res = ZigZag.calculate(high, low, deviation=5.0, depth=5)
    zigzag = res["zigzag"]
    swing_type = res["swing_type"]
    is_peak = ZigZag.is_peak(swing_type, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_ZIGZAG_DEVIATION: float = 0.01
DEFAULT_ZIGZAG_DEVIATION: float = 5.0
MIN_ZIGZAG_DEPTH: int = 1
DEFAULT_ZIGZAG_DEPTH: int = 5
MIN_SWINGS_FOR_INTERPOLATION: int = 2
SWING_PEAK_TYPE: float = 1.0
SWING_TROUGH_TYPE: float = -1.0
SWING_THRESHOLD: float = 0.5


class _ZigZagTracker:
    """Internal helper tracking candidate extrema and confirmed swing pivots."""

    def __init__(self, dev_frac: float, depth: int) -> None:
        self.dev_frac = dev_frac
        self.depth = depth
        self.swings: list[tuple[int, float, float]] = []
        self.direction = 0
        self.cand_high = 0.0
        self.cand_high_idx = 0
        self.cand_low = 0.0
        self.cand_low_idx = 0

    def init_first_bar(self, high: float, low: float) -> None:
        """Set initial candidate extremes at bar 0."""
        self.cand_high = high
        self.cand_high_idx = 0
        self.cand_low = low
        self.cand_low_idx = 0

    def process_bar(self, h_val: float, l_val: float, i: int) -> None:
        """Process price values at bar index i."""
        if self.direction == 0:
            self._update_undecided(h_val, l_val, i)
        elif self.direction == 1:
            self._update_peak_search(h_val, l_val, i)
        else:
            self._update_trough_search(h_val, l_val, i)

    def _update_undecided(self, h_val: float, l_val: float, i: int) -> None:
        trough_confirmed = (
            h_val >= self.cand_low * (1.0 + self.dev_frac)
            and (i - self.cand_low_idx) >= self.depth
        )
        peak_confirmed = (
            l_val <= self.cand_high * (1.0 - self.dev_frac)
            and (i - self.cand_high_idx) >= self.depth
        )
        if trough_confirmed:
            self.swings.append((self.cand_low_idx, self.cand_low, SWING_TROUGH_TYPE))
            self.direction = 1
            self.cand_high = h_val
            self.cand_high_idx = i
        elif peak_confirmed:
            self.swings.append((self.cand_high_idx, self.cand_high, SWING_PEAK_TYPE))
            self.direction = -1
            self.cand_low = l_val
            self.cand_low_idx = i
        else:
            self._expand_undecided_bounds(h_val, l_val, i)

    def _expand_undecided_bounds(self, h_val: float, l_val: float, i: int) -> None:
        if h_val > self.cand_high:
            self.cand_high = h_val
            self.cand_high_idx = i
        if l_val < self.cand_low:
            self.cand_low = l_val
            self.cand_low_idx = i

    def _update_peak_search(self, h_val: float, l_val: float, i: int) -> None:
        if h_val > self.cand_high:
            self.cand_high = h_val
            self.cand_high_idx = i
        elif (
            l_val <= self.cand_high * (1.0 - self.dev_frac)
            and (i - self.cand_high_idx) >= self.depth
        ):
            self.swings.append((self.cand_high_idx, self.cand_high, SWING_PEAK_TYPE))
            self.direction = -1
            self.cand_low = l_val
            self.cand_low_idx = i

    def _update_trough_search(self, h_val: float, l_val: float, i: int) -> None:
        if l_val < self.cand_low:
            self.cand_low = l_val
            self.cand_low_idx = i
        elif (
            h_val >= self.cand_low * (1.0 + self.dev_frac)
            and (i - self.cand_low_idx) >= self.depth
        ):
            self.swings.append((self.cand_low_idx, self.cand_low, SWING_TROUGH_TYPE))
            self.direction = 1
            self.cand_high = h_val
            self.cand_high_idx = i

    def finalize(self) -> list[tuple[int, float, float]]:
        """Append trailing extreme if unconfirmed at series end."""
        last_bar = self.swings[-1][0] if self.swings else -1
        if self.direction == 1 and self.cand_high_idx > last_bar:
            self.swings.append((self.cand_high_idx, self.cand_high, SWING_PEAK_TYPE))
        elif self.direction == -1 and self.cand_low_idx > last_bar:
            self.swings.append((self.cand_low_idx, self.cand_low, SWING_TROUGH_TYPE))
        return self.swings


class ZigZag(BaseIndicator):
    """ZigZag structural swing extrema and trendline segmentation block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        deviation: float = DEFAULT_ZIGZAG_DEVIATION,
        depth: int = DEFAULT_ZIGZAG_DEPTH,
    ) -> dict[str, IndicatorSeries]:
        """Compute ZigZag swing points, types, and interpolated zigzag line.

        Args:
            high: High price series.
            low: Low price series.
            deviation: Minimum percentage change to confirm a swing (>= 0.01).
            depth: Minimum bar distance between consecutive swings (>= 1).

        Returns:
            Dictionary containing:
                - 'zigzag': Linearly interpolated zigzag trendline series.
                - 'swing_point': Price at swing bar, np.nan elsewhere.
                - 'swing_type': +1.0 for peak, -1.0 for trough, 0.0 elsewhere.
        """
        logger.info(
            "ZigZag calculation initiated: deviation=%.2f, depth=%d",
            deviation,
            depth,
        )
        if deviation < MIN_ZIGZAG_DEVIATION:
            raise ValueError(
                f"deviation must be >= {MIN_ZIGZAG_DEVIATION}, got {deviation}"
            )
        if depth < MIN_ZIGZAG_DEPTH:
            raise ValueError(f"depth must be >= {MIN_ZIGZAG_DEPTH}, got {depth}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        swings = cls._find_swings(h_arr, l_arr, deviation, depth, n)
        zline, spoints, stypes = cls._build_series(h_arr, l_arr, swings, n)

        logger.info(
            "ZigZag calculation completed: bars=%d, swings=%d",
            n,
            len(swings),
        )
        return {
            "zigzag": IndicatorSeries(zline, name=f"ZigZag({deviation}%)"),
            "swing_point": IndicatorSeries(spoints, name="ZigZagSwings"),
            "swing_type": IndicatorSeries(stypes, name="ZigZagType"),
        }

    @classmethod
    def _find_swings(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        deviation: float,
        depth: int,
        n: int,
    ) -> list[tuple[int, float, float]]:
        tracker = _ZigZagTracker(deviation / 100.0, depth)
        tracker.init_first_bar(float(h_arr[0]), float(l_arr[0]))
        for i in range(1, n):
            tracker.process_bar(float(h_arr[i]), float(l_arr[i]), i)
        return tracker.finalize()

    @classmethod
    def _build_series(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        swings: list[tuple[int, float, float]],
        n: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        spoints = np.full(n, np.nan, dtype=np.float64)
        stypes = np.zeros(n, dtype=np.float64)
        zline = np.full(n, np.nan, dtype=np.float64)

        for idx, price, stype in swings:
            spoints[idx] = price
            stypes[idx] = stype

        if len(swings) >= MIN_SWINGS_FOR_INTERPOLATION:
            for s in range(len(swings) - 1):
                idx1, p1, _ = swings[s]
                idx2, p2, _ = swings[s + 1]
                span = idx2 - idx1
                for k in range(idx1, idx2 + 1):
                    t = (k - idx1) / span if span > 0 else 0.0
                    zline[k] = p1 + t * (p2 - p1)
            first_idx = swings[0][0]
            zline[:first_idx] = swings[0][1]
            last_idx = swings[-1][0]
            zline[last_idx:] = swings[-1][1]
        elif len(swings) == 1:
            zline[:] = swings[0][1]
        else:
            zline[:] = (h_arr + l_arr) / 2.0

        return zline, spoints, stypes

    @classmethod
    def is_peak(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a confirmed swing peak."""
        logger.info("Evaluating ZigZag is_peak at shift=%d", shift)
        val = swing_type.get(shift)
        return not np.isnan(val) and val > SWING_THRESHOLD

    @classmethod
    def is_trough(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a confirmed swing trough."""
        logger.info("Evaluating ZigZag is_trough at shift=%d", shift)
        val = swing_type.get(shift)
        return not np.isnan(val) and val < -SWING_THRESHOLD

    @classmethod
    def is_swing(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is any confirmed swing point."""
        logger.info("Evaluating ZigZag is_swing at shift=%d", shift)
        val = swing_type.get(shift)
        return not np.isnan(val) and abs(val) > SWING_THRESHOLD

    @classmethod
    def last_swing_direction(cls, swing_type: IndicatorSeries, shift: int = 0) -> int:
        """Returns +1 if most recent swing was a peak, -1 if trough, 0 if none."""
        logger.info("Evaluating ZigZag last_swing_direction at shift=%d", shift)
        n = len(swing_type)
        for s in range(shift, n):
            val = swing_type.get(s)
            if not np.isnan(val):
                if val > SWING_THRESHOLD:
                    return 1
                if val < -SWING_THRESHOLD:
                    return -1
        return 0

    @classmethod
    def is_rising(cls, zigzag: IndicatorSeries, shift: int = 0) -> bool:
        """True if zigzag line is rising between shift+1 and shift."""
        logger.info("Evaluating ZigZag is_rising at shift=%d", shift)
        curr = zigzag.get(shift)
        prev = zigzag.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, zigzag: IndicatorSeries, shift: int = 0) -> bool:
        """True if zigzag line is falling between shift+1 and shift."""
        logger.info("Evaluating ZigZag is_falling at shift=%d", shift)
        curr = zigzag.get(shift)
        prev = zigzag.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
