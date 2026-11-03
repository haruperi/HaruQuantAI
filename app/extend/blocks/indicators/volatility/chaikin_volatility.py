"""ChaikinVolatility indicator.

- Calculates Marc Chaikin's Volatility indicator measuring the percentage rate of
  change of the exponential moving average of the high-low spread.
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

_SCALE_100: float = 100.0
_EPSILON: float = 1e-12


class ChaikinVolatility(BaseIndicator):
    """Chaikin Volatility indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.chaikin_volatility",
        version="1.0.0",
        name="Chaikin Volatility",
        description="Percentage rate of change of EMA of High-Low range",
        category="volatility",
        tags=("volatility", "chaikin", "range"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Chaikin Volatility"),),
        required_market_inputs=("high", "low"),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "ema_period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "roc_period": {"type": "int", "min": 2, "max": 50, "default": 10},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    ema_period: int = Field(
        default=10,
        ge=1,
        title="Ema period",
        description="Number of bars in the ema window",
    )

    roc_period: int = Field(
        default=10,
        ge=1,
        title="Roc period",
        description="Number of bars in the roc window",
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
        return self.ema_period + self.roc_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Chaikin Volatility values."""
        logger.debug(
            "FR-indicator-calculation: ChaikinVolatility requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        n = len(high)
        hl_ema = ema_kernel(high - low, self.ema_period)
        cv = np.full(n, np.nan, dtype=np.float64)
        p = self.roc_period
        if n > p:
            with np.errstate(divide="ignore", invalid="ignore"):
                for i in range(p, n):
                    prev = hl_ema[i - p]
                    curr = hl_ema[i]
                    if not np.isnan(prev) and not np.isnan(curr) and prev > _EPSILON:
                        cv[i] = _SCALE_100 * (curr - prev) / prev
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated ChaikinVol(%d, %d) for %d",
            self.ema_period,
            self.roc_period,
            len(bars),
        )
        return {"value": IndicatorSeries(cv, name="ChaikinVol")}


# Public exports.
__all__ = ["ChaikinVolatility"]
