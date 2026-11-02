"""Chande Kroll Stop volatility strategy block.

Description:
    Calculates Tushar Chande and Stanley Kroll's trailing stop lines based on
    ATR offsets applied to directional extrema over primary and secondary lookbacks.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-chande-kroll-stop: Chande Kroll stop computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.chande_kroll_stop import (
        ChandeKrollStop,
    )
    res = ChandeKrollStop().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.volatility.atr import ATR
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


def _rolling_max(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    for i in range(p - 1, n):
        w = x[i - p + 1 : i + 1]
        if not np.all(np.isnan(w)):
            res[i] = np.nanmax(w)
    return res


def _rolling_min(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    for i in range(p - 1, n):
        w = x[i - p + 1 : i + 1]
        if not np.all(np.isnan(w)):
            res[i] = np.nanmin(w)
    return res


class ChandeKrollStop(BaseIndicator):
    """Chande Kroll Stop indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.chande_kroll_stop",
        version="1.0.0",
        name="Chande Kroll Stop",
        description="Volatility stop lines based on ATR and price extrema",
        category="volatility",
        tags=("volatility", "stop", "chande", "kroll", "atr"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("long_stop", PortType.SERIES, "Chande Kroll Long Stop"),
            OutputPort("short_stop", PortType.SERIES, "Chande Kroll Short Stop"),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "multiplier": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0},
            "secondary_period": {"type": "int", "min": 2, "max": 50, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=10, ge=1)
    multiplier: float = Field(default=2.0, gt=0.0)
    secondary_period: int = Field(default=9, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + self.secondary_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Long Stop and Short Stop lines."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        atr = ATR(period=self.period).calculate(bars)["value"].values
        hh = _rolling_max(high, self.period)
        ll = _rolling_min(low, self.period)
        raw_long = hh - self.multiplier * atr
        raw_short = ll + self.multiplier * atr
        long_stop = _rolling_max(raw_long, self.secondary_period)
        short_stop = _rolling_min(raw_short, self.secondary_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated ChandeKrollStop for %d bars",
            len(bars),
        )
        return {
            "long_stop": IndicatorSeries(long_stop, name="CK.LongStop"),
            "short_stop": IndicatorSeries(short_stop, name="CK.ShortStop"),
        }


__all__ = ["ChandeKrollStop"]
