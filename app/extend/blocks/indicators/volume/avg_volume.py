"""AvgVolume indicator.

- Calculates rolling average volume over configurable lookback period.
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
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_PERIOD: int = 14


class AvgVolume(BaseIndicator):
    """Average Volume indicator with trend and crossover condition evaluation."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.avg_volume",
        version="1.0.0",
        name="AvgVolume",
        description=(
            "Calculates rolling average volume over configurable lookback period."
        ),
        category="volume",
        tags=("volume", "avg-volume"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "volume",
                PortType.SERIES,
                required=True,
                description="Volume input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("volume",),
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
        default=DEFAULT_PERIOD,
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
        logger.debug("FR-indicator-calculation: AvgVolume requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        volume = bars.volume
        period = self.period
        vol_arr = to_numpy(volume)
        n = len(vol_arr)
        if period < 1:
            logger.warning(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Invalid period %d, defaulting to %d",
                period,
                DEFAULT_PERIOD,
            )
            period = DEFAULT_PERIOD
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            logger.info(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return {"value": IndicatorSeries(out, name=f"AvgVolume({period})")}
        cumsum = np.cumsum(np.nan_to_num(vol_arr, nan=0.0))
        out[period - 1] = cumsum[period - 1] / period
        out[period:] = (cumsum[period:] - cumsum[:-period]) / period
        logger.info(
            "FR-SERVICES-AVGVOLUME-CALCULATE: AvgVolume(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(out, name=f"AvgVolume({period})")}


# Public exports.
__all__ = ["AvgVolume"]
