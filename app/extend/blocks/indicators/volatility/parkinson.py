"""ParkinsonVolatility indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-PARKINSONVOLATILITY: validated batch calculation.
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
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_PARKINSON_PERIOD: int = 2
DEFAULT_PARKINSON_PERIOD: int = 20
DEFAULT_TRADING_PERIODS: int = 252
EPSILON: float = 1e-12
PARKINSON_DENOM_FACTOR: float = 4.0 * np.log(2.0)


class ParkinsonVolatility(BaseIndicator):
    """Parkinson High-Low extreme value volatility estimator."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.parkinson",
        name="ParkinsonVolatility",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 80, "default": 20},
            "annualize": {"type": "bool", "choices": [False, True], "default": False},
            "trading_periods": {"type": "int", "min": 1, "max": 1008, "default": 252},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=DEFAULT_PARKINSON_PERIOD, ge=MIN_PARKINSON_PERIOD)
    annualize: bool = Field(default=False)
    trading_periods: int = Field(default=DEFAULT_TRADING_PERIODS, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_PARKINSON_PERIOD:
            raise ValueError(
                f"period must be >= {MIN_PARKINSON_PERIOD}, got {self.period}"
            )
        if self.trading_periods < 1:
            raise ValueError(
                f"trading_periods must be >= 1, got {self.trading_periods}"
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
        period = self.period
        annualize = self.annualize
        trading_periods = self.trading_periods
        logger.info(
            "ParkinsonVolatility initiated: period=%d, annualize=%s", period, annualize
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        ann_factor = np.sqrt(float(trading_periods)) if annualize else 1.0
        vol_vals = self._compute_parkinson(h_arr, l_arr, period, ann_factor)
        logger.info("ParkinsonVolatility completed: bars=%d", n)
        return {"value": IndicatorSeries(vol_vals, name=f"Parkinson({period})")}

    @classmethod
    def _compute_parkinson(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        ann_factor: float,
    ) -> np.ndarray[Any, Any]:
        n = len(h_arr)
        valid_l = np.maximum(l_arr, EPSILON)
        valid_h = np.maximum(h_arr, valid_l)
        log_hl = np.log(valid_h / valid_l)
        log_hl_sq = log_hl * log_hl
        vol = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            denom = PARKINSON_DENOM_FACTOR * window_len
            sum_sq = float(np.sum(log_hl_sq[start : i + 1]))
            vol[i] = np.sqrt(max(0.0, sum_sq / denom)) * ann_factor
        return vol

    @classmethod
    def is_elevated(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility exceeds specified threshold."""
        logger.info(
            "Evaluating Parkinson is_elevated: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_greater(vol, threshold, shift1=shift)

    @classmethod
    def is_subdued(cls, vol: IndicatorSeries, threshold: float, shift: int = 0) -> bool:
        """True if volatility is below specified threshold."""
        logger.info(
            "Evaluating Parkinson is_subdued: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_lower(vol, threshold, shift1=shift)

    @classmethod
    def crosses_above(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility crosses above threshold at shift."""
        logger.info(
            "Evaluating Parkinson crosses_above: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_above(vol, threshold, shift=shift)

    @classmethod
    def crosses_below(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility crosses below threshold at shift."""
        logger.info(
            "Evaluating Parkinson crosses_below: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_below(vol, threshold, shift=shift)

    @classmethod
    def is_rising(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is rising between shift+1 and shift."""
        logger.info("Evaluating Parkinson is_rising at shift=%d", shift)
        return is_rising(vol, shift=shift)

    @classmethod
    def is_falling(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is falling between shift+1 and shift."""
        logger.info("Evaluating Parkinson is_falling at shift=%d", shift)
        return is_falling(vol, shift=shift)
