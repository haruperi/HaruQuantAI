"""HullMovingAverage indicator.

- Calculates Hull Moving Average (HMA) combining reduced lag and smooth curve.
"""

from __future__ import annotations

import math
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
from app.extend.calculators.average import lwma_kernel

logger = get_logger(__name__)


class HullMovingAverage(BaseIndicator):
    """Hull Moving Average indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.hull_moving_average",
        version="1.0.0",
        name="HullMovingAverage",
        description=(
            "Calculates Hull Moving Average (HMA) combining reduced lag and "
            "smooth curve."
        ),
        category="trend",
        tags=("trend", "hull-moving-average"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=16,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
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
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + int(self.period**0.5) - 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: HullMovingAverage requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = bars.close
        period = self.period
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)
        if period <= 1:
            logger.warning(
                "FR-SERVICES-HMA-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        fast_period = max(1, math.floor(period / 2.0))
        sqrt_period = max(1, math.floor(math.sqrt(period)))
        fast_wma = lwma_kernel(c_arr, fast_period)
        slow_wma = lwma_kernel(c_arr, period)
        diff = 2.0 * fast_wma - slow_wma
        hma = lwma_kernel(diff, sqrt_period)
        logger.info(
            "FR-SERVICES-HMA-CALCULATE: Computed HMA(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(hma, name=f"HMA({period})")}


# Public exports.
__all__ = ["HullMovingAverage"]
