"""NetVolume indicator.

- Calculates Net Volume per bar as signed volume: positive on up bars, negative on
  down bars, and zero on unchanged bars.
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


class NetVolume(BaseIndicator):
    """Net Volume block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.net_volume",
        version="1.0.0",
        name="Net Volume",
        description="Signed bar volume (positive on up bars, negative on down bars)",
        category="volume",
        tags=("volume", "net_volume"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Net Volume"),),
        required_market_inputs=("open", "close", "volume"),
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
        """Compute Net Volume values."""
        logger.debug("FR-indicator-calculation: NetVolume requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        open_arr = np.asarray(bars.open, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        net_vol = np.where(
            close_arr > open_arr,
            volume,
            np.where(close_arr < open_arr, -volume, 0.0),
        )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated NetVolume for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(net_vol, name="NetVolume")}


# Public exports.
__all__ = ["NetVolume"]
