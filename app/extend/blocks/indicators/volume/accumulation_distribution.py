"""AccumulationDistribution indicator.

- Calculates Marc Chaikin's Accumulation/Distribution Line measuring the cumulative
  flow of money into and out of an asset based on close location.
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


class AccumulationDistribution(BaseIndicator):
    """Accumulation/Distribution Line (ADL) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.accumulation_distribution",
        version="1.0.0",
        name="Accumulation/Distribution",
        description="Cumulative money flow volume indicator (Marc Chaikin)",
        category="volume",
        tags=("volume", "adl", "chaikin", "accumulation"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Accumulation/Distribution"),),
        required_market_inputs=("high", "low", "close", "volume"),
        required_history_lookback=1,
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
        return 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Accumulation/Distribution Line values."""
        logger.debug(
            "FR-indicator-calculation: AccumulationDistribution requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        adl = adl_kernel(high, low, close, volume)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated ADL for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(adl, name="ADL")}


# Private helpers: used only by this indicator.
def adl_kernel(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    """Compute Accumulation/Distribution Line."""
    n = len(close)
    hl = high - low
    with np.errstate(divide="ignore", invalid="ignore"):
        valid = hl > _EPSILON
        clv = np.zeros(n, dtype=np.float64)
        clv[valid] = ((close[valid] - low[valid]) - (high[valid] - close[valid])) / hl[
            valid
        ]
    mf_vol = clv * volume
    return np.cumsum(mf_vol)


# Public exports.
__all__ = ["AccumulationDistribution"]
