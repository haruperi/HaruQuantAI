"""TrendStrengthIndex indicator.

- Calculates the Trend Strength Index measuring cumulative directional price
  displacement normalized by absolute price movement over a lookback window.
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

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_SCALE_100: float = 100.0


class TrendStrengthIndex(BaseIndicator):
    """Trend Strength Index block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.trend_strength_index",
        version="1.0.0",
        name="Trend Strength Index",
        description="Quantifies directional trend persistence and power",
        category="trend",
        tags=("trend", "strength", "directional"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Trend Strength Index"),),
        required_market_inputs=("close",),
        required_history_lookback=21,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20}
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

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Trend Strength Index values."""
        logger.debug(
            "FR-indicator-calculation: TrendStrengthIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        tsi = np.full(n, np.nan, dtype=np.float64)
        p = self.period
        if n > p:
            diff = np.diff(close)
            abs_diff = np.abs(diff)
            diff_cs = np.insert(np.cumsum(diff), 0, 0.0)
            abs_cs = np.insert(np.cumsum(abs_diff), 0, 0.0)
            net_move = diff_cs[p:] - diff_cs[:-p]
            tot_move = abs_cs[p:] - abs_cs[:-p]
            with np.errstate(divide="ignore", invalid="ignore"):
                val = np.where(
                    tot_move > _EPSILON, _SCALE_100 * net_move / tot_move, 0.0
                )
            tsi[p:] = val
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated TrendStrength(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(tsi, name="TSI_Trend")}


# Public exports.
__all__ = ["TrendStrengthIndex"]
