"""Price Volume Trend (PVT) strategy block.

Description:
    Calculates Price Volume Trend (PVT) representing cumulative volume
    adjusted by percentage changes in closing price.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-price-volume-trend: PVT cumulative computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.price_volume_trend import (
        PriceVolumeTrend,
    )
    res = PriceVolumeTrend().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

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

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class PriceVolumeTrend(BaseIndicator):
    """Price Volume Trend (PVT) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.price_volume_trend",
        version="1.0.0",
        name="Price Volume Trend",
        description="Cumulative volume weighted by percentage price change",
        category="volume",
        tags=("volume", "pvt", "price_volume_trend"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Price Volume Trend"),),
        required_market_inputs=("close", "volume"),
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return _MIN_BARS

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Price Volume Trend values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        n = len(close)
        pvt = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            prev = close[:-1]
            diff = close[1:] - prev
            with np.errstate(divide="ignore", invalid="ignore"):
                valid = prev > _EPSILON
                pct = np.zeros(n - 1, dtype=np.float64)
                pct[valid] = diff[valid] / prev[valid]
            pvt[1:] = np.cumsum(pct * volume[1:])
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated PVT for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(pvt, name="PVT")}


__all__ = ["PriceVolumeTrend"]
