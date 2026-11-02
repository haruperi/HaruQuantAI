"""Ultimate Oscillator momentum strategy block.

Description:
    Calculates Larry Williams' Ultimate Oscillator combining buying pressure
    across three distinct timeframes (7, 14, 28) with weighted coefficients.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-ultimate-oscillator: Ultimate oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.ultimate_oscillator import (
        UltimateOscillator,
    )
    res = UltimateOscillator().calculate(bars)
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

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_SCALE_100: float = 100.0
_MIN_BARS: int = 2


def _rolling_sum(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    if n >= p:
        cs = np.insert(np.cumsum(x), 0, 0.0)
        res[p - 1 :] = cs[p:] - cs[:-p]
    return res


class UltimateOscillator(BaseIndicator):
    """Ultimate Oscillator (UO) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.ultimate_oscillator",
        version="1.0.0",
        name="Ultimate Oscillator",
        description="Multi-timeframe buying pressure oscillator (Larry Williams)",
        category="momentum",
        tags=("momentum", "oscillator", "ultimate", "williams"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Ultimate Oscillator"),),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period1": {"type": "int", "min": 2, "max": 20, "default": 7},
            "period2": {"type": "int", "min": 5, "max": 40, "default": 14},
            "period3": {"type": "int", "min": 10, "max": 80, "default": 28},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period1: int = Field(default=7, ge=1)
    period2: int = Field(default=14, ge=1)
    period3: int = Field(default=28, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.period1, self.period2, self.period3) + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Ultimate Oscillator values."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        uo = np.full(n, np.nan, dtype=np.float64)
        if n >= _MIN_BARS:
            prev_close = np.roll(close, 1)
            prev_close[0] = close[0]
            true_low = np.minimum(low, prev_close)
            true_high = np.maximum(high, prev_close)
            bp = close - true_low
            tr = true_high - true_low
            sum_bp1 = _rolling_sum(bp, self.period1)
            sum_tr1 = _rolling_sum(tr, self.period1)
            sum_bp2 = _rolling_sum(bp, self.period2)
            sum_tr2 = _rolling_sum(tr, self.period2)
            sum_bp3 = _rolling_sum(bp, self.period3)
            sum_tr3 = _rolling_sum(tr, self.period3)
            with np.errstate(divide="ignore", invalid="ignore"):
                avg1 = np.where(sum_tr1 > _EPSILON, sum_bp1 / sum_tr1, 0.0)
                avg2 = np.where(sum_tr2 > _EPSILON, sum_bp2 / sum_tr2, 0.0)
                avg3 = np.where(sum_tr3 > _EPSILON, sum_bp3 / sum_tr3, 0.0)
                val = _SCALE_100 * (4.0 * avg1 + 2.0 * avg2 + avg3) / 7.0
            max_p = max(self.period1, self.period2, self.period3)
            uo[max_p - 1 :] = val[max_p - 1 :]
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated UO for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(uo, name="UO")}


__all__ = ["UltimateOscillator"]
