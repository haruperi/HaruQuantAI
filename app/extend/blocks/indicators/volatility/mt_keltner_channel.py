"""MTKeltnerChannel indicator.

- Calculates Multi-Timeframe Keltner Channel envelope projection.
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


class MTKeltnerChannel(BaseIndicator):
    """MetaTrader Keltner Channel indicator family (Close-based middle band)."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.mt_keltner_channel",
        version="1.0.0",
        name="MTKeltnerChannel",
        description="Calculates Multi-Timeframe Keltner Channel envelope projection.",
        category="volatility",
        tags=("volatility", "mt-keltner-channel"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, description="Upper output series"),
            OutputPort("middle", PortType.SERIES, description="Middle output series"),
            OutputPort("lower", PortType.SERIES, description="Lower output series"),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20},
            "deviation": {
                "type": "float",
                "min": 0.0,
                "max": 6.0,
                "default": 1.5,
                "min_exclusive": True,
            },
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
        description="Number of bars in the calculation window",
    )

    deviation: float = Field(
        default=1.5,
        gt=0.0,
        title="Deviation",
        description="Deviation used by the indicator calculation",
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
            "FR-indicator-calculation: MTKeltnerChannel requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        deviation = self.deviation
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-MTKELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20
        bar_range = high_arr - low_arr
        middle = sma_kernel(close_arr, period)
        offset = sma_kernel(bar_range, period) * deviation
        upper = middle + offset
        lower = middle - offset
        logger.info(
            "FR-SERVICES-MTKELTNER-CALCULATE: MTKC(p=%d, d=%.2f) computed for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="MTKC.Upper"),
            "middle": IndicatorSeries(middle, name="MTKC.Middle"),
            "lower": IndicatorSeries(lower, name="MTKC.Lower"),
        }


# Public exports.
__all__ = ["MTKeltnerChannel"]
