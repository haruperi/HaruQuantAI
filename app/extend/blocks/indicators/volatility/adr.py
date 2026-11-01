"""AverageDailyRange indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AVERAGEDAILYRANGE: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_ADR_PERIOD: int = 1
DEFAULT_ADR_PERIOD: int = 14
DEFAULT_STRETCH_THRESHOLD: float = 1.2
DEFAULT_COMPRESS_THRESHOLD: float = 0.8
EPSILON: float = 1e-12


class AverageDailyRange(BaseIndicator):
    """Average Daily Range (ADR) price travel and stretch ratio block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.adr",
        name="AverageDailyRange",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("adr", PortType.SERIES),
            OutputPort("stretch", PortType.SERIES),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=DEFAULT_ADR_PERIOD, ge=MIN_ADR_PERIOD)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_ADR_PERIOD:
            raise ValueError(f"period must be >= {MIN_ADR_PERIOD}, got {self.period}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        period = self.period
        logger.info("AverageDailyRange initiated: period=%d", period)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        adr_vals, stretch_vals = self._compute_adr(h_arr, l_arr, period, n)
        logger.info("AverageDailyRange completed: bars=%d", n)
        return {
            "adr": IndicatorSeries(adr_vals, name=f"ADR({period})"),
            "stretch": IndicatorSeries(stretch_vals, name=f"ADR_Stretch({period})"),
        }

    @classmethod
    def _compute_adr(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        n: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        rng = np.maximum(0.0, h_arr - l_arr)
        adr = np.zeros(n, dtype=np.float64)
        stretch = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            mean_rng = float(np.sum(rng[start : i + 1])) / window_len
            adr[i] = mean_rng
            stretch[i] = rng[i] / mean_rng if mean_rng > EPSILON else 1.0
        return (adr, stretch)

    @classmethod
    def is_stretched(
        cls,
        stretch: IndicatorSeries,
        threshold: float = DEFAULT_STRETCH_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if bar range stretch exceeds threshold (volatility expansion)."""
        logger.info(
            "Evaluating ADR is_stretched: threshold=%.2f, shift=%d", threshold, shift
        )
        return is_greater(stretch, threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_compressed(
        cls,
        stretch: IndicatorSeries,
        threshold: float = DEFAULT_COMPRESS_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if bar range stretch is below threshold (volatility compression)."""
        logger.info(
            "Evaluating ADR is_compressed: threshold=%.2f, shift=%d", threshold, shift
        )
        return is_lower(stretch, threshold, shift1=shift, round_digits=8)

    @classmethod
    def crosses_above(cls, adr: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if ADR crosses above level at shift."""
        logger.info("Evaluating ADR crosses_above: level=%.4f, shift=%d", level, shift)
        return crosses_above(adr, level, shift=shift)

    @classmethod
    def crosses_below(cls, adr: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if ADR crosses below level at shift."""
        logger.info("Evaluating ADR crosses_below: level=%.4f, shift=%d", level, shift)
        return crosses_below(adr, level, shift=shift)

    @classmethod
    def is_rising(cls, adr: IndicatorSeries, shift: int = 0) -> bool:
        """True if ADR is rising between shift+1 and shift."""
        logger.info("Evaluating ADR is_rising at shift=%d", shift)
        return is_rising(adr, shift=shift)

    @classmethod
    def is_falling(cls, adr: IndicatorSeries, shift: int = 0) -> bool:
        """True if ADR is falling between shift+1 and shift."""
        logger.info("Evaluating ADR is_falling at shift=%d", shift)
        return is_falling(adr, shift=shift)
