"""SmallestRange volatility indicator strategy block.

Description:
    Identifies smallest bar range in rolling lookback window.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-volatility: Rolling minimum bar range calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.smallest_range import SmallestRange
    res = SmallestRange().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
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
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.extrema import rolling_extreme

logger = get_logger(__name__)


class SmallestRange(BaseIndicator):
    """Numeric extreme of eight-decimal candle ranges over available history."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.smallest_range",
        name="SmallestRange",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=tuple(
            InputPort(key, PortType.SERIES, required=True) for key in ("high", "low")
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        is_causal=True,
        is_generation_eligible=True,
        parameter_search_space={
            "period": {
                "type": "int",
                "values": [3, 5, 10, 14, 20, 25, 30, 40, 50],
                "default": 14,
            }
        },
        required_history_lookback=1,
    )
    period: int = Field(default=14, ge=1)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Return values, not a predicate about the current candle."""
        bars.require_inputs(self.spec.required_market_inputs)
        ranges = bars.high - bars.low
        if not np.isfinite(ranges).all():
            raise ValueError("Candle ranges must be finite")
        rounded = np.floor(ranges * 100_000_000.0 + 0.5) / 100_000_000.0
        values = rolling_extreme(rounded, self.period, highest=False)
        values = np.minimum(values, 100_000_000.0)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated SmallestRange for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="SmallestRange")}
