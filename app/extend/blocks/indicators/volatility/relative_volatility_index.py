"""RelativeVolatilityIndex indicator.

- Calculates Donald Dorsey's Relative Volatility Index applying standard RSI
  mechanics to standard deviation rather than daily price change.
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
from app.extend.calculators.std_dev import std_dev_kernel

logger = get_logger(__name__)

_SCALE_100: float = 100.0
_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class RelativeVolatilityIndex(BaseIndicator):
    """Relative Volatility Index (RVI) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.relative_volatility_index",
        version="1.0.0",
        name="Relative Volatility Index",
        description="RSI formula applied to Standard Deviation (Donald Dorsey)",
        category="volatility",
        tags=("volatility", "rvi", "dorsey", "std_dev"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Relative Volatility Index"),),
        required_market_inputs=("close",),
        required_history_lookback=25,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "std_period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "smooth_period": {"type": "int", "min": 2, "max": 50, "default": 14},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    std_period: int = Field(
        default=10,
        ge=1,
        title="Std period",
        description="Number of bars in the std window",
    )

    smooth_period: int = Field(
        default=14,
        ge=1,
        title="Smooth period",
        description="Number of bars in the smooth window",
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
        return self.std_period + self.smooth_period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Relative Volatility Index values."""
        logger.debug(
            "FR-indicator-calculation: RelativeVolatilityIndex requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        sd = std_dev_kernel(close, self.std_period)
        up_sd = np.zeros(n, dtype=np.float64)
        dn_sd = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            diff = close[1:] - close[:-1]
            valid_sd = sd[1:]
            up_sd[1:] = np.where(diff > 0.0, valid_sd, 0.0)
            dn_sd[1:] = np.where(diff < 0.0, valid_sd, 0.0)
        u_smooth = ema_kernel(up_sd, self.smooth_period)
        d_smooth = ema_kernel(dn_sd, self.smooth_period)
        rvi = np.full(n, np.nan, dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            total = u_smooth + d_smooth
            valid = ~np.isnan(u_smooth) & ~np.isnan(d_smooth) & (total > _EPSILON)
            rvi[valid] = _SCALE_100 * u_smooth[valid] / total[valid]
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated RVI(%d, %d) for %d bars",
            self.std_period,
            self.smooth_period,
            len(bars),
        )
        return {"value": IndicatorSeries(rvi, name="RVI_Vol")}


# Public exports.
__all__ = ["RelativeVolatilityIndex"]
