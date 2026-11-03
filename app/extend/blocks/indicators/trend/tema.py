"""TEMA indicator.

- Calculates Triple Exponential Moving Average (TEMA) minimizing lag via triple
  smoothing.
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
from app.extend.calculators.average import tema_kernel

logger = get_logger(__name__)


class TEMA(BaseIndicator):
    """Triple Exponential Moving Average indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.tema",
        version="1.0.0",
        name="Triple Exponential Moving Average",
        description=(
            "Calculates triple smoothed exponential moving average reducing "
            "lag (3*EMA1 - 3*EMA2 + EMA3)"
        ),
        category="trend",
        tags=("trend", "moving_average", "tema"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "TEMA smoothed series"),),
        required_market_inputs=("close",),
        required_history_lookback=40,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 200, "default": 14}
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
        """Return minimum history bars needed for the first valid TEMA calculation."""
        return 3 * self.period - 2

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute TEMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        logger.debug("FR-indicator-calculation: TEMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        values = tema_kernel(bars.close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated TEMA(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="TEMA")}


# Public exports.
__all__ = ["TEMA"]
