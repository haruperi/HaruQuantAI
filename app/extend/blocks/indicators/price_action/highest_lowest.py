"""HighestLowest indicator.

- Calculates rolling highest high and lowest low price channels.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import is_lower
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)


class HighestLowest(BaseIndicator):
    """Highest and Lowest price extrema indicator with breakout condition evaluators."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.highest_lowest",
        version="1.0.0",
        name="HighestLowest",
        description="Calculates rolling highest high and lowest low price channels.",
        category="price_action",
        tags=("price_action", "highest-lowest"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=False, description="Low input series"
            ),
        ),
        outputs=(
            OutputPort("highest", PortType.SERIES, description="Highest output series"),
            OutputPort("lowest", PortType.SERIES, description="Lowest output series"),
            OutputPort(
                "highest_index",
                PortType.SERIES,
                description="Highest index output series",
            ),
            OutputPort(
                "lowest_index",
                PortType.SERIES,
                description="Lowest index output series",
            ),
        ),
        required_market_inputs=("high",),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < 1:
            raise ValueError(f"Period must be >= 1, got {self.period}")
        return self

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: HighestLowest requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
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

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["HighestLowest"]
