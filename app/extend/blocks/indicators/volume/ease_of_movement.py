"""Ease of Movement (EOM) volume indicator strategy block.

Description:
    Calculates Richard Arms' Ease of Movement (EOM/EMV) relating price change
    to volume to assess how easily prices move.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-ease-of-movement: EOM computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.ease_of_movement import (
        EaseOfMovement,
    )
    res = EaseOfMovement().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class EaseOfMovement(BaseIndicator):
    """Ease of Movement (EOM) block."""

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
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 14},
            "divisor": {
                "type": "float",
                "min": 1000.0,
                "max": 100000000.0,
                "default": 10000.0,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=14, ge=1)
    divisor: float = Field(default=10000.0, gt=0.0)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Ease of Movement values."""
        bars.require_inputs(self.spec.required_market_inputs)
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


__all__ = ["EaseOfMovement"]
