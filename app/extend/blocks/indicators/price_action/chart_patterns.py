"""ChartPatterns price_action indicator strategy block.

Description:
    Detects geometric classical chart formations and channel breakouts.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator library.
Key Capabilities:
    - FR-indicator-price-action: Chart pattern recognition.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.price_action.chart_patterns import (
        ChartPatterns,
    )
    res = ChartPatterns().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import is_lower
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_CHART_LOOKBACK: int = 10
DEFAULT_CHART_LOOKBACK: int = 50
DEFAULT_TOLERANCE_PCT: float = 0.03
PATTERN_THRESHOLD: float = 0.5
EPSILON: float = 1e-12


class ChartPatterns(BaseIndicator):
    """Multi-structural chart pattern recognizer."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.chart_patterns",
        name="ChartPatterns",
        category="price_action",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("double_pattern", PortType.SERIES),
            OutputPort("breakout_retest", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "lookback": {"type": "int", "min": 10, "max": 200, "default": 50},
            "tolerance_pct": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.03,
                "min_exclusive": True,
                "max_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=50,
    )
    lookback: int = Field(default=DEFAULT_CHART_LOOKBACK, ge=MIN_CHART_LOOKBACK)
    tolerance_pct: float = Field(default=DEFAULT_TOLERANCE_PCT, lt=1.0, gt=0.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.lookback < MIN_CHART_LOOKBACK:
            raise ValueError(
                f"lookback must be >= {MIN_CHART_LOOKBACK}, got {self.lookback}"
            )
        if self.tolerance_pct <= 0.0 or self.tolerance_pct >= 1.0:
            raise ValueError(
                f"tolerance_pct must be between 0 and 1, got {self.tolerance_pct}"
            )
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.lookback

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        lookback = self.lookback
        tolerance_pct = self.tolerance_pct
        logger.info(
            "ChartPatterns.calculate called: lookback=%d, tol=%.2f",
            lookback,
            tolerance_pct,
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        double_pat, breakout_pat = self._compute_chart_patterns(
            (h_arr, l_arr, c_arr), lookback, tolerance_pct
        )
        logger.info("ChartPatterns completed: bars=%d", n)
        return {
            "double_pattern": IndicatorSeries(
                double_pat, name=f"DoublePattern({lookback})"
            ),
            "breakout_retest": IndicatorSeries(
                breakout_pat, name=f"BreakoutRetest({lookback})"
            ),
        }

    @classmethod
    def _compute_chart_patterns(
        cls,
        prices: tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]],
        lookback: int,
        tolerance_pct: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        double_pat = np.zeros(n, dtype=np.float64)
        breakout_pat = np.zeros(n, dtype=np.float64)
        for i in range(lookback, n):
            start = i - lookback
            w_h = h_arr[start : i + 1]
            w_l = l_arr[start : i + 1]
            w_max = float(np.max(w_h))
            w_min = float(np.min(w_l))
            rng = w_max - w_min
            tol = tolerance_pct * rng if rng > EPSILON else 0.01
            half = lookback // 2
            peak1 = float(np.max(w_h[:half]))
            peak2 = float(np.max(w_h[half:]))
            trough1 = float(np.min(w_l[:half]))
            trough2 = float(np.min(w_l[half:]))
            if abs(peak1 - peak2) <= tol and peak2 >= w_max - tol:
                double_pat[i] = -1.0
            elif abs(trough1 - trough2) <= tol and trough2 <= w_min + tol:
                double_pat[i] = 1.0
            prev_high_level = float(np.max(w_h[:-2]))
            prev_low_level = float(np.min(w_l[:-2]))
            curr_c = c_arr[i]
            curr_l = l_arr[i]
            curr_h = h_arr[i]
            if curr_c > prev_high_level and curr_l <= prev_high_level + tol:
                breakout_pat[i] = 1.0
            elif curr_c < prev_low_level and curr_h >= prev_low_level - tol:
                breakout_pat[i] = -1.0
        return (double_pat, breakout_pat)

    @classmethod
    def is_double_top(cls, double_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if double top pattern formed at shift."""
        logger.info("Evaluating ChartPatterns.is_double_top: shift=%d", shift)
        return is_lower(double_series, -PATTERN_THRESHOLD, shift1=shift, round_digits=8)

    @classmethod
    def is_double_bottom(cls, double_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if double bottom pattern formed at shift."""
        logger.info("Evaluating ChartPatterns.is_double_bottom: shift=%d", shift)
        return is_greater(
            double_series, PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )

    @classmethod
    def is_bullish_breakout(
        cls, breakout_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bullish breakout and retest occurred at shift."""
        logger.info("Evaluating ChartPatterns.is_bullish_breakout: shift=%d", shift)
        return is_greater(
            breakout_series, PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )

    @classmethod
    def is_bearish_breakout(
        cls, breakout_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bearish breakdown and retest occurred at shift."""
        logger.info("Evaluating ChartPatterns.is_bearish_breakout: shift=%d", shift)
        return is_lower(
            breakout_series, -PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )
