"""ChopZone indicator.

- Calculates TradingView Chop Zone indicator quantifying the angle and slope of a
  30-period EMA to classify market state into discrete phases.
"""

from __future__ import annotations

import math
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

_RAD_TO_DEG: float = 180.0 / math.pi
_SCALE_100: float = 100.0
_THRESH_STRONG: float = 20.0
_THRESH_MODERATE: float = 10.0
_THRESH_WEAK: float = 3.0


class ChopZone(BaseIndicator):
    """Chop Zone regime indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.chop_zone",
        version="1.0.0",
        name="Chop Zone",
        description="Quantifies EMA angle into discrete trend and chop phases",
        category="regime",
        tags=("regime", "chop_zone", "ema", "trend"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, "Chop Zone Phase (-3 to +3)"),
            OutputPort("angle", PortType.SERIES, "EMA Angle in Degrees"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=31,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 5, "max": 100, "default": 30}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=30,
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
        """Compute Chop Zone phase (-3 to +3) and angle."""
        logger.debug("FR-indicator-calculation: ChopZone requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        ema = ema_kernel(close, self.period)
        angle = _ema_angle(ema)
        phase = np.zeros_like(angle)
        for i in range(len(angle)):
            a = angle[i]
            if np.isnan(a):
                phase[i] = np.nan
            elif a > _THRESH_STRONG:
                phase[i] = 3.0
            elif a > _THRESH_MODERATE:
                phase[i] = 2.0
            elif a > _THRESH_WEAK:
                phase[i] = 1.0
            elif a < -_THRESH_STRONG:
                phase[i] = -3.0
            elif a < -_THRESH_MODERATE:
                phase[i] = -2.0
            elif a < -_THRESH_WEAK:
                phase[i] = -1.0
            else:
                phase[i] = 0.0
        logger.debug(
            "FR-SERVICES-INDICATOR-REGIME: Calculated ChopZone(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "value": IndicatorSeries(phase, name="ChopZone.Phase"),
            "angle": IndicatorSeries(angle, name="ChopZone.Angle"),
        }


# Private helpers: used only by this indicator.
def _ema_angle(ema: np.ndarray) -> np.ndarray:
    n = len(ema)
    angle = np.full(n, np.nan, dtype=np.float64)
    for i in range(1, n):
        if not np.isnan(ema[i]) and not np.isnan(ema[i - 1]) and ema[i - 1] != 0.0:
            pct_change = (ema[i] - ema[i - 1]) / ema[i - 1] * _SCALE_100
            angle[i] = math.atan(pct_change) * _RAD_TO_DEG
    return angle


# Public exports.
__all__ = ["ChopZone"]
