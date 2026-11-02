"""Percentage Price Oscillator (PPO) strategy block.

Description:
    Calculates the Percentage Price Oscillator (PPO) showing the percentage
    difference between two exponential moving averages, alongside a signal line.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-price-oscillator: PPO percentage oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.price_oscillator import (
        PercentagePriceOscillator,
    )
    res = PercentagePriceOscillator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
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


def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


_EPSILON: float = 1e-12
_SCALE_100: float = 100.0


class PercentagePriceOscillator(BaseIndicator):
    """Percentage Price Oscillator (PPO) block."""

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
        parameter_search_space={
            "fast_period": {"type": "int", "min": 2, "max": 50, "default": 12},
            "slow_period": {"type": "int", "min": 5, "max": 100, "default": 26},
            "signal_period": {"type": "int", "min": 2, "max": 30, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    fast_period: int = Field(default=12, ge=1)
    slow_period: int = Field(default=26, ge=1)
    signal_period: int = Field(default=9, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.fast_period, self.slow_period) + self.signal_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute PPO line, signal line, and histogram."""
        bars.require_inputs(self.spec.required_market_inputs)
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


__all__ = ["PercentagePriceOscillator"]
