"""TrueRange indicator.

- Calculates single-bar True Range considering prior bar close gap.
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
from app.extend.blocks.comparisons import (
    is_lower,
)
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.volatility.atr import ATR

logger = get_logger(__name__)


class TrueRange(BaseIndicator):
    """True Range indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.true_range",
        version="1.0.0",
        name="TrueRange",
        description="Calculates single-bar True Range considering prior bar close gap.",
        category="volatility",
        tags=("volatility", "true-range"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=1,
        dependencies=("indicator.volatility.atr",),
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
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: TrueRange requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        res = ATR.true_range(high_arr, low_arr, close_arr)
        logger.info(
            "FR-SERVICES-TRUERANGE-CALCULATE: Computed TrueRange for %d bars", n
        )
        return {"value": IndicatorSeries(res, name="TrueRange")}

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        lookback: int = 1,
        shift: int = 0,
        level: float | None = None,
    ) -> bool:
        """Evaluate True Range is lower than past value (or level)."""
        if level is not None:
            return is_lower(series, level, shift=shift)
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)


# Public exports.
__all__ = ["TrueRange"]
