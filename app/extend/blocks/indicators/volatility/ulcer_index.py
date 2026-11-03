"""UlcerIndex indicator.

- Calculates Ulcer Index downside risk volatility metric.
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

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

DOWN_MODE = 2
logger = get_logger(__name__)


class UlcerIndex(BaseIndicator):
    """Ulcer Index indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.ulcer_index",
        version="1.0.0",
        name="UlcerIndex",
        description="Calculates Ulcer Index downside risk volatility metric.",
        category="volatility",
        tags=("volatility", "ulcer-index"),
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
        required_history_lookback=24,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "mode": {"type": "int", "choices": [1, 2], "default": 1},
            "period": {"type": "int", "min": 1, "max": 96, "default": 24},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    mode: Literal[1, 2] = Field(
        default=1, title="Mode", description="Mode used by the indicator calculation"
    )

    period: int = Field(
        default=24,
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: UlcerIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        data = bars.close
        mode = self.mode
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-ULCER-CALCULATE: Invalid period %d, defaulting to 24",
                period,
            )
            period = 24
        dd_buffer = np.zeros(n, dtype=np.float64)
        res = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            if mode == DOWN_MODE:
                lc = float(np.min(win))
                if lc != 0.0 and (not np.isnan(lc)):
                    dd_buffer[i] = 100.0 * (arr[i] - lc) / lc
            else:
                hc = float(np.max(win))
                if hc != 0.0 and (not np.isnan(hc)):
                    dd_buffer[i] = 100.0 * (arr[i] - hc) / hc
            if i >= period:
                dd_win = dd_buffer[i - period + 1 : i + 1]
                sum_sq = float(np.sum(np.square(dd_win)))
                res[i] = float(np.sqrt(sum_sq / period))
        logger.info(
            "FR-SERVICES-ULCER-CALCULATE: UI(mode=%d, period=%d) computed for %d bars",
            mode,
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"UlcerIndex(mode={mode},{period})")}


# Public exports.
__all__ = ["UlcerIndex"]
