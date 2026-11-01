"""MFI indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-MFI: validated batch calculation.
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
MIN_MFI_PERIOD: int = 2
DEFAULT_MFI_PERIOD: int = 14
DEFAULT_OVERBOUGHT: float = 80.0
DEFAULT_OVERSOLD: float = 20.0
NEUTRAL_MFI: float = 50.0
MAX_MFI: float = 100.0
EPSILON: float = 1e-12


class MFI(BaseIndicator):
    """Money Flow Index volume-weighted momentum oscillator."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.mfi",
        name="MFI",
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
            "period": {"type": "int", "min": 2, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=DEFAULT_MFI_PERIOD, ge=MIN_MFI_PERIOD)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_MFI_PERIOD:
            raise ValueError(f"period must be >= {MIN_MFI_PERIOD}, got {self.period}")
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
        logger.info("MFI calculation initiated: period=%d", period)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n or (len(v_arr) != n):
            raise ValueError("Arrays cannot be empty and lengths must match")
        mfi_vals = self._compute_mfi(h_arr, l_arr, c_arr, v_arr, period=period)
        return {"value": IndicatorSeries(mfi_vals, name=f"MFI({period})")}

    @classmethod
    def _compute_mfi(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        *,
        period: int,
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        mfi = np.full(n, NEUTRAL_MFI, dtype=np.float64)
        if n < period + 1:
            return mfi
        typical = (h_arr + l_arr + c_arr) / 3.0
        raw_money = typical * v_arr
        pos_flow = np.zeros(n, dtype=np.float64)
        neg_flow = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            if typical[i] > typical[i - 1]:
                pos_flow[i] = raw_money[i]
            elif typical[i] < typical[i - 1]:
                neg_flow[i] = raw_money[i]
        for i in range(period, n):
            start = i - period + 1
            sum_pos = float(np.sum(pos_flow[start : i + 1]))
            sum_neg = float(np.sum(neg_flow[start : i + 1]))
            if sum_neg <= EPSILON:
                mfi[i] = MAX_MFI if sum_pos > 0.0 else NEUTRAL_MFI
            else:
                mr = sum_pos / sum_neg
                mfi[i] = MAX_MFI - MAX_MFI / (1.0 + mr)
        return mfi

    @classmethod
    def is_above_level(
        cls, mfi: IndicatorSeries, level: float = DEFAULT_OVERBOUGHT, shift: int = 0
    ) -> bool:
        """True if MFI is above specified level (overbought)."""
        logger.info("Evaluating MFI is_above_level=%.2f at shift=%d", level, shift)
        return is_greater(mfi, level, shift1=shift)

    @classmethod
    def is_below_level(
        cls, mfi: IndicatorSeries, level: float = DEFAULT_OVERSOLD, shift: int = 0
    ) -> bool:
        """True if MFI is below specified level (oversold)."""
        logger.info("Evaluating MFI is_below_level=%.2f at shift=%d", level, shift)
        return is_lower(mfi, level, shift1=shift)

    @classmethod
    def is_overbought(
        cls, mfi: IndicatorSeries, threshold: float = DEFAULT_OVERBOUGHT, shift: int = 0
    ) -> bool:
        """True if MFI is above overbought threshold."""
        logger.info(
            "Evaluating MFI is_overbought: threshold=%.2f, shift=%d", threshold, shift
        )
        return cls.is_above_level(mfi, level=threshold, shift=shift)

    @classmethod
    def is_oversold(
        cls, mfi: IndicatorSeries, threshold: float = DEFAULT_OVERSOLD, shift: int = 0
    ) -> bool:
        """True if MFI is below oversold threshold."""
        logger.info(
            "Evaluating MFI is_oversold: threshold=%.2f, shift=%d", threshold, shift
        )
        return cls.is_below_level(mfi, level=threshold, shift=shift)

    @classmethod
    def crosses_above(cls, mfi: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if MFI crosses above level."""
        logger.info("Evaluating MFI crosses_above level=%.2f at shift=%d", level, shift)
        return crosses_above(mfi, level, shift=shift)

    @classmethod
    def crosses_below(cls, mfi: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if MFI crosses below level."""
        logger.info("Evaluating MFI crosses_below level=%.2f at shift=%d", level, shift)
        return crosses_below(mfi, level, shift=shift)

    @classmethod
    def is_rising(cls, mfi: IndicatorSeries, shift: int = 0) -> bool:
        """True if MFI is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating MFI is_rising at shift=%d", shift)
        return is_rising(mfi, shift=shift)

    @classmethod
    def is_falling(cls, mfi: IndicatorSeries, shift: int = 0) -> bool:
        """True if MFI is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating MFI is_falling at shift=%d", shift)
        return is_falling(mfi, shift=shift)
