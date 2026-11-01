"""BBRange numeric Bollinger variant with donor startup semantics."""

from __future__ import annotations

from typing import ClassVar, Literal, override

import numpy as np
from pydantic import Field

from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import (
    COMPUTED_PRICE_INPUTS,
    BarData,
    IndicatorSeries,
    computed_price,
)
from app.include.calculators.std_dev import std_dev_kernel


class BBRange(BaseIndicator):
    """Population-standard-deviation price range with partial-window startup."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.bb_range",
        name="BBRange",
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
        result = 2 * self.deviation * std_dev_kernel(values, self.period)
        return {"value": IndicatorSeries(result, name="BBRange")}
