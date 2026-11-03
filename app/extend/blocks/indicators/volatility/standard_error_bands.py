"""StandardErrorBands indicator.

- Calculates Standard Error Bands around a Linear Regression curve with specified
  standard error envelope multipliers.
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
from app.extend.blocks.indicators.trend.lin_reg import LinReg
from app.extend.blocks.indicators.volatility.standard_error import (
    standard_error_kernel,
)

logger = get_logger(__name__)


class StandardErrorBands(BaseIndicator):
    """Standard Error Bands block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.standard_error_bands",
        version="1.0.0",
        name="Standard Error Bands",
        description="Linear regression curve with standard error envelope bands",
        category="volatility",
        tags=("volatility", "bands", "standard_error", "linreg"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Standard Error Band"),
            OutputPort("middle", PortType.SERIES, "Middle Linear Regression Line"),
            OutputPort("lower", PortType.SERIES, "Lower Standard Error Band"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 3, "max": 100, "default": 20},
            "multiplier": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=20,
        ge=3,
        title="Period",
        description="Number of bars in the calculation window",
    )

    multiplier: float = Field(
        default=2.0,
        gt=0.0,
        title="Multiplier",
        description="Multiplier used by the indicator calculation",
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
        """Compute Standard Error Bands."""
        logger.debug(
            "FR-indicator-calculation: StandardErrorBands requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        middle = LinReg(period=self.period).calculate(bars)["lin_reg"].values
        se = standard_error_kernel(close, self.period)
        upper = middle + self.multiplier * se
        lower = middle - self.multiplier * se
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated SEB(%d, %.2f) for %d bars",
            self.period,
            self.multiplier,
            len(bars),
        )
        return {
            "upper": IndicatorSeries(upper, name="SEB.Upper"),
            "middle": IndicatorSeries(middle, name="SEB.Middle"),
            "lower": IndicatorSeries(lower, name="SEB.Lower"),
        }


# Public exports.
__all__ = ["StandardErrorBands"]
