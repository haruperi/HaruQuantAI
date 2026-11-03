"""BalanceOfPower indicator.

- Calculates Igor Livshin's Balance of Power (BOP) comparing buyer vs seller ability
  to push price to extreme levels, smoothed by a moving average.
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

_EPSILON: float = 1e-12


class BalanceOfPower(BaseIndicator):
    """Balance of Power (BOP) indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.balance_of_power",
        version="1.0.0",
        name="Balance of Power",
        description="Measures the market power of buyers versus sellers",
        category="momentum",
        tags=("momentum", "oscillator", "balance_of_power", "bop"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Balance of Power"),),
        required_market_inputs=("open", "high", "low", "close"),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 100, "default": 14}
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
        """Return minimum history bars needed for valid calculation."""
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Balance of Power values over historical bars."""
        logger.debug(
            "FR-indicator-calculation: BalanceOfPower requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        open_arr = np.asarray(bars.open, dtype=np.float64)
        high_arr = np.asarray(bars.high, dtype=np.float64)
        low_arr = np.asarray(bars.low, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        hl_range = high_arr - low_arr
        raw_bop = np.zeros_like(close_arr)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid_mask = hl_range > _EPSILON
            raw_bop[valid_mask] = (
                close_arr[valid_mask] - open_arr[valid_mask]
            ) / hl_range[valid_mask]
        bop = sma_kernel(raw_bop, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated BOP(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(bop, name="BOP")}


# Public exports.
__all__ = ["BalanceOfPower"]
