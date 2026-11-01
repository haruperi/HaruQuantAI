"""GannHiLo indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-GANNHILO: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import crosses_above, crosses_below, is_lower
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


class GannHiLo(BaseIndicator):
    """Gann High-Low Activator indicator with trend regime tracking."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.gann_hi_lo",
        name="GannHiLo",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("gha", PortType.SERIES),
            OutputPort("gh_high", PortType.SERIES),
            OutputPort("gh_low", PortType.SERIES),
            OutputPort("trend", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 40, "default": 10}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=11,
    )
    period: int = Field(default=10, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < 1:
            raise ValueError(f"Period must be >= 1, got {self.period}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        logger.info(
            "GannHiLo calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not len(h_arr) == len(l_arr) == n:
            raise ValueError(
                f"Array mismatch: high({len(h_arr)}), low({len(l_arr)}), close({n})"
            )
        gha_vals = np.full(n, np.nan, dtype=np.float64)
        gh_high_vals = np.full(n, np.nan, dtype=np.float64)
        gh_low_vals = np.full(n, np.nan, dtype=np.float64)
        trend_vals = np.zeros(n, dtype=np.float64)
        if n < period:
            return {
                "gha": IndicatorSeries(gha_vals, name=f"GHA({period})"),
                "gh_high": IndicatorSeries(gh_high_vals, name=f"GHHigh({period})"),
                "gh_low": IndicatorSeries(gh_low_vals, name=f"GHLow({period})"),
                "trend": IndicatorSeries(trend_vals, name=f"GHTrend({period})"),
            }
        for i in range(period - 1, n):
            gh_high_vals[i] = np.mean(h_arr[i - period + 1 : i + 1])
            gh_low_vals[i] = np.mean(l_arr[i - period + 1 : i + 1])
        hlv = 1.0
        for i in range(period, n):
            prev_high_sma = gh_high_vals[i - 1]
            prev_low_sma = gh_low_vals[i - 1]
            curr_close = c_arr[i]
            if curr_close > prev_high_sma:
                hlv = 1.0
            elif curr_close < prev_low_sma:
                hlv = -1.0
            trend_vals[i] = hlv
            gha_vals[i] = gh_high_vals[i] if hlv == -1.0 else gh_low_vals[i]
        logger.info(
            "GannHiLo calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return {
            "gha": IndicatorSeries(gha_vals, name=f"GHA({period})"),
            "gh_high": IndicatorSeries(gh_high_vals, name=f"GHHigh({period})"),
            "gh_low": IndicatorSeries(gh_low_vals, name=f"GHLow({period})"),
            "trend": IndicatorSeries(trend_vals, name=f"GHTrend({period})"),
        }

    @staticmethod
    def is_uptrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is above the Gann Hi-Lo Activator line (Uptrend).

        Formula:
            close[shift] > gha[shift]
        """
        logger.info(
            "Evaluating GannHiLo is_uptrend at shift=%d", shift, extra={"shift": shift}
        )
        return is_greater(close_prices, gha, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def is_downtrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is below the Gann Hi-Lo Activator line (Downtrend).

        Formula:
            close[shift] < gha[shift]
        """
        logger.info(
            "Evaluating GannHiLo is_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(close_prices, gha, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def turns_uptrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close turned from below or equal to GHA into above GHA."""
        logger.info(
            "Evaluating GannHiLo turns_uptrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return crosses_above(close_prices, gha, shift=shift, round_digits=8)

    @staticmethod
    def turns_downtrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close turned from above or equal to GHA into below GHA."""
        logger.info(
            "Evaluating GannHiLo turns_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return crosses_below(close_prices, gha, shift=shift, round_digits=8)
