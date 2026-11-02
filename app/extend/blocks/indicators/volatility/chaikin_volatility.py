"""Chaikin Volatility strategy block.

Description:
    Calculates Marc Chaikin's Volatility indicator measuring the percentage
    rate of change of the exponential moving average of the high-low spread.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-chaikin-volatility: Chaikin volatility computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.chaikin_volatility import (
        ChaikinVolatility,
    )
    res = ChaikinVolatility().calculate(bars)
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

_SCALE_100: float = 100.0
_EPSILON: float = 1e-12


class ChaikinVolatility(BaseIndicator):
    """Chaikin Volatility indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.chaikin_volatility",
        version="1.0.0",
        name="Chaikin Volatility",
        description="Percentage rate of change of EMA of High-Low range",
        category="volatility",
        tags=("volatility", "chaikin", "range"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Chaikin Volatility"),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "ema_period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "roc_period": {"type": "int", "min": 2, "max": 50, "default": 10},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    ema_period: int = Field(default=10, ge=1)
    roc_period: int = Field(default=10, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.ema_period + self.roc_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Chaikin Volatility values."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        n = len(high)
        hl_ema = ema_kernel(high - low, self.ema_period)
        cv = np.full(n, np.nan, dtype=np.float64)
        p = self.roc_period
        if n > p:
            with np.errstate(divide="ignore", invalid="ignore"):
                for i in range(p, n):
                    prev = hl_ema[i - p]
                    curr = hl_ema[i]
                    if not np.isnan(prev) and not np.isnan(curr) and prev > _EPSILON:
                        cv[i] = _SCALE_100 * (curr - prev) / prev
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated ChaikinVol(%d, %d) for %d",
            self.ema_period,
            self.roc_period,
            len(bars),
        )
        return {"value": IndicatorSeries(cv, name="ChaikinVol")}


__all__ = ["ChaikinVolatility"]
