"""EaseOfMovement indicator.

- Calculates Richard Arms' Ease of Movement (EOM/EMV) relating price change to
  volume to assess how easily prices move.
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

_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class EaseOfMovement(BaseIndicator):
    """Ease of Movement (EOM) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.ease_of_movement",
        version="1.0.0",
        name="Ease of Movement",
        description="Richard Arms Ease of Movement relating price change to volume",
        category="volume",
        tags=("volume", "eom", "emv", "arms"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Ease of Movement"),),
        required_market_inputs=("high", "low", "volume"),
        required_history_lookback=15,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 14},
            "divisor": {
                "type": "float",
                "min": 1000.0,
                "max": 100000000.0,
                "default": 10000.0,
            },
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

    divisor: float = Field(
        default=10000.0,
        gt=0.0,
        title="Divisor",
        description="Scaling divisor applied to the ease-of-movement value",
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
        """Compute Ease of Movement values."""
        logger.debug(
            "FR-indicator-calculation: EaseOfMovement requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        n = len(high)
        emv_raw = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            hl2 = (high + low) / 2.0
            move = hl2[1:] - hl2[:-1]
            box_ratio = np.zeros(n - 1, dtype=np.float64)
            hl_diff = high[1:] - low[1:]
            with np.errstate(divide="ignore", invalid="ignore"):
                vol_div = volume[1:] / self.divisor
                valid = hl_diff > _EPSILON
                box_ratio[valid] = vol_div[valid] / hl_diff[valid]
                valid_emv = box_ratio > _EPSILON
                emv_raw[1:][valid_emv] = move[valid_emv] / box_ratio[valid_emv]
        eom = sma_kernel(emv_raw, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated EOM(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(eom, name="EOM")}


# Public exports.
__all__ = ["EaseOfMovement"]
