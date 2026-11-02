"""Advance/Decline market breadth volume indicator block.

Description:
    Calculates cumulative volume breadth by accumulating volume on advancing
    bars and subtracting volume on declining bars.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-advance-decline: Advance/Decline breadth computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.advance_decline import (
        AdvanceDecline,
    )
    res = AdvanceDecline().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
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


class AdvanceDecline(BaseIndicator):
    """Advance/Decline volume breadth block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.advance_decline",
        version="1.0.0",
        name="Advance/Decline",
        description="Cumulative volume market breadth line",
        category="volume",
        tags=("volume", "breadth", "advance_decline"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Advance/Decline Line"),),
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
        """Compute Advance/Decline cumulative line."""
        bars.require_inputs(self.spec.required_market_inputs)
        open_arr = np.asarray(bars.open, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        direction = np.sign(close_arr - open_arr)
        ad_line = np.cumsum(direction * volume)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated AdvanceDecline for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(ad_line, name="AdvDec")}


__all__ = ["AdvanceDecline"]
