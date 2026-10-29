"""HighestLowest indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-HIGHESTLOWEST: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import is_lower
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


class HighestLowest(BaseIndicator):
    """Highest and Lowest price extrema indicator with breakout condition evaluators."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.highest_lowest",
        name="HighestLowest",
        category="price_action",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=False),
        ),
        outputs=(
            OutputPort("highest", PortType.SERIES),
            OutputPort("lowest", PortType.SERIES),
            OutputPort("highest_index", PortType.SERIES),
            OutputPort("lowest_index", PortType.SERIES),
        ),
        required_market_inputs=("high",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < 1:
            raise ValueError(f"Period must be >= 1, got {self.period}")
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
        low = bars.low if bars.has_input("low") else None
        period = self.period
        logger.info(
            "HighestLowest calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low) if low is not None else h_arr
        if len(h_arr) == 0:
            raise ValueError("Input series cannot be empty")
        if len(h_arr) != len(l_arr):
            raise ValueError(
                f"High and low series length mismatch: {len(h_arr)} vs {len(l_arr)}"
            )
        n = len(h_arr)
        highest_vals = np.full(n, np.nan, dtype=np.float64)
        lowest_vals = np.full(n, np.nan, dtype=np.float64)
        highest_idx = np.full(n, np.nan, dtype=np.float64)
        lowest_idx = np.full(n, np.nan, dtype=np.float64)
        for i in range(n):
            start_idx = max(0, i - period + 1)
            h_win = h_arr[start_idx : i + 1]
            l_win = l_arr[start_idx : i + 1]
            max_val = np.max(h_win)
            min_val = np.min(l_win)
            highest_vals[i] = max_val
            lowest_vals[i] = min_val
            rel_max_idx = np.argmax(h_win)
            rel_min_idx = np.argmin(l_win)
            highest_idx[i] = float(len(h_win) - 1 - rel_max_idx)
            lowest_idx[i] = float(len(l_win) - 1 - rel_min_idx)
        logger.info(
            "HighestLowest calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return {
            "highest": IndicatorSeries(highest_vals, name=f"Highest({period})"),
            "lowest": IndicatorSeries(lowest_vals, name=f"Lowest({period})"),
            "highest_index": IndicatorSeries(
                highest_idx, name=f"HighestIndex({period})"
            ),
            "lowest_index": IndicatorSeries(lowest_idx, name=f"LowestIndex({period})"),
        }

    @staticmethod
    def bar_opens_above_highest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        highest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened above previous highest level after opening below.

        Formula:
            open[shift + 1] < highest[shift + 1] and open[shift] > highest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_above_highest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(
            open_prices, highest, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_greater(
            open_prices, highest, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def bar_opens_below_lowest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lowest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened below previous lowest level after opening above.

        Formula:
            open[shift + 1] > lowest[shift + 1] and open[shift] < lowest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_below_lowest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(
            open_prices, lowest, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_lower(
            open_prices, lowest, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def bar_opens_below_highest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        highest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened below previous highest level after opening above.

        Formula:
            open[shift + 1] > highest[shift + 1] and open[shift] < highest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_below_highest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(
            open_prices, highest, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_lower(
            open_prices, highest, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def bar_opens_above_lowest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lowest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened above previous lowest level after opening below.

        Formula:
            open[shift + 1] < lowest[shift + 1] and open[shift] > lowest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_above_lowest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(
            open_prices, lowest, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_greater(
            open_prices, lowest, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def cot_emergency_exit_long(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        low_prices: IndicatorSeries | np.ndarray[Any, Any],
        lookback: int = 20,
        shift: int = 0,
    ) -> bool:
        """Check if current close dropped below lowest low of lookback window.

        Formula:
            close[shift] < min(low[shift+1 : shift+1+lookback])
        """
        logger.info(
            "Evaluating cot_emergency_exit_long at shift=%d, lookback=%d",
            shift,
            lookback,
            extra={"shift": shift, "lookback": lookback},
        )
        c = to_numpy(close_prices)
        l_arr = to_numpy(low_prices)
        curr_bar = len(c) - 1 - shift
        if curr_bar < 0 or curr_bar >= len(c):
            return False
        start_bar = max(0, curr_bar - lookback)
        end_bar = curr_bar
        if start_bar >= end_bar:
            return False
        month_low = float(np.min(l_arr[start_bar:end_bar]))
        return is_lower(c, month_low, shift1=shift, round_digits=8)

    @staticmethod
    def cot_emergency_exit_short(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        high_prices: IndicatorSeries | np.ndarray[Any, Any],
        lookback: int = 20,
        shift: int = 0,
    ) -> bool:
        """Check if current close exceeded highest high of lookback window.

        Formula:
            close[shift] > max(high[shift+1 : shift+1+lookback])
        """
        logger.info(
            "Evaluating cot_emergency_exit_short at shift=%d, lookback=%d",
            shift,
            lookback,
            extra={"shift": shift, "lookback": lookback},
        )
        c = to_numpy(close_prices)
        h_arr = to_numpy(high_prices)
        curr_bar = len(c) - 1 - shift
        if curr_bar < 0 or curr_bar >= len(c):
            return False
        start_bar = max(0, curr_bar - lookback)
        end_bar = curr_bar
        if start_bar >= end_bar:
            return False
        month_high = float(np.max(h_arr[start_bar:end_bar]))
        return is_greater(c, month_high, shift1=shift, round_digits=8)
