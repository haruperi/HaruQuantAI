"""Volatility Zero Trend Close-to-Close strategy block.

Description:
    Calculates zero-mean sample volatility assuming zero drift in asset returns,
    annualized by trading days per year.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-volatility-zero-trend: Zero trend volatility computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.volatility_zero_trend import (
        VolatilityZeroTrend,
    )
    res = VolatilityZeroTrend().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

import math
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

_SCALE_100: float = 100.0
_MIN_BARS: int = 2


class VolatilityZeroTrend(BaseIndicator):
    """Volatility Zero Trend Close-to-Close block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.volatility_zero_trend",
        version="1.0.0",
        name="Volatility Zero Trend Close-to-Close",
        description="Zero-drift annualized historical sample volatility estimator",
        category="volatility",
        tags=("volatility", "zero_trend", "historical_volatility"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Zero Trend Volatility (%)"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
            "annual_days": {"type": "int", "min": 1, "max": 365, "default": 252},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=2)
    annual_days: int = Field(default=252, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute zero-trend sample volatility values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        out = np.full(n, np.nan, dtype=np.float64)
        p = self.period
        if n >= p + 1:
            log_ret = np.diff(np.log(np.maximum(close, 1e-12)))
            scale = math.sqrt(float(self.annual_days)) * _SCALE_100
            for i in range(p - 1, len(log_ret)):
                window = log_ret[i - p + 1 : i + 1]
                mean_sq = float(np.mean(window**2))
                out[i + 1] = math.sqrt(mean_sq) * scale
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated VolZeroTrend(%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(out, name="VolZeroTrend")}


__all__ = ["VolatilityZeroTrend"]
