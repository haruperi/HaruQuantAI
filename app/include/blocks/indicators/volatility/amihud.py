"""AmihudIlliquidity indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AMIHUDILLIQUIDITY: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_AMIHUD_PERIOD: int = 1
DEFAULT_AMIHUD_PERIOD: int = 20
DEFAULT_AMIHUD_MULTIPLIER: float = 1000000.0
EPSILON: float = 1e-12


class AmihudIlliquidity(BaseIndicator):
    """Amihud illiquidity price impact ratio indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.amihud",
        name="AmihudIlliquidity",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close", "volume"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20},
            "multiplier": {
                "type": "float",
                "min": 0.0,
                "max": 4000000.0,
                "default": 1000000.0,
                "min_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=DEFAULT_AMIHUD_PERIOD, ge=MIN_AMIHUD_PERIOD)
    multiplier: float = Field(default=DEFAULT_AMIHUD_MULTIPLIER, gt=0.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_AMIHUD_PERIOD:
            raise ValueError(
                f"period must be >= {MIN_AMIHUD_PERIOD}, got {self.period}"
            )
        if self.multiplier <= 0.0:
            raise ValueError(f"multiplier must be > 0.0, got {self.multiplier}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = bars.close
        volume = bars.volume
        period = self.period
        multiplier = self.multiplier
        logger.info(
            "AmihudIlliquidity initiated: period=%d, mult=%.1e", period, multiplier
        )
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        amihud_vals = self._compute_amihud(c_arr, v_arr, period, multiplier, n=n)
        logger.info("AmihudIlliquidity completed: bars=%d", n)
        return {"value": IndicatorSeries(amihud_vals, name=f"Amihud({period})")}

    @classmethod
    def _compute_amihud(
        cls,
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        period: int,
        multiplier: float,
        *,
        n: int,
    ) -> np.ndarray[Any, Any]:
        ret = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            prev_c = c_arr[i - 1]
            if prev_c > EPSILON:
                ret[i] = abs(c_arr[i] - prev_c) / prev_c
        dollar_vol = c_arr * v_arr
        raw_ratio = np.zeros(n, dtype=np.float64)
        valid_dv = dollar_vol > EPSILON
        raw_ratio[valid_dv] = ret[valid_dv] / dollar_vol[valid_dv] * multiplier
        amihud = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            amihud[i] = float(np.sum(raw_ratio[start : i + 1])) / window_len
        return amihud

    @classmethod
    def is_illiquid(
        cls, amihud: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if illiquidity ratio exceeds threshold (illiquid/thin market)."""
        logger.info(
            "Evaluating Amihud is_illiquid: threshold=%.4f, shift=%d", threshold, shift
        )
        return is_greater(amihud, threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_liquid(
        cls, amihud: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if illiquidity ratio is below threshold (liquid/deep market)."""
        logger.info(
            "Evaluating Amihud is_liquid: threshold=%.4f, shift=%d", threshold, shift
        )
        return is_lower(amihud, threshold, shift1=shift, round_digits=8)

    @classmethod
    def crosses_above(
        cls, amihud: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """True if Amihud ratio crosses above level at shift."""
        logger.info(
            "Evaluating Amihud crosses_above: level=%.4f, shift=%d", level, shift
        )
        return crosses_above(amihud, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, amihud: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """True if Amihud ratio crosses below level at shift."""
        logger.info(
            "Evaluating Amihud crosses_below: level=%.4f, shift=%d", level, shift
        )
        return crosses_below(amihud, level, shift=shift)

    @classmethod
    def is_rising(cls, amihud: IndicatorSeries, shift: int = 0) -> bool:
        """True if Amihud ratio is rising between shift+1 and shift."""
        logger.info("Evaluating Amihud is_rising at shift=%d", shift)
        return is_rising(amihud, shift=shift)

    @classmethod
    def is_falling(cls, amihud: IndicatorSeries, shift: int = 0) -> bool:
        """True if Amihud ratio is falling between shift+1 and shift."""
        logger.info("Evaluating Amihud is_falling at shift=%d", shift)
        return is_falling(amihud, shift=shift)
