"""BBWidthRatio volatility indicator strategy block.

Description:
    Calculates Bollinger BandWidth ratio normalizing bandwidth by middle SMA.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-volatility: Bollinger BandWidth ratio calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
    res = BBWidthRatio().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import (
    COMPUTED_PRICE_INPUTS,
    BarData,
    IndicatorSeries,
    computed_price,
)
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.average import AverageCalculator, AverageType
from app.extend.calculators.std_dev import centered_deviation

logger = get_logger(__name__)


class BBWidthRatio(BaseIndicator):
    """Deviation from the current SMA, divided by period and positive SMA."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.bb_width_ratio",
        name="BBWidthRatio",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=tuple(
            InputPort(key, PortType.SERIES, required=False)
            for key in ("open", "high", "low", "close")
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=(),
        is_causal=True,
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 10000, "default": 20},
            "deviation": {
                "type": "float",
                "min": 0.1,
                "max": 7.0,
                "step": 0.1,
                "default": 2.0,
            },
            "computed_from": {
                "type": "int",
                "values": [0, 1, 2, 3, 4, 5, 6],
                "default": 0,
            },
        },
        required_history_lookback=1,
    )
    period: int = Field(default=20, ge=2, le=10000)
    deviation: float = Field(default=2.0, ge=0.01, le=10)
    computed_from: Literal[0, 1, 2, 3, 4, 5, 6] = 0

    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Expose the selected price feed to builders and execution planners."""
        return COMPUTED_PRICE_INPUTS[self.computed_from]

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Select the explicit input series and calculate all available bars."""
        values = computed_price(bars, self.computed_from)
        if not np.isfinite(values).all():
            raise ValueError("Bollinger input must be finite")
        calculator = AverageCalculator(AverageType.SMA, self.period)
        centers = np.zeros(len(values))
        for i, value in enumerate(values):
            calculator.on_bar_update(float(value), i)
            centers[i] = calculator.get_value()
        deviation = centered_deviation(values, centers, self.period, fixed_divisor=True)
        result = np.zeros(len(values))
        np.divide(
            2 * self.deviation * deviation, centers, out=result, where=centers > 0
        )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated BBWidthRatio for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(result, name="BBWidthRatio")}
