"""ForceIndex indicator.

- Calculates Alexander Elder's Force Index combining price movement and volume to
  quantify bull and bear power behind price moves.
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

    # Metadata: catalog identity, ports, and execution capabilities.
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
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 50, "default": 13}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=13,
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
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Force Index values."""
        logger.debug(
            "FR-indicator-calculation: ForceIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
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


# Public exports.
__all__ = ["ForceIndex"]
