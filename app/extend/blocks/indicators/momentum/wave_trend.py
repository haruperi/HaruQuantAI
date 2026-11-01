"""WaveTrend indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-WAVETREND: validated batch calculation.
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
    is_rising,
)
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
MIN_WT_PERIOD: int = 2
DEFAULT_CHANNEL_LENGTH: int = 10
DEFAULT_AVERAGE_LENGTH: int = 21
DEFAULT_SIGNAL_LENGTH: int = 4
CI_FACTOR: float = 0.015
EPSILON: float = 1e-12


class WaveTrend(BaseIndicator):
    """WaveTrend oscillator block generating Main (WT1) and Signal (WT2) lines."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.wave_trend",
        name="WaveTrend",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=False),
            InputPort("close", PortType.SERIES, required=False),
        ),
        outputs=(
            OutputPort("wt1", PortType.SERIES),
            OutputPort("wt2", PortType.SERIES),
        ),
        required_market_inputs=("high",),
        parameter_search_space={
            "channel_length": {"type": "int", "min": 2, "max": 40, "default": 10},
            "average_length": {"type": "int", "min": 2, "max": 84, "default": 21},
            "signal_length": {"type": "int", "min": 1, "max": 16, "default": 4},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=33,
    )
    channel_length: int = Field(default=DEFAULT_CHANNEL_LENGTH, ge=MIN_WT_PERIOD)
    average_length: int = Field(default=DEFAULT_AVERAGE_LENGTH, ge=MIN_WT_PERIOD)
    signal_length: int = Field(default=DEFAULT_SIGNAL_LENGTH, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if (
            self.channel_length < MIN_WT_PERIOD
            or self.average_length < MIN_WT_PERIOD
            or self.signal_length < 1
        ):
            raise ValueError("Lengths must satisfy channel>=2, avg>=2, signal>=1")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.channel_length + self.average_length + self.signal_length - 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low if bars.has_input("low") else None
        close = bars.close if bars.has_input("close") else None
        channel_length = self.channel_length
        average_length = self.average_length
        signal_length = self.signal_length
        logger.info(
            "WaveTrend calculation initiated: ch=%d, avg=%d, sig=%d",
            channel_length,
            average_length,
            signal_length,
            extra={
                "channel_length": channel_length,
                "average_length": average_length,
                "signal_length": signal_length,
            },
        )
        ap = self._compute_typical_price(high, low, close)
        n = len(ap)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        wt1_vals, wt2_vals = self._compute_wt_lines(
            ap, channel_length, average_length, signal_length
        )
        logger.info("WaveTrend calculation complete: bars=%d", n, extra={"bars": n})
        return {
            "wt1": IndicatorSeries(wt1_vals, name=f"WT1({channel_length})"),
            "wt2": IndicatorSeries(wt2_vals, name=f"WT2({signal_length})"),
        }

    @classmethod
    def _compute_typical_price(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any] | None,
        close: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> np.ndarray[Any, Any]:
        """Derive typical price array (H+L+C)/3.0 or single price array."""
        h_arr = to_numpy(high)
        if low is None or close is None:
            return h_arr
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        if not len(h_arr) == len(l_arr) == len(c_arr):
            raise ValueError("High, Low, and Close array lengths must match")
        return np.asarray((h_arr + l_arr + c_arr) / 3.0, dtype=np.float64)

    @classmethod
    def _compute_wt_lines(
        cls, ap: np.ndarray[Any, Any], channel_len: int, avg_len: int, sig_len: int
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Compute recursive WaveTrend filter stages."""
        n = len(ap)
        wt1 = np.zeros(n, dtype=np.float64)
        wt2 = np.zeros(n, dtype=np.float64)
        esa_mult = 2.0 / (channel_len + 1.0)
        d_mult = 2.0 / (channel_len + 1.0)
        tci_mult = 2.0 / (avg_len + 1.0)
        wt2_mult = 2.0 / (sig_len + 1.0)
        esa = np.zeros(n, dtype=np.float64)
        d = np.zeros(n, dtype=np.float64)
        esa[0] = ap[0]
        d[0] = 0.0
        for i in range(1, n):
            curr_ap = ap[i]
            curr_esa = esa_mult * curr_ap + (1.0 - esa_mult) * esa[i - 1]
            esa[i] = curr_esa
            diff = abs(curr_ap - curr_esa)
            curr_d = d_mult * diff + (1.0 - d_mult) * d[i - 1]
            d[i] = curr_d
            denom = CI_FACTOR * curr_d
            if curr_d > EPSILON and denom > EPSILON:
                ci = (curr_ap - curr_esa) / denom
                curr_wt1 = tci_mult * ci + (1.0 - tci_mult) * wt1[i - 1]
                curr_wt2 = wt2_mult * curr_wt1 + (1.0 - wt2_mult) * wt2[i - 1]
            else:
                curr_wt1 = wt1[i - 1]
                curr_wt2 = wt2[i - 1]
            wt1[i] = curr_wt1
            wt2[i] = curr_wt2
        return (wt1, wt2)

    @staticmethod
    def wt1_crosses_above_wt2(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        wt2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate WaveTrendMainCrossAboveSignal."""
        logger.info("Evaluating WaveTrend wt1_crosses_above_wt2 at shift=%d", shift)
        return crosses_above(wt1, wt2, shift=shift)

    @staticmethod
    def wt1_crosses_below_wt2(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        wt2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate WaveTrendMainCrossBelowSignal."""
        logger.info("Evaluating WaveTrend wt1_crosses_below_wt2 at shift=%d", shift)
        return crosses_below(wt1, wt2, shift=shift)

    @staticmethod
    def wt1_crosses_above_zero(
        wt1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate WaveTrendMainCrossAboveZero."""
        logger.info("Evaluating WaveTrend wt1_crosses_above_zero at shift=%d", shift)
        return crosses_above(wt1, 0.0, shift=shift)

    @staticmethod
    def wt1_crosses_below_zero(
        wt1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate WaveTrendMainCrossBelowZero."""
        logger.info("Evaluating WaveTrend wt1_crosses_below_zero at shift=%d", shift)
        return crosses_below(wt1, 0.0, shift=shift)

    @staticmethod
    def wt1_is_rising(
        wt1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate WaveTrendMainRising."""
        logger.info("Evaluating WaveTrend wt1_is_rising at shift=%d", shift)
        return is_rising(wt1, shift=shift)

    @staticmethod
    def wt1_is_falling(
        wt1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate WaveTrendMainFalling."""
        logger.info("Evaluating WaveTrend wt1_is_falling at shift=%d", shift)
        return is_falling(wt1, shift=shift)
