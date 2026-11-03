"""VWMA indicator.

- Calculates Volume-Weighted Moving Average (VWMA) weighting closing prices by their
  respective volume over a rolling window.
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

    # Metadata: catalog identity, ports, and execution capabilities.
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
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=20,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute VWMA values."""
        logger.debug("FR-indicator-calculation: VWMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
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


# Public exports.
__all__ = ["VWMA"]
