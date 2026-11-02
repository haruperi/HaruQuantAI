"""Stochastic RSI momentum indicator strategy block.

Description:
    Calculates Stochastic RSI (StochRSI) by applying the classical Stochastic
    oscillator formula directly to Relative Strength Index values.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-stochastic-rsi: Stochastic RSI computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.stochastic_rsi import StochasticRSI
    res = StochasticRSI().calculate(bars)
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
from app.extend.calculators.average import sma_kernel
from app.extend.calculators.rsi import rsi_kernel

logger = get_logger(__name__)


def _safe_sma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = sma_kernel(x[start:], period)
    return out


_EPSILON: float = 1e-12
_SCALE_100: float = 100.0


class StochasticRSI(BaseIndicator):
    """Stochastic RSI (StochRSI) indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.stochastic_rsi",
        version="1.0.0",
        name="Stochastic RSI",
        description="Applies Stochastic formula to RSI for range sensitivity",
        category="momentum",
        tags=("momentum", "oscillator", "stochrsi", "rsi", "stochastic"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("k", PortType.SERIES, "StochRSI %K"),
            OutputPort("d", PortType.SERIES, "StochRSI %D"),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "rsi_period": {"type": "int", "min": 2, "max": 50, "default": 14},
            "stoch_period": {"type": "int", "min": 2, "max": 50, "default": 14},
            "k_period": {"type": "int", "min": 1, "max": 20, "default": 3},
            "d_period": {"type": "int", "min": 1, "max": 20, "default": 3},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    rsi_period: int = Field(default=14, ge=1)
    stoch_period: int = Field(default=14, ge=1)
    k_period: int = Field(default=3, ge=1)
    d_period: int = Field(default=3, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.rsi_period + self.stoch_period + self.k_period + self.d_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute StochRSI %K and %D lines."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        rsi = rsi_kernel(close, self.rsi_period)
        raw_k = np.full(n, np.nan, dtype=np.float64)
        p = self.stoch_period
        for i in range(p - 1, n):
            window = rsi[i - p + 1 : i + 1]
            if not np.any(np.isnan(window)):
                min_v = np.min(window)
                max_v = np.max(window)
                diff = max_v - min_v
                raw_k[i] = (
                    _SCALE_100 * (rsi[i] - min_v) / diff if diff > _EPSILON else 50.0
                )
        k = _safe_sma(raw_k, self.k_period)
        d = _safe_sma(k, self.d_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated StochRSI(%d, %d) for %d bars",
            self.rsi_period,
            self.stoch_period,
            len(bars),
        )
        return {
            "k": IndicatorSeries(k, name="StochRSI.K"),
            "d": IndicatorSeries(d, name="StochRSI.D"),
        }


__all__ = ["StochasticRSI"]
