"""Volume-Weighted Moving Average (VWMA) strategy block.

Description:
    Calculates Volume-Weighted Moving Average (VWMA) weighting closing prices
    by their respective volume over a rolling window.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-vwma: VWMA computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.vwma import VWMA
    res = VWMA().calculate(bars)
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)

_EPSILON: float = 1e-12


class VWMA(BaseIndicator):
    """Volume-Weighted Moving Average (VWMA) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.vwma",
        version="1.0.0",
        name="Volume Weighted Moving Average",
        description="Moving average weighted by bar trading volume",
        category="volume",
        tags=("volume", "ma", "vwma"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "VWMA"),),
        required_market_inputs=("close", "volume"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute VWMA values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        pv_sma = sma_kernel(close * volume, self.period)
        vol_sma = sma_kernel(volume, self.period)
        vwma = np.full_like(close, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(pv_sma) & ~np.isnan(vol_sma) & (vol_sma > _EPSILON)
            vwma[valid] = pv_sma[valid] / vol_sma[valid]
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated VWMA(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(vwma, name="VWMA")}


__all__ = ["VWMA"]
