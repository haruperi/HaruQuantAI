"""Net Volume strategy block.

Description:
    Calculates Net Volume per bar as signed volume: positive on up bars,
    negative on down bars, and zero on unchanged bars.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-net-volume: Net volume computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.net_volume import NetVolume
    res = NetVolume().calculate(bars)
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


class NetVolume(BaseIndicator):
    """Net Volume block."""

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
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Net Volume values."""
        bars.require_inputs(self.spec.required_market_inputs)
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


__all__ = ["NetVolume"]
