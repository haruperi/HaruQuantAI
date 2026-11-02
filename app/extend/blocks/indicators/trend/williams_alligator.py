"""Williams Alligator strategy block.

Description:
    Calculates Bill Williams Alligator indicator consisting of three displaced
    smoothed moving averages: Jaw (Blue), Teeth (Red), and Lips (Green).
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-williams-alligator: Williams Alligator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.williams_alligator import (
        WilliamsAlligator,
    )
    res = WilliamsAlligator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
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
from app.extend.calculators.average import smma_kernel

logger = get_logger(__name__)


def _shift_array(arr: np.ndarray, shift: int) -> np.ndarray:
    n = len(arr)
    shifted = np.full(n, np.nan, dtype=np.float64)
    if shift < n:
        shifted[shift:] = arr[:-shift] if shift > 0 else arr
    return shifted


class WilliamsAlligator(BaseIndicator):
    """Williams Alligator indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.williams_alligator",
        version="1.0.0",
        name="Williams Alligator",
        description="Three displaced smoothed moving averages (Bill Williams)",
        category="trend",
        tags=("trend", "alligator", "williams", "smma"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(
            OutputPort("jaw", PortType.SERIES, "Alligator Jaw (SMMA 13, Shift 8)"),
            OutputPort("teeth", PortType.SERIES, "Alligator Teeth (SMMA 8, Shift 5)"),
            OutputPort("lips", PortType.SERIES, "Alligator Lips (SMMA 5, Shift 3)"),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "jaw_period": {"type": "int", "min": 5, "max": 50, "default": 13},
            "jaw_shift": {"type": "int", "min": 1, "max": 20, "default": 8},
            "teeth_period": {"type": "int", "min": 3, "max": 30, "default": 8},
            "teeth_shift": {"type": "int", "min": 1, "max": 15, "default": 5},
            "lips_period": {"type": "int", "min": 2, "max": 20, "default": 5},
            "lips_shift": {"type": "int", "min": 1, "max": 10, "default": 3},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    jaw_period: int = Field(default=13, ge=1)
    jaw_shift: int = Field(default=8, ge=0)
    teeth_period: int = Field(default=8, ge=1)
    teeth_shift: int = Field(default=5, ge=0)
    lips_period: int = Field(default=5, ge=1)
    lips_shift: int = Field(default=3, ge=0)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(
            self.jaw_period + self.jaw_shift,
            self.teeth_period + self.teeth_shift,
            self.lips_period + self.lips_shift,
        )

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Alligator Jaw, Teeth, and Lips lines."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        median = (high + low) / 2.0
        jaw_raw = smma_kernel(median, self.jaw_period)
        teeth_raw = smma_kernel(median, self.teeth_period)
        lips_raw = smma_kernel(median, self.lips_period)
        jaw = _shift_array(jaw_raw, self.jaw_shift)
        teeth = _shift_array(teeth_raw, self.teeth_shift)
        lips = _shift_array(lips_raw, self.lips_shift)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated Alligator for %d bars",
            len(bars),
        )
        return {
            "jaw": IndicatorSeries(jaw, name="Alligator.Jaw"),
            "teeth": IndicatorSeries(teeth, name="Alligator.Teeth"),
            "lips": IndicatorSeries(lips, name="Alligator.Lips"),
        }


__all__ = ["WilliamsAlligator"]
