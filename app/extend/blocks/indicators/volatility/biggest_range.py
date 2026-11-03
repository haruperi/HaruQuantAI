"""BiggestRange indicator.

- Identifies largest bar range in rolling lookback window.
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
from app.extend.calculators.highest import rolling_extreme

logger = get_logger(__name__)


class BiggestRange(BaseIndicator):
    """Numeric extreme of eight-decimal candle ranges over available history."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.biggest_range",
        version="1.0.0",
        name="BiggestRange",
        description="Identifies largest bar range in rolling lookback window.",
        category="volatility",
        tags=("volatility", "biggest-range"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=tuple(
            InputPort(
                key,
                PortType.SERIES,
                required=True,
                description=f"{key} input series",
            )
            for key in ("high", "low")
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=1,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {
                "type": "int",
                "values": [3, 5, 10, 14, 20, 25, 30, 40, 50],
                "default": 14,
            }
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
        """Return the existing startup requirement for this calculation."""
        return self.spec.required_history_lookback

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Return values, not a predicate about the current candle."""
        logger.debug(
            "FR-indicator-calculation: BiggestRange requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        ranges = bars.high - bars.low
        if not np.isfinite(ranges).all():
            raise ValueError("Candle ranges must be finite")
        rounded = np.floor(ranges * 100_000_000.0 + 0.5) / 100_000_000.0
        values = rolling_extreme(rounded, self.period, highest=True)
        values = np.maximum(values, 0.0)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated BiggestRange for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="BiggestRange")}


# Public exports.
__all__ = ["BiggestRange"]
