"""QQE momentum indicator strategy block.

Description:
    Calculates Quantitative Qualitative Estimation (QQE) smoothed RSI
    and fast/slow volatility trail lines.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: QQE indicator calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.qqe import QQE
    res = QQE().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
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
MIN_RSI_PERIOD: int = 2
DEFAULT_RSI_PERIOD: int = 14
DEFAULT_SF: int = 5
DEFAULT_WF: float = 4.236


class QQE(BaseIndicator):
    """Quantitative Qualitative Estimation indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.qqe",
        name="QQE",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("value1", PortType.SERIES),
            OutputPort("value2", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "rsi_period": {"type": "int", "min": 2, "max": 56, "default": 14},
            "sf": {"type": "int", "min": 1, "max": 20, "default": 5},
            "wf": {
                "type": "float",
                "min": 0.0,
                "max": 16.944,
                "default": 4.236,
                "min_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=19,
    )
    rsi_period: int = Field(default=DEFAULT_RSI_PERIOD, ge=MIN_RSI_PERIOD)
    sf: int = Field(default=DEFAULT_SF, ge=1)
    wf: float = Field(default=DEFAULT_WF, gt=0.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.rsi_period < MIN_RSI_PERIOD:
            raise ValueError(f"rsi_period must be >= 2, got {self.rsi_period}")
        if self.sf < 1:
            raise ValueError(f"sf must be >= 1, got {self.sf}")
        if self.wf <= 0.0:
            raise ValueError(f"wf must be > 0.0, got {self.wf}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.rsi_period + self.sf

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        rsi_period = self.rsi_period
        sf = self.sf
        wf = self.wf
        logger.info(
            "QQE calculation initiated: rsi_period=%d, sf=%d, wf=%.3f",
            rsi_period,
            sf,
            wf,
            extra={"rsi_period": rsi_period, "sf": sf, "wf": wf},
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if n < rsi_period + 1:
            nan_arr = np.full(n, np.nan)
            return {
                "value1": IndicatorSeries(nan_arr, name=f"QQE1({rsi_period})"),
                "value2": IndicatorSeries(nan_arr, name=f"QQE2({rsi_period})"),
            }
        raw_rsi = self._calc_raw_rsi(p_arr, rsi_period)
        val1 = self._calc_ema(raw_rsi, sf)
        wilders_period = rsi_period * 2 - 1
        atr_rsi = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            atr_rsi[i] = abs(val1[i] - val1[i - 1])
        smoothed_atr1 = self._calc_ema(atr_rsi, wilders_period)
        smoothed_atr2 = self._calc_ema(smoothed_atr1, wilders_period)
        dar = smoothed_atr2 * wf
        val2 = self._calc_trailing_stop(val1, dar, rsi_period)
        logger.info(
            "QQE calculation complete: bars=%d, rsi_period=%d",
            n,
            rsi_period,
            extra={"bars": n, "rsi_period": rsi_period},
        )
        return {
            "value1": IndicatorSeries(val1, name=f"QQE_Value1({rsi_period})"),
            "value2": IndicatorSeries(val2, name=f"QQE_Value2({rsi_period})"),
        }

    @staticmethod
    def _calc_raw_rsi(p_arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        """Compute standard Wilder's RSI."""
        n = len(p_arr)
        rsi = np.full(n, 50.0, dtype=np.float64)
        diff = np.diff(p_arr)
        gains = np.maximum(diff, 0.0)
        losses = np.maximum(-diff, 0.0)
        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))
        alpha = 1.0 / period
        for i in range(period, n - 1):
            avg_gain = alpha * gains[i] + (1.0 - alpha) * avg_gain
            avg_loss = alpha * losses[i] + (1.0 - alpha) * avg_loss
            if avg_loss == 0.0:
                rsi[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i + 1] = 100.0 - 100.0 / (1.0 + rs)
        return rsi

    @staticmethod
    def _calc_ema(arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        """Compute Exponential Moving Average."""
        n = len(arr)
        ema = np.zeros(n, dtype=np.float64)
        if n == 0:
            return ema
        alpha = 2.0 / (period + 1.0)
        ema[0] = arr[0]
        for i in range(1, n):
            ema[i] = alpha * arr[i] + (1.0 - alpha) * ema[i - 1]
        return ema

    @staticmethod
    def _calc_trailing_stop(
        val1: np.ndarray[Any, Any], dar: np.ndarray[Any, Any], start_idx: int
    ) -> np.ndarray[Any, Any]:
        """Compute dynamic trailing stop line Value2."""
        n = len(val1)
        val2 = np.full(n, 50.0, dtype=np.float64)
        tr = 50.0
        for i in range(start_idx, n):
            dv = tr
            rsi0 = val1[i]
            rsi1 = val1[i - 1]
            curr_dar = dar[i]
            if rsi0 < tr:
                tr = rsi0 + curr_dar
                if rsi1 < dv and tr > dv:
                    tr = dv
            elif rsi0 > tr:
                tr = rsi0 - curr_dar
                if rsi1 > dv and tr < dv:
                    tr = dv
            val2[i] = tr
        return val2

    @staticmethod
    def value1_crosses_above_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossAboveValue2."""
        logger.info("Evaluating QQE value1_crosses_above_value2 at shift=%d", shift)
        return crosses_above(value1, value2, shift=shift)

    @staticmethod
    def value1_crosses_below_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1CrossBelowValue2."""
        logger.info("Evaluating QQE value1_crosses_below_value2 at shift=%d", shift)
        return crosses_below(value1, value2, shift=shift)

    @staticmethod
    def value1_higher_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1HigherValue2."""
        logger.info("Evaluating QQE value1_higher_value2 at shift=%d", shift)
        return is_greater(value1, value2, shift=shift)

    @staticmethod
    def value1_lower_value2(
        value1: IndicatorSeries | np.ndarray[Any, Any],
        value2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Evaluate QQEValue1LowerValue2."""
        logger.info("Evaluating QQE value1_lower_value2 at shift=%d", shift)
        return is_lower(value1, value2, shift=shift)

    @staticmethod
    def value1_is_rising(
        value1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate QQEValue1Rising."""
        logger.info("Evaluating QQE value1_is_rising at shift=%d", shift)
        return is_rising(value1, shift=shift)

    @staticmethod
    def value1_is_falling(
        value1: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Evaluate QQEValue1Falling."""
        logger.info("Evaluating QQE value1_is_falling at shift=%d", shift)
        return is_falling(value1, shift=shift)
