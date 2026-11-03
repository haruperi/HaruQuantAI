"""BearsPower indicator.

- Calculates Bears Power measuring sellers' capability to push price below EMA
  smoothing baseline.
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
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


class BearsPower(BaseIndicator):
    """Bears Power (Elder-Ray) indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.bears_power",
        version="1.0.0",
        name="BearsPower",
        description=(
            "Calculates Bears Power measuring sellers' capability to push "
            "price below EMA smoothing baseline."
        ),
        category="momentum",
        tags=("momentum", "bears-power"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
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
        required_market_inputs=("low", "close"),
        required_history_lookback=14,
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: BearsPower requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        low = bars.low
        close = bars.close
        period = self.period
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(low_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-BEARS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        ema = ema_kernel(close_arr, period)
        res = low_arr - ema
        logger.info(
            "FR-SERVICES-BEARS-CALCULATE: Computed BearsPower(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"BearsPower({period})")}


# Public exports.
__all__ = ["BearsPower"]
