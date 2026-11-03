"""KnowSureThing indicator.

- Calculates Martin Pring's Know Sure Thing (KST) as a four-component weighted sum
  of smoothed rate-of-change indicators with a signal line.
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


_SCALE_100: float = 100.0


class KnowSureThing(BaseIndicator):
    """Know Sure Thing (KST) oscillator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.know_sure_thing",
        version="1.0.0",
        name="Know Sure Thing",
        description="Four-component smoothed ROC rate oscillator with signal line",
        category="momentum",
        tags=("momentum", "oscillator", "kst", "pring"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("kst", PortType.SERIES, "KST Line"),
            OutputPort("signal", PortType.SERIES, "KST Signal Line"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=54,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "r1": {"type": "int", "min": 2, "max": 20, "default": 10},
            "r2": {"type": "int", "min": 5, "max": 30, "default": 15},
            "r3": {"type": "int", "min": 10, "max": 40, "default": 20},
            "r4": {"type": "int", "min": 15, "max": 60, "default": 30},
            "s1": {"type": "int", "min": 2, "max": 20, "default": 10},
            "s2": {"type": "int", "min": 2, "max": 20, "default": 10},
            "s3": {"type": "int", "min": 2, "max": 20, "default": 10},
            "s4": {"type": "int", "min": 2, "max": 30, "default": 15},
            "signal_period": {"type": "int", "min": 2, "max": 20, "default": 9},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    r1: int = Field(
        default=10,
        ge=1,
        title="R1",
        description="Rate-of-change lookback for component 1, in bars",
    )

    r2: int = Field(
        default=15,
        ge=1,
        title="R2",
        description="Rate-of-change lookback for component 2, in bars",
    )

    r3: int = Field(
        default=20,
        ge=1,
        title="R3",
        description="Rate-of-change lookback for component 3, in bars",
    )

    r4: int = Field(
        default=30,
        ge=1,
        title="R4",
        description="Rate-of-change lookback for component 4, in bars",
    )

    s1: int = Field(
        default=10,
        ge=1,
        title="S1",
        description="Smoothing window for component 1, in bars",
    )

    s2: int = Field(
        default=10,
        ge=1,
        title="S2",
        description="Smoothing window for component 2, in bars",
    )

    s3: int = Field(
        default=10,
        ge=1,
        title="S3",
        description="Smoothing window for component 3, in bars",
    )

    s4: int = Field(
        default=15,
        ge=1,
        title="S4",
        description="Smoothing window for component 4, in bars",
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
        max_lookback = max(
            self.r1 + self.s1,
            self.r2 + self.s2,
            self.r3 + self.s3,
            self.r4 + self.s4,
        )
        return max_lookback + self.signal_period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute KST line and signal line."""
        logger.debug(
            "FR-indicator-calculation: KnowSureThing requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        rc1 = _safe_sma(_roc(close, self.r1), self.s1)
        rc2 = _safe_sma(_roc(close, self.r2), self.s2)
        rc3 = _safe_sma(_roc(close, self.r3), self.s3)
        rc4 = _safe_sma(_roc(close, self.r4), self.s4)
        kst = rc1 * 1.0 + rc2 * 2.0 + rc3 * 3.0 + rc4 * 4.0
        signal = _safe_sma(kst, self.signal_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated KST for %d bars",
            len(bars),
        )
        return {
            "kst": IndicatorSeries(kst, name="KST"),
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


def _roc(close: np.ndarray, period: int) -> np.ndarray:
    n = len(close)
    res = np.full(n, np.nan, dtype=np.float64)
    if n > period:
        with np.errstate(divide="ignore", invalid="ignore"):
            res[period:] = (
                _SCALE_100 * (close[period:] - close[:-period]) / close[:-period]
            )
    return res


# Public exports.
__all__ = ["KnowSureThing"]
