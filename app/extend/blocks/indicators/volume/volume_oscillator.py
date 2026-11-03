"""VolumeOscillator indicator.

- Calculates Volume Oscillator as the percentage spread between a fast volume moving
  average and a slow volume moving average.
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

_SCALE_100: float = 100.0
_EPSILON: float = 1e-12


class VolumeOscillator(BaseIndicator):
    """Volume Oscillator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.volume_oscillator",
        version="1.0.0",
        name="Volume Oscillator",
        description="Percentage difference between fast and slow volume MAs",
        category="volume",
        tags=("volume", "oscillator", "volume_oscillator"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("volume", PortType.SERIES, "Volume series", required=True),),
        outputs=(OutputPort("value", PortType.SERIES, "Volume Oscillator"),),
        required_market_inputs=("volume",),
        required_history_lookback=10,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "fast_period": {"type": "int", "min": 2, "max": 50, "default": 5},
            "slow_period": {"type": "int", "min": 5, "max": 100, "default": 10},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    fast_period: int = Field(
        default=5,
        ge=1,
        title="Fast period",
        description="Number of bars in the fast window",
    )

    slow_period: int = Field(
        default=10,
        ge=1,
        title="Slow period",
        description="Number of bars in the slow window",
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
        return max(self.fast_period, self.slow_period)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Volume Oscillator values."""
        logger.debug(
            "FR-indicator-calculation: VolumeOscillator requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        volume = np.asarray(bars.volume, dtype=np.float64)
        fast_sma = sma_kernel(volume, self.fast_period)
        slow_sma = sma_kernel(volume, self.slow_period)
        vo = np.full_like(volume, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid = ~np.isnan(fast_sma) & ~np.isnan(slow_sma) & (slow_sma > _EPSILON)
            vo[valid] = (
                _SCALE_100 * (fast_sma[valid] - slow_sma[valid]) / slow_sma[valid]
            )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated VolumeOsc(%d, %d) for %d bars",
            self.fast_period,
            self.slow_period,
            len(bars),
        )
        return {"value": IndicatorSeries(vo, name="VolOsc")}


# Public exports.
__all__ = ["VolumeOscillator"]
