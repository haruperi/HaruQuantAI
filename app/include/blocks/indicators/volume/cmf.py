"""CMF indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-CMF: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
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
MIN_CMF_PERIOD: int = 1
DEFAULT_CMF_PERIOD: int = 20
EPSILON: float = 1e-12


class CMF(BaseIndicator):
    """Chaikin Money Flow volume accumulation/distribution indicator."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.cmf",
        name="CMF",
        category="volume",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close", "volume"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=DEFAULT_CMF_PERIOD, ge=MIN_CMF_PERIOD)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_CMF_PERIOD:
            raise ValueError(f"period must be >= {MIN_CMF_PERIOD}, got {self.period}")
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
        volume = bars.volume
        period = self.period
        logger.info("CMF calculation initiated: period=%d", period)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n or (len(v_arr) != n):
            raise ValueError("Arrays cannot be empty and lengths must match")
        cmf_vals = self._compute_cmf(h_arr, l_arr, c_arr, v_arr, period=period)
        return {"value": IndicatorSeries(cmf_vals, name=f"CMF({period})")}

    @classmethod
    def _compute_cmf(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        *,
        period: int,
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        cmf = np.zeros(n, dtype=np.float64)
        rng = h_arr - l_arr
        mfm = np.zeros(n, dtype=np.float64)
        valid_rng = rng > EPSILON
        mfm[valid_rng] = (
            c_arr[valid_rng] - l_arr[valid_rng] - (h_arr[valid_rng] - c_arr[valid_rng])
        ) / rng[valid_rng]
        mfv = mfm * v_arr
        for i in range(n):
            start = max(0, i - period + 1)
            sum_mfv = float(np.sum(mfv[start : i + 1]))
            sum_vol = float(np.sum(v_arr[start : i + 1]))
            cmf[i] = sum_mfv / sum_vol if sum_vol > EPSILON else 0.0
        return cmf

    @classmethod
    def is_above_zero(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is above zero (buying pressure)."""
        logger.info("Evaluating CMF is_above_zero at shift=%d", shift)
        return is_greater(cmf, 0.0, shift1=shift)

    @classmethod
    def is_below_zero(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is below zero (selling pressure)."""
        logger.info("Evaluating CMF is_below_zero at shift=%d", shift)
        return is_lower(cmf, 0.0, shift1=shift)

    @classmethod
    def crosses_above(
        cls, cmf: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if CMF crosses above specified level."""
        logger.info("Evaluating CMF crosses_above level=%.2f at shift=%d", level, shift)
        return crosses_above(cmf, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, cmf: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if CMF crosses below specified level."""
        logger.info("Evaluating CMF crosses_below level=%.2f at shift=%d", level, shift)
        return crosses_below(cmf, level, shift=shift)

    @classmethod
    def is_rising(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating CMF is_rising at shift=%d", shift)
        return is_rising(cmf, shift=shift)

    @classmethod
    def is_falling(cls, cmf: IndicatorSeries, shift: int = 0) -> bool:
        """True if CMF is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating CMF is_falling at shift=%d", shift)
        return is_falling(cmf, shift=shift)
