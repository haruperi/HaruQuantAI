"""ROC indicator.

- Calculates Rate of Change (ROC) percentage difference across lookback window.
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

logger = get_logger(__name__)


class ROC(BaseIndicator):
    """Rate of Change (ROC) indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.roc",
        version="1.0.0",
        name="ROC",
        description=(
            "Calculates Rate of Change (ROC) percentage difference across "
            "lookback window."
        ),
        category="momentum",
        tags=("momentum", "roc"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
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
        required_market_inputs=("close",),
        required_history_lookback=6,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 20, "default": 5}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=5,
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
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: ROC requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        data = bars.close
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-ROC-CALCULATE: Invalid period %d, defaulting to 5", period
            )
            period = 5
        res = np.zeros(n, dtype=np.float64)
        for i in range(period, n):
            past = arr[i - period]
            if past != 0.0 and (not np.isnan(past)):
                res[i] = (arr[i] - past) / past * 100.0
            else:
                res[i] = 0.0
        logger.info(
            "FR-SERVICES-ROC-CALCULATE: Computed ROC(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(res, name=f"ROC({period})")}


# Public exports.
__all__ = ["ROC"]
