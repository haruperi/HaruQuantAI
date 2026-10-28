"""Trend indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-TREND: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal, Self, override

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


class Trend(BaseIndicator):
    """Trend regime classifier evaluating price position relative to baseline."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.trend",
        name="Trend",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("trend", PortType.SERIES),
            OutputPort("baseline", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 800, "default": 200},
            "method": {"type": "str", "choices": ["sma", "ema"], "default": "sma"},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=200,
    )
    period: int = Field(default=200, ge=1)
    method: Literal["sma", "ema"] = Field(default="sma")

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
        price = bars.close
        period = self.period
        method = self.method
        logger.info(
            "Trend calculation initiated with period=%d, method=%s",
            period,
            method,
            extra={"period": period, "method": method},
        )
        clean_method = method.strip().lower()
        if clean_method not in ("sma", "ema"):
            raise ValueError(f"Unsupported method '{method}'; choose 'sma' or 'ema'")
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if n < period:
            return {
                "trend": IndicatorSeries(np.zeros(n), name=f"Trend({period})"),
                "baseline": IndicatorSeries(
                    np.full(n, np.nan), name=f"TrendBaseline({period})"
                ),
            }
        baseline_vals = self._compute_baseline(p_arr, period, clean_method)
        trend_vals = self._classify_trend(p_arr, baseline_vals, period)
        logger.info(
            "Trend calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return {
            "trend": IndicatorSeries(trend_vals, name=f"Trend({period})"),
            "baseline": IndicatorSeries(baseline_vals, name=f"TrendBaseline({period})"),
        }

    @staticmethod
    def _compute_baseline(
        p_arr: np.ndarray[Any, Any], period: int, method: str
    ) -> np.ndarray[Any, Any]:
        """Compute moving average baseline values."""
        n = len(p_arr)
        baseline = np.full(n, np.nan, dtype=np.float64)
        if method == "sma":
            for i in range(period - 1, n):
                baseline[i] = np.mean(p_arr[i - period + 1 : i + 1])
        else:
            alpha = 2.0 / (period + 1.0)
            baseline[period - 1] = np.mean(p_arr[:period])
            for i in range(period, n):
                baseline[i] = alpha * p_arr[i] + (1.0 - alpha) * baseline[i - 1]
        return baseline

    @staticmethod
    def _classify_trend(
        p_arr: np.ndarray[Any, Any], baseline: np.ndarray[Any, Any], period: int
    ) -> np.ndarray[Any, Any]:
        """Classify trend state based on price vs baseline position."""
        n = len(p_arr)
        trend = np.zeros(n, dtype=np.float64)
        for i in range(period - 1, n):
            base_val = baseline[i]
            if np.isnan(base_val):
                continue
            if p_arr[i] > base_val:
                trend[i] = 1.0
            elif p_arr[i] < base_val:
                trend[i] = -1.0
        return trend

    @staticmethod
    def is_uptrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly above the baseline (Uptrend).

        Formula:
            price[shift] > baseline[shift]
        """
        logger.info(
            "Evaluating Trend is_uptrend at shift=%d", shift, extra={"shift": shift}
        )
        return is_greater(price, baseline, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def is_downtrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly below the baseline (Downtrend).

        Formula:
            price[shift] < baseline[shift]
        """
        logger.info(
            "Evaluating Trend is_downtrend at shift=%d", shift, extra={"shift": shift}
        )
        return is_lower(price, baseline, shift1=shift, shift2=shift, round_digits=8)

    @staticmethod
    def turns_uptrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed from below or equal baseline to above baseline."""
        logger.info(
            "Evaluating Trend turns_uptrend at shift=%d", shift, extra={"shift": shift}
        )
        return crosses_above(price, baseline, shift=shift, round_digits=8)

    @staticmethod
    def turns_downtrend(
        price: IndicatorSeries | np.ndarray[Any, Any],
        baseline: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed from above or equal baseline to below baseline."""
        logger.info(
            "Evaluating Trend turns_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return crosses_below(price, baseline, shift=shift, round_digits=8)
