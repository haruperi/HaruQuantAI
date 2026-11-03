"""BullsPower indicator.

- Calculates Bulls Power measuring buyers' capability to push price above EMA
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


class BullsPower(BaseIndicator):
    """Bulls Power (Elder-Ray) indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.bulls_power",
        version="1.0.0",
        name="BullsPower",
        description=(
            "Calculates Bulls Power measuring buyers' capability to push "
            "price above EMA smoothing baseline."
        ),
        category="momentum",
        tags=("momentum", "bulls-power"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
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
        required_market_inputs=("high", "close"),
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
            "FR-indicator-calculation: BullsPower requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        close = bars.close
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(high_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-BULLS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        ema = ema_kernel(close_arr, period)
        res = high_arr - ema
        logger.info(
            "FR-SERVICES-BULLS-CALCULATE: Computed BullsPower(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"BullsPower({period})")}


# Public exports.
__all__ = ["BullsPower"]
