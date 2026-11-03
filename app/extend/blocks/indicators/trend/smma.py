"""SMMA indicator.

- Calculates Smoothed Moving Average (SMMA / Wilder's MA) rolling trend filter.
"""

from __future__ import annotations

from typing import ClassVar, override

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
from app.extend.calculators.average import smma_kernel

logger = get_logger(__name__)


class SMMA(BaseIndicator):
    """Smoothed Moving Average (Wilder's MA) indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.smma",
        version="1.0.0",
        name="Smoothed Moving Average",
        description=(
            "Calculates smoothed moving average using Wilder's smoothing algorithm"
        ),
        category="trend",
        tags=("trend", "moving_average", "smma", "wilder"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "SMMA smoothed series"),),
        required_market_inputs=("close",),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 200, "default": 20}
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
        description="Smoothing lookback period in bars",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid SMMA calculation."""
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute SMMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        logger.debug("FR-indicator-calculation: SMMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        values = smma_kernel(bars.close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated SMMA(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="SMMA")}


# Public exports.
__all__ = ["SMMA"]
