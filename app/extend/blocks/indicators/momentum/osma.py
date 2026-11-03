"""OSMA indicator.

- Calculates Oscillator Moving Average (OSMA) histogram of MACD.
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
from app.extend.calculators.average import ema_kernel, sma_kernel

logger = get_logger(__name__)


class OSMA(BaseIndicator):
    """Moving Average of Oscillator (OSMA) indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.osma",
        version="1.0.0",
        name="OSMA",
        description="Calculates Oscillator Moving Average (OSMA) histogram of MACD.",
        category="momentum",
        tags=("momentum", "osma"),
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
        required_history_lookback=34,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "fast_ema": {"type": "int", "min": 1, "max": 48, "default": 12},
            "slow_ema": {"type": "int", "min": 1, "max": 104, "default": 26},
            "signal_period": {"type": "int", "min": 1, "max": 36, "default": 9},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    fast_ema: int = Field(
        default=12,
        ge=1,
        title="Fast ema",
        description="Number of bars in the fast exponential moving average",
    )

    slow_ema: int = Field(
        default=26,
        ge=1,
        title="Slow ema",
        description="Number of bars in the slow exponential moving average",
    )

    signal_period: int = Field(
        default=9,
        ge=1,
        title="Signal period",
        description="Number of bars in the signal smoothing window",
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
        return max(self.fast_ema, self.slow_ema) + self.signal_period - 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: OSMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        data = bars.close
        fast_ema = self.fast_ema
        slow_ema = self.slow_ema
        signal_period = self.signal_period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if fast_ema <= 0:
            fast_ema = 12
        if slow_ema <= 0:
            slow_ema = 26
        if signal_period <= 0:
            signal_period = 9
        fast_arr = ema_kernel(arr, fast_ema)
        slow_arr = ema_kernel(arr, slow_ema)
        macd = fast_arr - slow_arr
        res = np.full(n, np.nan, dtype=np.float64)
        valid_indices = np.where(~np.isnan(macd))[0]
        if len(valid_indices) >= signal_period:
            first_idx = valid_indices[0]
            valid_macd = macd[first_idx:]
            sig_part = sma_kernel(valid_macd, signal_period)
            res[first_idx:] = valid_macd - sig_part
        logger.info(
            "FR-SERVICES-OSMA-CALCULATE: Computed OSMA(%d, %d, %d) for %d bars",
            fast_ema,
            slow_ema,
            signal_period,
            n,
        )
        return {
            "value": IndicatorSeries(
                res, name=f"OSMA({fast_ema},{slow_ema},{signal_period})"
            )
        }


# Public exports.
__all__ = ["OSMA"]
