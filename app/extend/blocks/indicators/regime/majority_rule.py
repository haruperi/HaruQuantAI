"""MajorityRule indicator.

- Aggregates multi-indicator trend consensus by calculating the majority vote among
  short, medium, and long moving average alignments.
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


class MajorityRule(BaseIndicator):
    """Majority Rule multi-period voting consensus block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.majority_rule",
        version="1.0.0",
        name="Majority Rule",
        description="Multi-timeframe moving average voting consensus indicator",
        category="regime",
        tags=("regime", "voting", "majority_rule", "consensus"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Majority Vote (-1, 0, +1)"),),
        required_market_inputs=("close",),
        required_history_lookback=50,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period1": {"type": "int", "min": 2, "max": 50, "default": 10},
            "period2": {"type": "int", "min": 5, "max": 100, "default": 20},
            "period3": {"type": "int", "min": 10, "max": 200, "default": 50},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period1: int = Field(
        default=10,
        ge=1,
        title="Period1",
        description="Number of bars in the first calculation window",
    )

    period2: int = Field(
        default=20,
        ge=1,
        title="Period2",
        description="Number of bars in the second calculation window",
    )

    period3: int = Field(
        default=50,
        ge=1,
        title="Period3",
        description="Number of bars in the third calculation window",
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
        return max(self.period1, self.period2, self.period3)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Majority Rule consensus direction."""
        logger.debug(
            "FR-indicator-calculation: MajorityRule requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        sma1 = sma_kernel(close, self.period1)
        sma2 = sma_kernel(close, self.period2)
        sma3 = sma_kernel(close, self.period3)
        v1 = np.where(close > sma1, 1.0, np.where(close < sma1, -1.0, 0.0))
        v2 = np.where(close > sma2, 1.0, np.where(close < sma2, -1.0, 0.0))
        v3 = np.where(close > sma3, 1.0, np.where(close < sma3, -1.0, 0.0))
        total = v1 + v2 + v3
        vote = np.where(total > 0.0, 1.0, np.where(total < 0.0, -1.0, 0.0))
        max_p = max(self.period1, self.period2, self.period3)
        vote[: max_p - 1] = np.nan
        logger.debug(
            "FR-SERVICES-INDICATOR-REGIME: Calculated MajorityRule for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(vote, name="MajorityRule")}


# Public exports.
__all__ = ["MajorityRule"]
