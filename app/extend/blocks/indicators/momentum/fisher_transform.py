"""Fisher Transform momentum indicator strategy block.

Description:
    Calculates John Ehlers' Fisher Transform converting normalized prices into
    a Gaussian normal distribution to pinpoint turning points with zero lag.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-fisher-transform: Fisher transform computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.fisher_transform import (
        FisherTransform,
    )
    res = FisherTransform().calculate(bars)
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

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_CLAMP_LIMIT: float = 0.999


class FisherTransform(BaseIndicator):
    """John Ehlers Fisher Transform indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.fisher_transform",
        version="1.0.0",
        name="Fisher Transform",
        description="Converts price distribution to Gaussian normal",
        category="momentum",
        tags=("momentum", "oscillator", "fisher", "ehlers"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(
            OutputPort("fisher", PortType.SERIES, "Fisher Transform"),
            OutputPort("signal", PortType.SERIES, "Trigger Signal (1-bar lag)"),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 50, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=9, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Fisher Transform and trigger signal values."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        n = len(high)
        fisher = np.full(n, np.nan, dtype=np.float64)
        signal = np.full(n, np.nan, dtype=np.float64)
        if n >= self.period:
            hl2 = (high + low) / 2.0
            x_prev = 0.0
            fish_prev = 0.0
            p = self.period
            for i in range(p - 1, n):
                window = hl2[i - p + 1 : i + 1]
                min_l = np.min(window)
                max_h = np.max(window)
                denom = max_h - min_l
                raw_x = (
                    0.33 * 2.0 * ((hl2[i] - min_l) / denom - 0.5) + 0.67 * x_prev
                    if denom > _EPSILON
                    else 0.0
                )
                x_val = np.clip(raw_x, -_CLAMP_LIMIT, _CLAMP_LIMIT)
                x_prev = x_val
                fish_val = 0.5 * np.log((1.0 + x_val) / (1.0 - x_val)) + 0.5 * fish_prev
                fisher[i] = fish_val
                if i > p - 1:
                    signal[i] = fish_prev
                fish_prev = fish_val
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated Fisher(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "fisher": IndicatorSeries(fisher, name="Fisher"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


__all__ = ["FisherTransform"]
