"""DetrendedPriceOscillator indicator.

- Calculates Detrended Price Oscillator (DPO) removing trend to highlight short-term
  price cycles by comparing price to a shifted moving average.
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class DetrendedPriceOscillator(BaseIndicator):
    """Detrended Price Oscillator (DPO) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.detrended_price_oscillator",
        version="1.0.0",
        name="Detrended Price Oscillator",
        description="Isolates short-term cycles by eliminating longer-term trend",
        category="momentum",
        tags=("momentum", "oscillator", "dpo", "cycles"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Detrended Price Oscillator"),),
        required_market_inputs=("close",),
        required_history_lookback=32,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 21}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=21,
        ge=2,
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
        """Return minimum history bars needed for valid calculation."""
        return self.period + (self.period // 2 + 1)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Detrended Price Oscillator values over historical bars."""
        logger.debug(
            "FR-indicator-calculation: DetrendedPriceOscillator requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        shift = self.period // 2 + 1
        sma = sma_kernel(close, self.period)
        dpo = np.full(n, np.nan, dtype=np.float64)
        if n >= self.period + shift:
            for i in range(self.period - 1 + shift, n):
                if not np.isnan(sma[i]):
                    dpo[i] = close[i - shift] - sma[i]
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated DPO(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(dpo, name="DPO")}


# Public exports.
__all__ = ["DetrendedPriceOscillator"]
