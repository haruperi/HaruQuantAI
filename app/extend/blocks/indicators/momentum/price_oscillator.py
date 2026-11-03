"""PercentagePriceOscillator indicator.

- Calculates the Percentage Price Oscillator (PPO) showing the percentage difference
  between two exponential moving averages, alongside a signal line.
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


class PercentagePriceOscillator(BaseIndicator):
    """Percentage Price Oscillator (PPO) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.price_oscillator",
        version="1.0.0",
        name="Percentage Price Oscillator",
        description="Percentage difference between two moving averages (PPO)",
        category="momentum",
        tags=("momentum", "oscillator", "ppo", "price_oscillator"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("ppo", PortType.SERIES, "PPO Line"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
            OutputPort("histogram", PortType.SERIES, "PPO Histogram"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=35,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "fast_period": {"type": "int", "min": 2, "max": 50, "default": 12},
            "slow_period": {"type": "int", "min": 5, "max": 100, "default": 26},
            "signal_period": {"type": "int", "min": 2, "max": 30, "default": 9},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    fast_period: int = Field(
        default=12,
        ge=1,
        title="Fast period",
        description="Number of bars in the fast smoothing window",
    )

    slow_period: int = Field(
        default=26,
        ge=1,
        title="Slow period",
        description="Number of bars in the slow smoothing window",
    )

    signal_period: int = Field(
        default=9,
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
        return max(self.fast_period, self.slow_period) + self.signal_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute PPO line, signal line, and histogram."""
        logger.debug(
            "FR-indicator-calculation: PercentagePriceOscillator requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        fast_ema = ema_kernel(close, self.fast_period)
        slow_ema = ema_kernel(close, self.slow_period)
        ppo = np.full_like(close, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = (
                ~np.isnan(fast_ema)
                & ~np.isnan(slow_ema)
                & (np.abs(slow_ema) > _EPSILON)
            )
            ppo[valid] = (
                _SCALE_100 * (fast_ema[valid] - slow_ema[valid]) / slow_ema[valid]
            )
        signal = _safe_ema(ppo, self.signal_period)
        hist = ppo - signal
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated PPO(%d, %d, %d) for %d bars",
            self.fast_period,
            self.slow_period,
            self.signal_period,
            len(bars),
        )
        return {
            "ppo": IndicatorSeries(ppo, name="PPO"),
            "signal": IndicatorSeries(signal, name="Signal"),
            "histogram": IndicatorSeries(hist, name="Histogram"),
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
__all__ = ["PercentagePriceOscillator"]
