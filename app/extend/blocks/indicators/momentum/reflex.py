"""Reflex momentum indicator strategy block.

Description:
    Calculates Ehlers Reflex indicator measuring cycle turns in price trend.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Reflex cycle indicator calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.reflex import Reflex
    res = Reflex().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import math
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
from app.extend.blocks.comparisons import (
    changes_down,
    changes_up,
    crosses_above,
    crosses_below,
    is_falling,
    is_rising,
)
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_REFLEX_PERIOD: int = 2
DEFAULT_FAST_PERIOD: int = 20
DEFAULT_SLOW_PERIOD: int = 40
EPSILON: float = 1e-12
FALLBACK_DENOM: float = 1e-06


class Reflex(BaseIndicator):
    """John Ehlers' Reflex cycle indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.reflex",
        name="Reflex",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("reflex", PortType.SERIES),
            OutputPort("fast", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 80, "default": 20}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=DEFAULT_FAST_PERIOD, ge=MIN_REFLEX_PERIOD)
    slow_period: int | None = Field(default=None, ge=MIN_REFLEX_PERIOD)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_REFLEX_PERIOD:
            raise ValueError(f"period must be >= 2, got {self.period}")
        if self.slow_period is not None and self.slow_period < MIN_REFLEX_PERIOD:
            raise ValueError(f"slow_period must be >= 2, got {self.slow_period}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.period, self.slow_period or self.period)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        period = self.period
        slow_period = self.slow_period
        logger.info(
            "Reflex calculation initiated: period=%d, slow_period=%s",
            period,
            str(slow_period),
            extra={"period": period, "slow_period": slow_period},
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        fast_vals = self._compute_single_reflex(p_arr, period)
        res = {
            "reflex": IndicatorSeries(fast_vals, name=f"Reflex({period})"),
            "fast": IndicatorSeries(fast_vals, name=f"FastReflex({period})"),
        }
        if slow_period is not None:
            slow_vals = self._compute_single_reflex(p_arr, slow_period)
            res["slow"] = IndicatorSeries(slow_vals, name=f"SlowReflex({slow_period})")
        logger.info(
            "Reflex calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return res

    @staticmethod
    def _compute_single_reflex(
        p_arr: np.ndarray[Any, Any], period: int
    ) -> np.ndarray[Any, Any]:
        """Compute single-line Reflex series according to Ehlers' formula."""
        n = len(p_arr)
        reflex = np.zeros(n, dtype=np.float64)
        if n < period:
            return reflex
        filt = np.zeros(n, dtype=np.float64)
        ms = np.zeros(n, dtype=np.float64)
        arg = 1.414 * math.pi / (0.5 * period)
        a1 = math.exp(-arg)
        b1 = 2.0 * a1 * math.cos(arg)
        c2 = b1
        c3 = -a1 * a1
        c1 = 1.0 - c2 - c3
        filt[0] = p_arr[0]
        if n > 1:
            filt[1] = p_arr[1]
        for i in range(2, n):
            c_term = c1 * (p_arr[i] + p_arr[i - 1]) * 0.5
            filt[i] = c_term + c2 * filt[i - 1] + c3 * filt[i - 2]
        for i in range(period, n):
            f_curr = filt[i]
            slope = (filt[i - period] - f_curr) / period
            sum_diff = 0.0
            for k in range(1, period + 1):
                sum_diff += f_curr + k * slope - filt[i - k]
            sum_diff /= period
            ms[i] = 0.04 * sum_diff * sum_diff + 0.96 * ms[i - 1]
            denom = math.sqrt(ms[i]) if ms[i] > EPSILON else FALLBACK_DENOM
            reflex[i] = sum_diff / denom
        return reflex

    @staticmethod
    def fast_crosses_above_slow(
        fast: IndicatorSeries | np.ndarray[Any, Any],
        slow: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Fast Reflex crossed above Slow Reflex."""
        logger.info("Evaluating Reflex fast_crosses_above_slow at shift=%d", shift)
        return crosses_above(fast, slow, shift=shift)

    @staticmethod
    def fast_crosses_below_slow(
        fast: IndicatorSeries | np.ndarray[Any, Any],
        slow: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Fast Reflex crossed below Slow Reflex."""
        logger.info("Evaluating Reflex fast_crosses_below_slow at shift=%d", shift)
        return crosses_below(fast, slow, shift=shift)

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Reflex is rising."""
        logger.info("Evaluating Reflex is_rising at shift=%d", shift)
        return is_rising(series, shift=shift)

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Reflex is falling."""
        logger.info("Evaluating Reflex is_falling at shift=%d", shift)
        return is_falling(series, shift=shift)

    @staticmethod
    def changes_direction_up(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Reflex turned upward (v0 > v1 and v1 <= v2)."""
        logger.info("Evaluating Reflex changes_direction_up at shift=%d", shift)
        return changes_up(series, shift=shift)

    @staticmethod
    def changes_direction_down(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Reflex turned downward (v0 < v1 and v1 >= v2)."""
        logger.info("Evaluating Reflex changes_direction_down at shift=%d", shift)
        return changes_down(series, shift=shift)
