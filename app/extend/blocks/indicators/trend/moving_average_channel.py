"""MovingAverageChannel indicator.

- Calculates a price channel constructed from simple moving averages applied
  separately to high and low prices.
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class MovingAverageChannel(BaseIndicator):
    """Moving Average Channel block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.moving_average_channel",
        version="1.0.0",
        name="Moving Average Channel",
        description="High and low price moving average channel",
        category="trend",
        tags=("trend", "channel", "ma", "moving_average"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Channel (High MA)"),
            OutputPort("lower", PortType.SERIES, "Lower Channel (Low MA)"),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=20,
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Upper and Lower Moving Average Channel lines."""
        logger.debug(
            "FR-indicator-calculation: MovingAverageChannel requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        upper = sma_kernel(high, self.period)
        lower = sma_kernel(low, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated MAChannel(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "upper": IndicatorSeries(upper, name="MAChannel.Upper"),
            "lower": IndicatorSeries(lower, name="MAChannel.Lower"),
        }


# Public exports.
__all__ = ["MovingAverageChannel"]
