"""PriceVolumeTrend indicator.

- Calculates Price Volume Trend (PVT) representing cumulative volume adjusted by
  percentage changes in closing price.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

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
_MIN_BARS: int = 2


class PriceVolumeTrend(BaseIndicator):
    """Price Volume Trend (PVT) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
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
        required_history_lookback=2,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={},
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return _MIN_BARS

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Price Volume Trend values."""
        logger.debug(
            "FR-indicator-calculation: PriceVolumeTrend requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
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


# Public exports.
__all__ = ["PriceVolumeTrend"]
