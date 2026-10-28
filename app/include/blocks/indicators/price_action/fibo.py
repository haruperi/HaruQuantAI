"""Fibo indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-FIBO: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.host.logging import get_logger
from app.include.blocks.comparisons import crosses_above, crosses_below, is_lower
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
MIN_FIBO_PERIOD: int = 2
STANDARD_FIBO_LEVELS: tuple[float, ...] = (23.6, 38.2, 50.0, 61.8, 78.6, 100.0, 161.8)


class Fibo(BaseIndicator):
    """Fibonacci Retracement and Extension indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.fibo",
        name="Fibo",
        category="price_action",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
            InputPort("open", PortType.SERIES, required=False),
        ),
        outputs=(
            OutputPort("level_23_6", PortType.SERIES),
            OutputPort("level_38_2", PortType.SERIES),
            OutputPort("level_50_0", PortType.SERIES),
            OutputPort("level_61_8", PortType.SERIES),
            OutputPort("level_78_6", PortType.SERIES),
            OutputPort("level_100_0", PortType.SERIES),
            OutputPort("level_161_8", PortType.SERIES),
            OutputPort("custom", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=MIN_FIBO_PERIOD)
    custom_level: float | None = Field(default=None)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_FIBO_PERIOD:
            raise ValueError(f"Period must be >= 2, got {self.period}")
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
        open_prices = bars.open if bars.has_input("open") else None
        period = self.period
        custom_level = self.custom_level
        logger.info(
            "Fibo calculation initiated with period=%d, custom_level=%s",
            period,
            str(custom_level),
            extra={"period": period, "custom_level": custom_level},
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        o_arr = to_numpy(open_prices) if open_prices is not None else c_arr
        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not len(h_arr) == len(l_arr) == len(o_arr) == n:
            raise ValueError("All price input series must have equal lengths")
        levels_to_calc = list(STANDARD_FIBO_LEVELS)
        if custom_level is not None and custom_level not in levels_to_calc:
            levels_to_calc.append(custom_level)
        output_arrays: dict[float, np.ndarray[Any, Any]] = {
            lvl: np.full(n, np.nan, dtype=np.float64) for lvl in levels_to_calc
        }
        for i in range(period - 1, n):
            start_idx = i - period + 1
            upper = np.max(h_arr[start_idx : i + 1])
            lower = np.min(l_arr[start_idx : i + 1])
            step = (upper - lower) / 100.0
            is_bullish = c_arr[i] >= o_arr[start_idx]
            for lvl in levels_to_calc:
                delta = lvl * step
                output_arrays[lvl][i] = upper - delta if is_bullish else lower + delta
        result: dict[str, IndicatorSeries] = {}
        for lvl in STANDARD_FIBO_LEVELS:
            key = f"level_{str(lvl).replace('.', '_')}"
            result[key] = IndicatorSeries(output_arrays[lvl], name=f"Fibo({lvl}%)")
        if custom_level is not None:
            result["custom"] = IndicatorSeries(
                output_arrays[custom_level], name=f"Fibo({custom_level}%)"
            )
        else:
            result["custom"] = IndicatorSeries(np.full(n, np.nan), name="Fibo.Custom")
        logger.info(
            "Fibo calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return result

    @staticmethod
    def is_above_level(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly above a Fibonacci level."""
        logger.info(
            "Evaluating Fibo is_above_level at shift=%d", shift, extra={"shift": shift}
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return is_greater(price, level, shift=shift)

    @staticmethod
    def is_below_level(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly below a Fibonacci level."""
        logger.info(
            "Evaluating Fibo is_below_level at shift=%d", shift, extra={"shift": shift}
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return is_lower(price, level, shift=shift)

    @staticmethod
    def crosses_above(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed above a Fibonacci level."""
        logger.info(
            "Evaluating Fibo crosses_above at shift=%d", shift, extra={"shift": shift}
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_above(price, level, shift=shift)

    @staticmethod
    def crosses_below(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed below a Fibonacci level."""
        logger.info(
            "Evaluating Fibo crosses_below at shift=%d", shift, extra={"shift": shift}
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_below(price, level, shift=shift)
