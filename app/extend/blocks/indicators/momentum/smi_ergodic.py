"""SMIErgodic indicator.

- Calculates William Blau's SMI Ergodic indicator based on double-smoothed true
  strength momentum with a signal oscillator line.
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


class SMIErgodic(BaseIndicator):
    """SMI Ergodic Indicator / Oscillator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.smi_ergodic",
        version="1.0.0",
        name="SMI Ergodic Indicator/Oscillator",
        description="Double-smoothed momentum indicator and signal oscillator",
        category="momentum",
        tags=("momentum", "oscillator", "smi", "ergodic", "blau"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("smi", PortType.SERIES, "SMI Ergodic Line"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
            OutputPort("oscillator", PortType.SERIES, "Ergodic Oscillator"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=30,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "long_period": {"type": "int", "min": 5, "max": 50, "default": 20},
            "short_period": {"type": "int", "min": 2, "max": 20, "default": 5},
            "signal_period": {"type": "int", "min": 2, "max": 20, "default": 5},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    long_period: int = Field(
        default=20,
        ge=1,
        title="Long period",
        description="Number of bars in the long window",
    )

    short_period: int = Field(
        default=5,
        ge=1,
        title="Short period",
        description="Number of bars in the short window",
    )

    signal_period: int = Field(
        default=5,
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
        """Compute SMI Ergodic, signal line, and oscillator."""
        logger.debug(
            "FR-indicator-calculation: SMIErgodic requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        diff = np.zeros(n, dtype=np.float64)
        diff[1:] = close[1:] - close[:-1]
        abs_diff = np.abs(diff)
        num = _double_ema(diff, self.long_period, self.short_period)
        den = _double_ema(abs_diff, self.long_period, self.short_period)
        smi = np.full_like(close, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(num) & ~np.isnan(den) & (den > _EPSILON)
            smi[valid] = num[valid] / den[valid]
        signal = _safe_ema(smi, self.signal_period)
        osc = smi - signal
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated SMI Ergodic for %d bars",
            len(bars),
        )
        return {
            "smi": IndicatorSeries(smi, name="SMI"),
            "signal": IndicatorSeries(signal, name="Signal"),
            "oscillator": IndicatorSeries(osc, name="Oscillator"),
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


def _double_ema(x: np.ndarray, r: int, s: int) -> np.ndarray:
    return _safe_ema(ema_kernel(x, r), s)


# Public exports.
__all__ = ["SMIErgodic"]
