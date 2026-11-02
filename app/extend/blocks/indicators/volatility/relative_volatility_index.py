"""Relative Volatility Index (RVI) strategy block.

Description:
    Calculates Donald Dorsey's Relative Volatility Index applying standard
    RSI mechanics to standard deviation rather than daily price change.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-relative-volatility-index: RVI volatility index computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.relative_volatility_index import (
        RelativeVolatilityIndex,
    )
    res = RelativeVolatilityIndex().calculate(bars)
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
from app.extend.calculators.average import ema_kernel
from app.extend.calculators.std_dev import std_dev_kernel

logger = get_logger(__name__)

_SCALE_100: float = 100.0
_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class RelativeVolatilityIndex(BaseIndicator):
    """Relative Volatility Index (RVI) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.relative_volatility_index",
        version="1.0.0",
        name="Relative Volatility Index",
        description="RSI formula applied to Standard Deviation (Donald Dorsey)",
        category="volatility",
        tags=("volatility", "rvi", "dorsey", "std_dev"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Relative Volatility Index"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "std_period": {"type": "int", "min": 2, "max": 50, "default": 10},
            "smooth_period": {"type": "int", "min": 2, "max": 50, "default": 14},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    std_period: int = Field(default=10, ge=1)
    smooth_period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.std_period + self.smooth_period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Relative Volatility Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        sd = std_dev_kernel(close, self.std_period)
        up_sd = np.zeros(n, dtype=np.float64)
        dn_sd = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            diff = close[1:] - close[:-1]
            valid_sd = sd[1:]
            up_sd[1:] = np.where(diff > 0.0, valid_sd, 0.0)
            dn_sd[1:] = np.where(diff < 0.0, valid_sd, 0.0)
        u_smooth = ema_kernel(up_sd, self.smooth_period)
        d_smooth = ema_kernel(dn_sd, self.smooth_period)
        rvi = np.full(n, np.nan, dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            total = u_smooth + d_smooth
            valid = ~np.isnan(u_smooth) & ~np.isnan(d_smooth) & (total > _EPSILON)
            rvi[valid] = _SCALE_100 * u_smooth[valid] / total[valid]
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated RVI(%d, %d) for %d bars",
            self.std_period,
            self.smooth_period,
            len(bars),
        )
        return {"value": IndicatorSeries(rvi, name="RVI_Vol")}


__all__ = ["RelativeVolatilityIndex"]
