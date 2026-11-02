"""Mass Index volatility strategy block.

Description:
    Calculates Donald Dorsey's Mass Index examining the narrowing and widening
    of the trading range between high and low prices to identify reversals.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-mass-index: Mass index computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.mass_index import MassIndex
    res = MassIndex().calculate(bars)
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


def _rolling_sum_valid(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    for i in range(p - 1, n):
        window = x[i - p + 1 : i + 1]
        if not np.any(np.isnan(window)):
            res[i] = np.sum(window)
    return res


class MassIndex(BaseIndicator):
    """Mass Index volatility reversal block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.mass_index",
        version="1.0.0",
        name="Mass Index",
        description="Examines range expansion to detect trend reversal bulges (Dorsey)",
        category="volatility",
        tags=("volatility", "mass_index", "dorsey", "reversal"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Mass Index"),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "ema_period": {"type": "int", "min": 2, "max": 30, "default": 9},
            "sum_period": {"type": "int", "min": 10, "max": 50, "default": 25},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    ema_period: int = Field(default=9, ge=1)
    sum_period: int = Field(default=25, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return (self.ema_period * 2) + self.sum_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Mass Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        hl = high - low
        ema1 = ema_kernel(hl, self.ema_period)
        ema2 = _safe_ema(ema1, self.ema_period)
        ratio = np.full_like(hl, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(ema1) & ~np.isnan(ema2) & (ema2 > _EPSILON)
            ratio[valid] = ema1[valid] / ema2[valid]
        mi = _rolling_sum_valid(ratio, self.sum_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated MassIndex for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(mi, name="MassIndex")}


__all__ = ["MassIndex"]
