"""True Strength Indicator (TSI) momentum strategy block.

Description:
    Calculates William Blau's True Strength Index (TSI) based on double-smoothed
    momentum divided by double-smoothed absolute momentum.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-true-strength-indicator: TSI computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.true_strength_indicator import (
        TrueStrengthIndicator,
    )
    res = TrueStrengthIndicator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
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


class TrueStrengthIndicator(BaseIndicator):
    """True Strength Indicator (TSI) block."""

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
        parameter_search_space={
            "long_period": {"type": "int", "min": 5, "max": 50, "default": 25},
            "short_period": {"type": "int", "min": 2, "max": 30, "default": 13},
            "signal_period": {"type": "int", "min": 2, "max": 30, "default": 7},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    long_period: int = Field(default=25, ge=1)
    short_period: int = Field(default=13, ge=1)
    signal_period: int = Field(default=7, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.long_period + self.short_period + self.signal_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute TSI and signal line."""
        bars.require_inputs(self.spec.required_market_inputs)
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


__all__ = ["TrueStrengthIndicator"]
