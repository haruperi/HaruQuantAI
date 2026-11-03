"""CoppockCurve indicator.

- Calculates E.S.C. Coppock's long-term momentum indicator as a 10-period weighted
  moving average of the sum of 14-period and 11-period ROC.
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
from app.extend.calculators.average import lwma_kernel

logger = get_logger(__name__)

_SCALE_100: float = 100.0


class CoppockCurve(BaseIndicator):
    """Coppock Curve momentum indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.coppock_curve",
        version="1.0.0",
        name="Coppock Curve",
        description="Long-term momentum oscillator identifying major bottom reversals",
        category="momentum",
        tags=("momentum", "oscillator", "coppock"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Coppock Curve"),),
        required_market_inputs=("close",),
        required_history_lookback=24,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "wma_period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "long_roc_period": {"type": "int", "min": 5, "max": 50, "default": 14},
            "short_roc_period": {"type": "int", "min": 5, "max": 50, "default": 11},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    wma_period: int = Field(
        default=10,
        ge=1,
        title="Wma period",
        description="Number of bars in the wma window",
    )

    long_roc_period: int = Field(
        default=14,
        ge=1,
        title="Long roc period",
        description="Number of bars in the long roc window",
    )

    short_roc_period: int = Field(
        default=11,
        ge=1,
        title="Short roc period",
        description="Number of bars in the short roc window",
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
        return max(self.long_roc_period, self.short_roc_period) + self.wma_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Coppock Curve values over historical bars."""
        logger.debug(
            "FR-indicator-calculation: CoppockCurve requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        roc_sum = np.full(n, np.nan, dtype=np.float64)
        max_roc = max(self.long_roc_period, self.short_roc_period)
        if n > max_roc:
            roc_l = np.full(n, np.nan, dtype=np.float64)
            roc_s = np.full(n, np.nan, dtype=np.float64)
            p_long = self.long_roc_period
            p_short = self.short_roc_period
            with np.errstate(divide="ignore", invalid="ignore"):
                roc_l[p_long:] = (
                    _SCALE_100 * (close[p_long:] - close[:-p_long]) / close[:-p_long]
                )
                roc_s[p_short:] = (
                    _SCALE_100 * (close[p_short:] - close[:-p_short]) / close[:-p_short]
                )
            roc_sum = roc_l + roc_s
        curve = lwma_kernel(roc_sum, self.wma_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated Coppock(%d, %d, %d) "
            "for %d bars",
            self.wma_period,
            self.long_roc_period,
            self.short_roc_period,
            len(bars),
        )
        return {"value": IndicatorSeries(curve, name="Coppock")}


# Public exports.
__all__ = ["CoppockCurve"]
