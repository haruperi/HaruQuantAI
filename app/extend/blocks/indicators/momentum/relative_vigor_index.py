"""RelativeVigorIndex indicator.

- Calculates John Ehlers' Relative Vigor Index (RVI) measuring the conviction of
  recent price action using triangular weighted moving averages.
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


_EPSILON: float = 1e-12
_SWMA_BARS: int = 4
_SWMA_DIVISOR: float = 6.0


class RelativeVigorIndex(BaseIndicator):
    """Relative Vigor Index (RVI) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.relative_vigor_index",
        version="1.0.0",
        name="Relative Vigor Index",
        description="Measures energy and conviction of closing prices",
        category="momentum",
        tags=("momentum", "oscillator", "rvi", "ehlers"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("rvi", PortType.SERIES, "RVI Line"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
        ),
        required_market_inputs=("open", "high", "low", "close"),
        required_history_lookback=17,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 10}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=10,
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
        return self.period + 7

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute RVI and signal line."""
        logger.debug(
            "FR-indicator-calculation: RelativeVigorIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        open_arr = np.asarray(bars.open, dtype=np.float64)
        high_arr = np.asarray(bars.high, dtype=np.float64)
        low_arr = np.asarray(bars.low, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        num = _swma(close_arr - open_arr)
        den = _swma(high_arr - low_arr)
        rvi = np.full_like(close_arr, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            num_sma = _safe_sma(num, self.period)
            den_sma = _safe_sma(den, self.period)
            valid = ~np.isnan(num_sma) & ~np.isnan(den_sma) & (den_sma > _EPSILON)
            rvi[valid] = num_sma[valid] / den_sma[valid]
        signal = _swma(rvi)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated RVI(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "rvi": IndicatorSeries(rvi, name="RVI"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


# Private helpers: used only by this indicator.
def _safe_sma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = sma_kernel(x[start:], period)
    return out


def _swma(x: np.ndarray) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    if n >= _SWMA_BARS:
        res[3:] = (x[3:] + 2.0 * x[2:-1] + 2.0 * x[1:-2] + x[:-3]) / _SWMA_DIVISOR
    return res


# Public exports.
__all__ = ["RelativeVigorIndex"]
