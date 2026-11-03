"""AwesomeOscillator indicator.

- Calculates Awesome Oscillator (AO) as the difference between 5-period and
  34-period SMAs of median prices.
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


class AwesomeOscillator(BaseIndicator):
    """Awesome Oscillator indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.awesome_oscillator",
        version="1.0.0",
        name="AwesomeOscillator",
        description=(
            "Calculates Awesome Oscillator (AO) as the difference between "
            "5-period and 34-period SMAs of median prices."
        ),
        category="momentum",
        tags=("momentum", "awesome-oscillator"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=34,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "fast_period": {"type": "int", "min": 1, "max": 20, "default": 5},
            "slow_period": {"type": "int", "min": 1, "max": 136, "default": 34},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    fast_period: int = Field(
        default=5,
        ge=1,
        title="Fast period",
        description="Number of bars in the fast smoothing window",
    )

    slow_period: int = Field(
        default=34,
        ge=1,
        title="Slow period",
        description="Number of bars in the slow smoothing window",
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
        return max(self.fast_period, self.slow_period)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: AwesomeOscillator requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        fast_period = self.fast_period
        slow_period = self.slow_period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if fast_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid fast_period %d, defaulting to 5",
                fast_period,
            )
            fast_period = 5
        if slow_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid slow_period %d, defaulting to 34",
                slow_period,
            )
            slow_period = 34
        median = (high_arr + low_arr) / 2.0
        fast_sma = sma_kernel(median, fast_period)
        slow_sma = sma_kernel(median, slow_period)
        res = fast_sma - slow_sma
        logger.info(
            "FR-SERVICES-AWO-CALCULATE: Computed AWO(fast=%d, slow=%d) for %d bars",
            fast_period,
            slow_period,
            n,
        )
        return {"value": IndicatorSeries(res, name="AwesomeOscillator")}


# Public exports.
__all__ = ["AwesomeOscillator"]
