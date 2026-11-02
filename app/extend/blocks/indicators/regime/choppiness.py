"""ChoppinessIndex regime indicator strategy block.

Description:
    Calculates Choppiness Index differentiating trending from ranging regimes.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator library.
Key Capabilities:
    - FR-indicator-regime: Choppiness index market regime classification.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.regime.choppiness import (
        ChoppinessIndex,
    )
    res = ChoppinessIndex().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_greater_or_equal,
    is_lower,
    is_lower_or_equal,
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
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
REGIME_DIRECTIONAL: float = 0.0
REGIME_TRANSITION: float = 1.0
REGIME_CHOPPY: float = 2.0
MIN_CHOP_PERIOD: int = 2
DEFAULT_PERIOD: int = 14
DEFAULT_LOWER_THRESHOLD: float = 38.2
DEFAULT_UPPER_THRESHOLD: float = 61.8
DEFAULT_MID_CHOP: float = 50.0
SCALE_FACTOR: float = 100.0
EPSILON: float = 1e-12


class ChoppinessIndex(BaseIndicator):
    """Choppiness Index indicator and market trend regime classifier."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.choppiness",
        name="ChoppinessIndex",
        category="regime",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("chop", PortType.SERIES),
            OutputPort("regime", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 56, "default": 14},
            "lower_threshold": {
                "type": "float",
                "min": 0,
                "max": 152.8,
                "default": 38.2,
            },
            "upper_threshold": {
                "type": "float",
                "min": 0,
                "max": 247.2,
                "default": 61.8,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=DEFAULT_PERIOD, ge=MIN_CHOP_PERIOD)
    lower_threshold: float = Field(default=DEFAULT_LOWER_THRESHOLD)
    upper_threshold: float = Field(default=DEFAULT_UPPER_THRESHOLD)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.lower_threshold >= self.upper_threshold:
            raise ValueError("lower_threshold must be below upper_threshold")
        return self

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_CHOP_PERIOD:
            raise ValueError(f"period must be >= {MIN_CHOP_PERIOD}, got {self.period}")
        if self.lower_threshold >= self.upper_threshold:
            raise ValueError(
                "lower_threshold must be strictly less than upper_threshold"
            )
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
        close = bars.close
        period = self.period
        lower_threshold = self.lower_threshold
        upper_threshold = self.upper_threshold
        logger.info(
            "ChoppinessIndex initiated: period=%d, lower=%.1f, upper=%.1f",
            period,
            lower_threshold,
            upper_threshold,
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Price arrays cannot be empty and lengths must match")
        chop_vals, regime_vals = self._compute_chop_arrays(
            h_arr,
            l_arr,
            c_arr,
            period=period,
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )
        return {
            "chop": IndicatorSeries(chop_vals, name=f"CHOP({period})"),
            "regime": IndicatorSeries(regime_vals, name=f"CHOP_Regime({period})"),
        }

    @classmethod
    def _compute_chop_arrays(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        *,
        period: int,
        lower_threshold: float,
        upper_threshold: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Compute rolling True Range sum and log span ratios."""
        n = len(c_arr)
        chop_vals = np.full(n, DEFAULT_MID_CHOP, dtype=np.float64)
        regime_vals = np.full(n, REGIME_TRANSITION, dtype=np.float64)
        if n < period:
            return (chop_vals, regime_vals)
        tr = np.zeros(n, dtype=np.float64)
        tr[0] = h_arr[0] - l_arr[0]
        for i in range(1, n):
            hl = h_arr[i] - l_arr[i]
            hc = abs(h_arr[i] - c_arr[i - 1])
            lc = abs(l_arr[i] - c_arr[i - 1])
            tr[i] = max(hl, hc, lc)
        log10_period = math.log10(period)
        for i in range(period - 1, n):
            start = i - period + 1
            sum_tr = float(np.sum(tr[start : i + 1]))
            max_h = float(np.max(h_arr[start : i + 1]))
            min_l = float(np.min(l_arr[start : i + 1]))
            span = max_h - min_l
            chop = DEFAULT_MID_CHOP
            if span > EPSILON and sum_tr > 0.0:
                ratio = sum_tr / span
                if ratio > 0.0:
                    raw_chop = SCALE_FACTOR * math.log10(ratio) / log10_period
                    chop = max(0.0, min(SCALE_FACTOR, raw_chop))
            chop_vals[i] = chop
            regime_vals[i] = cls._classify_regime(
                chop, lower_threshold, upper_threshold
            )
        return (chop_vals, regime_vals)

    @staticmethod
    def _classify_regime(
        chop: float, lower_threshold: float, upper_threshold: float
    ) -> float:
        """Map choppiness index value to discrete regime code."""
        if chop <= lower_threshold:
            return REGIME_DIRECTIONAL
        if chop >= upper_threshold:
            return REGIME_CHOPPY
        return REGIME_TRANSITION

    @classmethod
    def is_trending(
        cls,
        chop: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is in a strong directional trend."""
        logger.info("Evaluating Choppiness is_trending at shift=%d", shift)
        return is_lower_or_equal(chop, lower_threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_choppy(
        cls,
        chop: IndicatorSeries,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is choppy / consolidating."""
        logger.info("Evaluating Choppiness is_choppy at shift=%d", shift)
        return is_greater_or_equal(chop, upper_threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_in_transition(
        cls,
        chop: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if market is in transition between trend and consolidation."""
        logger.info("Evaluating Choppiness is_in_transition at shift=%d", shift)
        return is_greater(
            chop, lower_threshold, shift1=shift, round_digits=8
        ) and is_lower(chop, upper_threshold, shift1=shift, round_digits=8)

    @classmethod
    def crosses_above(cls, chop: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if Choppiness crosses above specified level."""
        logger.info(
            "Evaluating CHOP crosses_above level=%.2f at shift=%d", level, shift
        )
        return crosses_above(chop, level, shift=shift)

    @classmethod
    def crosses_below(cls, chop: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if Choppiness crosses below specified level."""
        logger.info(
            "Evaluating CHOP crosses_below level=%.2f at shift=%d", level, shift
        )
        return crosses_below(chop, level, shift=shift)
