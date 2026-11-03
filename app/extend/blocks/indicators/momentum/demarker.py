"""DeMarker indicator.

- Calculates DeMarker indicator evaluating high/low price momentum exhaustion.
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


class DeMarker(BaseIndicator):
    """DeMarker oscillator indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.demarker",
        version="1.0.0",
        name="DeMarker",
        description=(
            "Calculates DeMarker indicator evaluating high/low price momentum"
            " exhaustion."
        ),
        category="momentum",
        tags=("momentum", "demarker"),
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
        required_history_lookback=15,
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
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: DeMarker requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-DEMARKER-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        de_max = np.zeros(n, dtype=np.float64)
        de_min = np.zeros(n, dtype=np.float64)
        if n > 1:
            diff_h = high_arr[1:] - high_arr[:-1]
            diff_l = low_arr[:-1] - low_arr[1:]
            de_max[1:] = np.maximum(diff_h, 0.0)
            de_min[1:] = np.maximum(diff_l, 0.0)
        avg_de_max = sma_kernel(de_max, period)
        avg_de_min = sma_kernel(de_min, period)
        denom = avg_de_max + avg_de_min
        res = np.zeros(n, dtype=np.float64)
        valid = (denom != 0.0) & ~np.isnan(denom)
        res[valid] = avg_de_max[valid] / denom[valid]
        logger.info(
            "FR-SERVICES-DEMARKER-CALCULATE: Computed DeMarker(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"DeMarker({period})")}


# Public exports.
__all__ = ["DeMarker"]
