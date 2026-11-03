"""FisherTransform indicator.

- Calculates John Ehlers' Fisher Transform converting normalized prices into a
  Gaussian normal distribution to pinpoint turning points with zero lag.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

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
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_CLAMP_LIMIT: float = 0.999


class FisherTransform(BaseIndicator):
    """John Ehlers Fisher Transform indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.fisher_transform",
        version="1.0.0",
        name="Fisher Transform",
        description="Converts price distribution to Gaussian normal",
        category="momentum",
        tags=("momentum", "oscillator", "fisher", "ehlers"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(
            OutputPort("fisher", PortType.SERIES, "Fisher Transform"),
            OutputPort("signal", PortType.SERIES, "Trigger Signal (1-bar lag)"),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=10,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 9}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=9,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Fisher Transform and trigger signal values."""
        logger.debug(
            "FR-indicator-calculation: FisherTransform requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        n = len(high)
        fisher = np.full(n, np.nan, dtype=np.float64)
        signal = np.full(n, np.nan, dtype=np.float64)
        if n >= self.period:
            hl2 = (high + low) / 2.0
            x_prev = 0.0
            fish_prev = 0.0
            p = self.period
            for i in range(p - 1, n):
                window = hl2[i - p + 1 : i + 1]
                min_l = np.min(window)
                max_h = np.max(window)
                denom = max_h - min_l
                raw_x = (
                    0.33 * 2.0 * ((hl2[i] - min_l) / denom - 0.5) + 0.67 * x_prev
                    if denom > _EPSILON
                    else 0.0
                )
                x_val = np.clip(raw_x, -_CLAMP_LIMIT, _CLAMP_LIMIT)
                x_prev = x_val
                fish_val = 0.5 * np.log((1.0 + x_val) / (1.0 - x_val)) + 0.5 * fish_prev
                fisher[i] = fish_val
                if i > p - 1:
                    signal[i] = fish_prev
                fish_prev = fish_val
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated Fisher(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "fisher": IndicatorSeries(fisher, name="Fisher"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


# Public exports.
__all__ = ["FisherTransform"]
