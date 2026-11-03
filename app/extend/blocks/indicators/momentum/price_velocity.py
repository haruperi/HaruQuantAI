"""PriceVelocity indicator.

- Calculates price change velocity per bar over lookback window.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
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

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.price_velocity",
        version="1.0.0",
        name="PriceVelocity",
        description="Calculates price change velocity per bar over lookback window.",
        category="momentum",
        tags=("momentum", "price-velocity"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort(
                "velocity", PortType.SERIES, description="Velocity output series"
            ),
            OutputPort(
                "normalized", PortType.SERIES, description="Normalized output series"
            ),
        ),
        required_market_inputs=("close",),
        required_history_lookback=11,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 40, "default": 10},
            "smooth_period": {"type": "int", "min": 1, "max": 4, "default": 1},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=DEFAULT_VELOCITY_PERIOD,
        ge=MIN_VELOCITY_PERIOD,
        title="Period",
        description="Number of bars in the calculation window",
    )

    smooth_period: int = Field(
        default=DEFAULT_SMOOTH_PERIOD,
        ge=1,
        title="Smooth period",
        description="Number of bars in the smooth window",
    )

    # Parameter validation: only relationships and custom constraints.
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

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + self.smooth_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: PriceVelocity requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
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

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["PriceVelocity"]
