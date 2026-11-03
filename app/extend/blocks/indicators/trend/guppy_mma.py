"""GuppyMMA indicator.

- Calculates Daryl Guppy's 12-EMA ribbon consisting of 6 short-term trader EMAs (3,
  5, 8, 10, 12, 15) and 6 long-term investor EMAs (30, 35, 40, 45, 50, 60).
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

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

_FAST_PERIODS: tuple[int, ...] = (3, 5, 8, 10, 12, 15)
_SLOW_PERIODS: tuple[int, ...] = (30, 35, 40, 45, 50, 60)


class GuppyMMA(BaseIndicator):
    """Guppy Multiple Moving Average (GMMA) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.guppy_mma",
        version="1.0.0",
        name="Guppy Multiple Moving Average",
        description="12-EMA ribbon tracking trader and investor agreement",
        category="trend",
        tags=("trend", "ma", "guppy", "gmma", "ribbon"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("fast_avg", PortType.SERIES, "Fast Ribbon Average"),
            OutputPort("slow_avg", PortType.SERIES, "Slow Ribbon Average"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=60,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={},
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
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
        return max(_SLOW_PERIODS)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Guppy Multiple Moving Average ribbon outputs."""
        logger.debug("FR-indicator-calculation: GuppyMMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        fast_emas = [ema_kernel(close, p) for p in _FAST_PERIODS]
        slow_emas = [ema_kernel(close, p) for p in _SLOW_PERIODS]
        fast_avg = np.mean(np.array(fast_emas), axis=0)
        slow_avg = np.mean(np.array(slow_emas), axis=0)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated GMMA for %d bars",
            len(bars),
        )
        return {
            "fast_avg": IndicatorSeries(fast_avg, name="GMMA.Fast"),
            "slow_avg": IndicatorSeries(slow_avg, name="GMMA.Slow"),
        }


# Public exports.
__all__ = ["GuppyMMA"]
