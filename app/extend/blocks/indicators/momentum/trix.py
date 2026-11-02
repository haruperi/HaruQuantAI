"""TRIX momentum indicator strategy block.

Description:
    Calculates TRIX as the 1-period percentage rate of change of a triple
    exponentially smoothed moving average, removing cyclical noise.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-trix: TRIX oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.trix import TRIX
    res = TRIX().calculate(bars)
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
from app.extend.calculators.average import ema_kernel, sma_kernel

logger = get_logger(__name__)


def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


def _safe_sma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = sma_kernel(x[start:], period)
    return out


_EPSILON: float = 1e-12
_SCALE_10000: float = 10000.0


class TRIX(BaseIndicator):
    """TRIX momentum oscillator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.trix",
        version="1.0.0",
        name="TRIX",
        description="1-period ROC of triple-smoothed EMA",
        category="momentum",
        tags=("momentum", "oscillator", "trix"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("trix", PortType.SERIES, "TRIX Line"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 18},
            "signal_period": {"type": "int", "min": 2, "max": 30, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=18, ge=1)
    signal_period: int = Field(default=9, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return (self.period * 3) + self.signal_period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute TRIX and signal line."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        ema1 = ema_kernel(close, self.period)
        ema2 = _safe_ema(ema1, self.period)
        ema3 = _safe_ema(ema2, self.period)
        trix = np.full(n, np.nan, dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            for i in range(1, n):
                if (
                    not np.isnan(ema3[i])
                    and not np.isnan(ema3[i - 1])
                    and abs(ema3[i - 1]) > _EPSILON
                ):
                    trix[i] = _SCALE_10000 * (ema3[i] - ema3[i - 1]) / ema3[i - 1]
        signal = _safe_sma(trix, self.signal_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated TRIX(%d, %d) for %d bars",
            self.period,
            self.signal_period,
            len(bars),
        )
        return {
            "trix": IndicatorSeries(trix, name="TRIX"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


__all__ = ["TRIX"]
