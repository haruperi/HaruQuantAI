"""ZigZag indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-ZIGZAG: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import is_falling, is_lower, is_rising
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
from app.include.calculators.base import to_numpy

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
            and i - self.cand_low_idx >= self.depth
        )
        peak_confirmed = (
            l_val <= self.cand_high * (1.0 - self.dev_frac)
            and i - self.cand_high_idx >= self.depth
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
            and i - self.cand_high_idx >= self.depth
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
            and i - self.cand_low_idx >= self.depth
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

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.zigzag",
        name="ZigZag",
        category="price_action",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("zigzag", PortType.SERIES),
            OutputPort("swing_point", PortType.SERIES),
            OutputPort("swing_type", PortType.SERIES),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "deviation": {"type": "float", "min": 0.01, "max": 20.0, "default": 5.0},
            "depth": {"type": "int", "min": 1, "max": 20, "default": 5},
        },
        is_causal=False,
        is_generation_eligible=False,
        required_history_lookback=6,
    )
    deviation: float = Field(default=DEFAULT_ZIGZAG_DEVIATION, ge=MIN_ZIGZAG_DEVIATION)
    depth: int = Field(default=DEFAULT_ZIGZAG_DEPTH, ge=MIN_ZIGZAG_DEPTH)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.deviation < MIN_ZIGZAG_DEVIATION:
            raise ValueError(
                f"deviation must be >= {MIN_ZIGZAG_DEVIATION}, got {self.deviation}"
            )
        if self.depth < MIN_ZIGZAG_DEPTH:
            raise ValueError(f"depth must be >= {MIN_ZIGZAG_DEPTH}, got {self.depth}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.depth + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        deviation = self.deviation
        depth = self.depth
        logger.info(
            "ZigZag calculation initiated: deviation=%.2f, depth=%d", deviation, depth
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        swings = self._find_swings(h_arr, l_arr, deviation, depth, n=n)
        zline, spoints, stypes = self._build_series(h_arr, l_arr, swings, n)
        logger.info("ZigZag calculation completed: bars=%d, swings=%d", n, len(swings))
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
        *,
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
        return (zline, spoints, stypes)

    @classmethod
    def is_peak(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a confirmed swing peak."""
        logger.info("Evaluating ZigZag is_peak at shift=%d", shift)
        return is_greater(swing_type, SWING_THRESHOLD, shift1=shift, round_digits=8)

    @classmethod
    def is_trough(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a confirmed swing trough."""
        logger.info("Evaluating ZigZag is_trough at shift=%d", shift)
        return is_lower(swing_type, -SWING_THRESHOLD, shift1=shift, round_digits=8)

    @classmethod
    def is_swing(cls, swing_type: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is any confirmed swing point."""
        logger.info("Evaluating ZigZag is_swing at shift=%d", shift)
        return is_greater(
            swing_type, SWING_THRESHOLD, shift1=shift, round_digits=8
        ) or is_lower(swing_type, -SWING_THRESHOLD, shift1=shift, round_digits=8)

    @classmethod
    def last_swing_direction(cls, swing_type: IndicatorSeries, shift: int = 0) -> int:
        """Returns +1 if most recent swing was a peak, -1 if trough, 0 if none."""
        logger.info("Evaluating ZigZag last_swing_direction at shift=%d", shift)
        n = len(swing_type)
        for s in range(shift, n):
            if is_greater(swing_type, SWING_THRESHOLD, shift1=s, round_digits=8):
                return 1
            if is_lower(swing_type, -SWING_THRESHOLD, shift1=s, round_digits=8):
                return -1
        return 0

    @classmethod
    def is_rising(cls, zigzag: IndicatorSeries, shift: int = 0) -> bool:
        """True if zigzag line is rising between shift+1 and shift."""
        logger.info("Evaluating ZigZag is_rising at shift=%d", shift)
        return is_rising(zigzag, shift=shift)

    @classmethod
    def is_falling(cls, zigzag: IndicatorSeries, shift: int = 0) -> bool:
        """True if zigzag line is falling between shift+1 and shift."""
        logger.info("Evaluating ZigZag is_falling at shift=%d", shift)
        return is_falling(zigzag, shift=shift)
