"""TrueStrengthIndicator indicator.

- Calculates William Blau's True Strength Index (TSI) based on double-smoothed
  momentum divided by double-smoothed absolute momentum.
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
_SCALE_100: float = 100.0


class TrueStrengthIndicator(BaseIndicator):
    """True Strength Indicator (TSI) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.true_strength_indicator",
        version="1.0.0",
        name="True Strength Indicator",
        description="Double-smoothed momentum oscillator tracking extremes",
        category="momentum",
        tags=("momentum", "oscillator", "tsi", "blau"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("tsi", PortType.SERIES, "TSI Line"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=45,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "long_period": {"type": "int", "min": 5, "max": 50, "default": 25},
            "short_period": {"type": "int", "min": 2, "max": 30, "default": 13},
            "signal_period": {"type": "int", "min": 2, "max": 30, "default": 7},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    long_period: int = Field(
        default=25,
        ge=1,
        title="Long period",
        description="Number of bars in the long window",
    )

    short_period: int = Field(
        default=13,
        ge=1,
        title="Short period",
        description="Number of bars in the short window",
    )

    signal_period: int = Field(
        default=7,
        ge=1,
        title="Signal period",
        description="Number of bars in the signal smoothing window",
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
        return self.long_period + self.short_period + self.signal_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute TSI and signal line."""
        logger.debug(
            "FR-indicator-calculation: TrueStrengthIndicator requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        diff = np.zeros(n, dtype=np.float64)
        diff[1:] = close[1:] - close[:-1]
        abs_diff = np.abs(diff)
        num = _safe_ema(ema_kernel(diff, self.long_period), self.short_period)
        den = _safe_ema(ema_kernel(abs_diff, self.long_period), self.short_period)
        tsi = np.full_like(close, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(num) & ~np.isnan(den) & (den > _EPSILON)
            tsi[valid] = _SCALE_100 * num[valid] / den[valid]
        signal = _safe_ema(tsi, self.signal_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated TSI for %d bars",
            len(bars),
        )
        return {
            "tsi": IndicatorSeries(tsi, name="TSI"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


# Private helpers: used only by this indicator.
def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


# Public exports.
__all__ = ["TrueStrengthIndicator"]
