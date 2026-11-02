"""Elder's Force Index volume strategy block.

Description:
    Calculates Alexander Elder's Force Index combining price movement
    and volume to quantify bull and bear power behind price moves.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-force-index: Force Index computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.force_index import ForceIndex
    res = ForceIndex().calculate(bars)
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
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


class ForceIndex(BaseIndicator):
    """Elder's Force Index block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.force_index",
        version="1.0.0",
        name="Force Index",
        description="Alexander Elder Force Index combining price delta and volume",
        category="volume",
        tags=("volume", "force_index", "elder"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Force Index"),),
        required_market_inputs=("close", "volume"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 50, "default": 13},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=13, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Force Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        n = len(close)
        raw_fi = np.zeros(n, dtype=np.float64)
        if n > 1:
            raw_fi[1:] = (close[1:] - close[:-1]) * volume[1:]
        fi = ema_kernel(raw_fi, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated ForceIndex(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(fi, name="ForceIndex")}


__all__ = ["ForceIndex"]
