"""SchaffTrendCycle indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-SCHAFFTRENDCYCLE: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np
from pydantic import Field

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
MIN_STC_PERIOD: int = 2
DEFAULT_STOCH_PERIOD: int = 10
DEFAULT_FAST_PERIOD: int = 20
DEFAULT_SLOW_PERIOD: int = 50
DEFAULT_FACTOR: float = 0.5


class SchaffTrendCycle(BaseIndicator):
    """Doug Schaff's Trend Cycle (STC) double-smoothed stochastic MACD indicator."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.schaff_trend_cycle",
        name="SchaffTrendCycle",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "stoch_period": {"type": "int", "min": 1, "max": 40, "default": 10},
            "fast_period": {"type": "int", "min": 1, "max": 80, "default": 20},
            "slow_period": {"type": "int", "min": 1, "max": 200, "default": 50},
            "factor": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "min_exclusive": True,
                "max_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=70,
    )
    stoch_period: int = Field(default=DEFAULT_STOCH_PERIOD, ge=1)
    fast_period: int = Field(default=DEFAULT_FAST_PERIOD, ge=1)
    slow_period: int = Field(default=DEFAULT_SLOW_PERIOD, ge=1)
    factor: float = Field(default=DEFAULT_FACTOR, gt=0.0, lt=1.0)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.fast_period, self.slow_period) + 2 * self.stoch_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        stoch_period = self.stoch_period
        fast_period = self.fast_period
        slow_period = self.slow_period
        factor = self.factor
        logger.info(
            "STC calculation initiated: stoch=%d, fast=%d, slow=%d",
            stoch_period,
            fast_period,
            slow_period,
            extra={
                "stoch_period": stoch_period,
                "fast_period": fast_period,
                "slow_period": slow_period,
            },
        )
        self._validate_params(stoch_period, fast_period, slow_period, factor)
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        stc_vals = np.zeros(n, dtype=np.float64)
        if n <= slow_period:
            return {"value": IndicatorSeries(stc_vals, name=f"STC({stoch_period})")}
        macd = self._calc_macd(p_arr, fast_period, slow_period)
        pf = self._run_first_cycle(macd, stoch_period, slow_period, factor)
        stc_vals = self._run_second_cycle(pf, stoch_period, slow_period, factor)
        logger.info("STC calculation complete: bars=%d", n, extra={"bars": n})
        return {"value": IndicatorSeries(stc_vals, name=f"STC({stoch_period})")}

    @classmethod
    def _validate_params(cls, stoch: int, fast: int, slow: int, factor: float) -> None:
        if stoch < MIN_STC_PERIOD:
            raise ValueError(f"stoch_period must be >= 2, got {stoch}")
        if fast < MIN_STC_PERIOD:
            raise ValueError(f"fast_period must be >= 2, got {fast}")
        if slow <= fast:
            raise ValueError(f"slow_period ({slow}) must be > fast_period ({fast})")
        if not 0.0 < factor <= 1.0:
            raise ValueError(f"factor must be in (0.0, 1.0], got {factor}")

    @classmethod
    def _calc_macd(
        cls, p_arr: np.ndarray[Any, Any], fast: int, slow: int
    ) -> np.ndarray[Any, Any]:
        """Compute MACD difference line."""
        fast_ema = cls._calc_ema(p_arr, fast)
        slow_ema = cls._calc_ema(p_arr, slow)
        return np.asarray(fast_ema - slow_ema, dtype=np.float64)

    @staticmethod
    def _calc_ema(arr: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
        n = len(arr)
        ema = np.zeros(n, dtype=np.float64)
        alpha = 2.0 / (period + 1.0)
        ema[0] = arr[0]
        for i in range(1, n):
            ema[i] = alpha * arr[i] + (1.0 - alpha) * ema[i - 1]
        return ema

    @staticmethod
    def _run_first_cycle(
        macd: np.ndarray[Any, Any], stoch_period: int, slow_period: int, factor: float
    ) -> np.ndarray[Any, Any]:
        n = len(macd)
        frac1 = np.zeros(n, dtype=np.float64)
        pf = np.zeros(n, dtype=np.float64)
        for i in range(slow_period, n):
            start_idx = max(0, i - stoch_period + 1)
            w = macd[start_idx : i + 1]
            v_min = float(np.min(w))
            v_range = float(np.max(w)) - v_min
            frac1[i] = (
                (macd[i] - v_min) / v_range * 100.0 if v_range > 0.0 else frac1[i - 1]
            )
            pf[i] = pf[i - 1] + factor * (frac1[i] - pf[i - 1])
        return pf

    @staticmethod
    def _run_second_cycle(
        pf: np.ndarray[Any, Any], stoch_period: int, slow_period: int, factor: float
    ) -> np.ndarray[Any, Any]:
        n = len(pf)
        frac2 = np.zeros(n, dtype=np.float64)
        stc = np.zeros(n, dtype=np.float64)
        for i in range(slow_period, n):
            start_idx = max(0, i - stoch_period + 1)
            w = pf[start_idx : i + 1]
            v3 = float(np.min(w))
            v4 = float(np.max(w)) - v3
            frac2[i] = (pf[i] - v3) / v4 * 100.0 if v4 > 0.0 else frac2[i - 1]
            stc[i] = stc[i - 1] + factor * (frac2[i] - stc[i - 1])
        return np.clip(stc, 0.0, 100.0)

    @staticmethod
    def is_above_level(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 75.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC is strictly above level."""
        logger.info("Evaluating STC is_above_level at shift=%d", shift)
        return is_greater(series, level, shift=shift)

    @staticmethod
    def is_below_level(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 25.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC is strictly below level."""
        logger.info("Evaluating STC is_below_level at shift=%d", shift)
        return is_lower(series, level, shift=shift)

    @staticmethod
    def crosses_above(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 25.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC crossed above a threshold level."""
        logger.info("Evaluating STC crosses_above at shift=%d", shift)
        return crosses_above(series, level, shift=shift)

    @staticmethod
    def crosses_below(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 75.0,
        shift: int = 0,
    ) -> bool:
        """Check if STC crossed below a threshold level."""
        logger.info("Evaluating STC crosses_below at shift=%d", shift)
        return crosses_below(series, level, shift=shift)

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if STC is rising."""
        logger.info("Evaluating STC is_rising at shift=%d", shift)
        return is_rising(series, shift=shift)

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if STC is falling."""
        logger.info("Evaluating STC is_falling at shift=%d", shift)
        return is_falling(series, shift=shift)
