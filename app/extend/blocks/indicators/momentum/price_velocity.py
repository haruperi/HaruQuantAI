"""PriceVelocity momentum indicator strategy block.

Description:
    Calculates price change velocity per bar over lookback window.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Price velocity calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.price_velocity import PriceVelocity
    res = PriceVelocity().calculate(bars)
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
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_VELOCITY_PERIOD: int = 1
DEFAULT_VELOCITY_PERIOD: int = 10
DEFAULT_SMOOTH_PERIOD: int = 1
PERCENT_MULTIPLIER: float = 100.0
EPSILON: float = 1e-12


class PriceVelocity(BaseIndicator):
    """Price velocity and momentum acceleration indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.price_velocity",
        name="PriceVelocity",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("velocity", PortType.SERIES),
            OutputPort("normalized", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 40, "default": 10},
            "smooth_period": {"type": "int", "min": 1, "max": 4, "default": 1},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=11,
    )
    period: int = Field(default=DEFAULT_VELOCITY_PERIOD, ge=MIN_VELOCITY_PERIOD)
    smooth_period: int = Field(default=DEFAULT_SMOOTH_PERIOD, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_VELOCITY_PERIOD:
            raise ValueError(
                f"period must be >= {MIN_VELOCITY_PERIOD}, got {self.period}"
            )
        if self.smooth_period < 1:
            raise ValueError(f"smooth_period must be >= 1, got {self.smooth_period}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + self.smooth_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        period = self.period
        smooth_period = self.smooth_period
        logger.info(
            "PriceVelocity initiated: period=%d, smooth=%d", period, smooth_period
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Price array cannot be empty")
        vel, norm = self._compute_velocity(p_arr, period, smooth_period, n)
        logger.info("PriceVelocity completed: bars=%d", n)
        return {
            "velocity": IndicatorSeries(vel, name=f"PriceVelocity({period})"),
            "normalized": IndicatorSeries(norm, name=f"PriceVelocityNorm({period})"),
        }

    @classmethod
    def _compute_velocity(
        cls, p_arr: np.ndarray[Any, Any], period: int, smooth_period: int, n: int
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        raw_vel = np.zeros(n, dtype=np.float64)
        raw_norm = np.zeros(n, dtype=np.float64)
        for i in range(n):
            past_idx = max(0, i - period)
            span = i - past_idx
            if span > 0:
                past_val = p_arr[past_idx]
                diff = p_arr[i] - past_val
                raw_vel[i] = diff / float(span)
                if abs(past_val) > EPSILON:
                    raw_norm[i] = diff / past_val / float(span) * PERCENT_MULTIPLIER
                else:
                    raw_norm[i] = 0.0
        if smooth_period > 1:
            vel = cls._smooth_series(raw_vel, smooth_period, n)
            norm = cls._smooth_series(raw_norm, smooth_period, n)
        else:
            vel = raw_vel
            norm = raw_norm
        return (vel, norm)

    @staticmethod
    def _smooth_series(
        data: np.ndarray[Any, Any], smooth_period: int, n: int
    ) -> np.ndarray[Any, Any]:
        smoothed = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - smooth_period + 1)
            window_len = i - start + 1
            smoothed[i] = float(np.sum(data[start : i + 1])) / window_len
        return smoothed

    @classmethod
    def is_accelerating_up(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is positive and rising (upward acceleration)."""
        logger.info("Evaluating PriceVelocity is_accelerating_up at shift=%d", shift)
        return is_greater(velocity, 0.0, shift=shift) and is_rising(
            velocity, bars=2, shift=shift
        )

    @classmethod
    def is_accelerating_down(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is negative and falling (downward acceleration)."""
        logger.info("Evaluating PriceVelocity is_accelerating_down at shift=%d", shift)
        return is_lower(velocity, 0.0, shift=shift) and is_falling(
            velocity, bars=2, shift=shift
        )

    @classmethod
    def crosses_above_zero(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity crosses above zero at shift."""
        logger.info("Evaluating PriceVelocity crosses_above_zero at shift=%d", shift)
        return crosses_above(velocity, 0.0, shift=shift)

    @classmethod
    def crosses_below_zero(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity crosses below zero at shift."""
        logger.info("Evaluating PriceVelocity crosses_below_zero at shift=%d", shift)
        return crosses_below(velocity, 0.0, shift=shift)

    @classmethod
    def is_rising(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is rising between shift+1 and shift."""
        logger.info("Evaluating PriceVelocity is_rising at shift=%d", shift)
        return is_rising(velocity, shift=shift)

    @classmethod
    def is_falling(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is falling between shift+1 and shift."""
        logger.info("Evaluating PriceVelocity is_falling at shift=%d", shift)
        return is_falling(velocity, shift=shift)
