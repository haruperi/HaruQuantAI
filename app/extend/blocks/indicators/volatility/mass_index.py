"""MassIndex indicator.

- Calculates Donald Dorsey's Mass Index examining the narrowing and widening of the
  trading range between high and low prices to identify reversals.
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


_EPSILON: float = 1e-12


class MassIndex(BaseIndicator):
    """Mass Index volatility reversal block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.mass_index",
        version="1.0.0",
        name="Mass Index",
        description="Examines range expansion to detect trend reversal bulges (Dorsey)",
        category="volatility",
        tags=("volatility", "mass_index", "dorsey", "reversal"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Mass Index"),),
        required_market_inputs=("high", "low"),
        required_history_lookback=43,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "ema_period": {"type": "int", "min": 2, "max": 30, "default": 9},
            "sum_period": {"type": "int", "min": 10, "max": 50, "default": 25},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    ema_period: int = Field(
        default=9,
        ge=1,
        title="Ema period",
        description="Number of bars in the ema window",
    )

    sum_period: int = Field(
        default=25,
        ge=1,
        title="Sum period",
        description="Number of bars in the sum window",
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
        return (self.ema_period * 2) + self.sum_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Mass Index values."""
        logger.debug("FR-indicator-calculation: MassIndex requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        hl = high - low
        ema1 = ema_kernel(hl, self.ema_period)
        ema2 = _safe_ema(ema1, self.ema_period)
        ratio = np.full_like(hl, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(ema1) & ~np.isnan(ema2) & (ema2 > _EPSILON)
            ratio[valid] = ema1[valid] / ema2[valid]
        mi = _rolling_sum_valid(ratio, self.sum_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated MassIndex for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(mi, name="MassIndex")}


# Private helpers: used only by this indicator.
def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


def _rolling_sum_valid(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    for i in range(p - 1, n):
        window = x[i - p + 1 : i + 1]
        if not np.any(np.isnan(window)):
            res[i] = np.sum(window)
    return res


# Public exports.
__all__ = ["MassIndex"]
