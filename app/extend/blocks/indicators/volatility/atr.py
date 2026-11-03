"""ATR indicator.

- Calculates Average True Range (ATR) measuring market volatility.
"""

from __future__ import annotations

from collections.abc import Sequence
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


class ATR(BaseIndicator):
    """Average True Range indicator family consolidating math and conditions."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.atr",
        version="1.0.0",
        name="ATR",
        description="Calculates Average True Range (ATR) measuring market volatility.",
        category="volatility",
        tags=("volatility", "atr"),
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
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
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
        logger.debug("FR-indicator-calculation: ATR requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        if period <= 0:
            logger.warning(
                "FR-SERVICES-ATR-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        tr = self.true_range(high, low, close)
        n = len(tr)
        if n == 0:
            return {"value": IndicatorSeries(np.empty(0, dtype=np.float64), name="ATR")}
        atr_vals = np.empty(n, dtype=np.float64)
        atr_vals[0] = tr[0]
        for i in range(1, n):
            current_bar = i
            window = min(current_bar + 1, period)
            atr_vals[i] = ((window - 1) * atr_vals[i - 1] + tr[i]) / window
        logger.info(
            "FR-SERVICES-ATR-CALCULATE: Computed ATR(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(atr_vals, name="ATR")}

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def true_range(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
    ) -> np.ndarray:
        """Calculate True Range array across all bars.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.

        Returns:
            1D float64 NumPy array of True Range values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(high_arr)
        if n == 0:
            return np.empty(0, dtype=np.float64)
        tr = np.empty(n, dtype=np.float64)
        tr[0] = high_arr[0] - low_arr[0]
        if n > 1:
            prev_c = close_arr[:-1]
            h_curr = high_arr[1:]
            l_curr = low_arr[1:]
            hl = h_curr - l_curr
            hc = np.abs(h_curr - prev_c)
            lc = np.abs(l_curr - prev_c)
            tr[1:] = np.maximum(hl, np.maximum(hc, lc))
        return tr


# Public exports.
__all__ = ["ATR"]
