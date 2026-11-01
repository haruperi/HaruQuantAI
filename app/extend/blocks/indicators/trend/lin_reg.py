"""LinReg indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-LINREG: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import is_falling, is_lower, is_rising
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
MIN_LINREG_PERIOD: int = 2


class LinReg(BaseIndicator):
    """Linear Regression indicator calculating least-squares regression lines."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.lin_reg",
        name="LinReg",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("lin_reg", PortType.SERIES),
            OutputPort("slope", PortType.SERIES),
            OutputPort("intercept", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=MIN_LINREG_PERIOD)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_LINREG_PERIOD:
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
        price = bars.close
        period = self.period
        logger.info(
            "LinReg calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        lin_reg_vals = np.full(n, np.nan, dtype=np.float64)
        slope_vals = np.full(n, np.nan, dtype=np.float64)
        intercept_vals = np.full(n, np.nan, dtype=np.float64)
        t = np.arange(period, dtype=np.float64)
        t_mean = (period - 1.0) / 2.0
        t_diff = t - t_mean
        denom = float(np.sum(t_diff**2))
        for i in range(period - 1, n):
            y_win = p_arr[i - period + 1 : i + 1]
            y_mean = float(np.mean(y_win))
            slope = float(np.sum(t_diff * (y_win - y_mean))) / denom
            intercept = y_mean - slope * t_mean
            end_val = intercept + slope * (period - 1.0)
            lin_reg_vals[i] = end_val
            slope_vals[i] = slope
            intercept_vals[i] = intercept
        logger.info(
            "LinReg calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return {
            "lin_reg": IndicatorSeries(lin_reg_vals, name=f"LinReg({period})"),
            "slope": IndicatorSeries(slope_vals, name=f"LinRegSlope({period})"),
            "intercept": IndicatorSeries(
                intercept_vals, name=f"LinRegIntercept({period})"
            ),
        }

    @staticmethod
    def bar_closes_above(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is strictly above the Linear Regression line."""
        logger.info(
            "Evaluating LinReg bar_closes_above at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(close_prices, lin_reg, shift=shift)

    @staticmethod
    def bar_closes_below(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is strictly below the Linear Regression line."""
        logger.info(
            "Evaluating LinReg bar_closes_below at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(close_prices, lin_reg, shift=shift)

    @staticmethod
    def bar_opens_above(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Open is strictly above the Linear Regression line."""
        logger.info(
            "Evaluating LinReg bar_opens_above at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(open_prices, lin_reg, shift=shift)

    @staticmethod
    def bar_opens_below(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Open is strictly below the Linear Regression line."""
        logger.info(
            "Evaluating LinReg bar_opens_below at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(open_prices, lin_reg, shift=shift)

    @staticmethod
    def bar_opens_above_after_open_below(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened above LinReg after previous bar opened below."""
        logger.info(
            "Evaluating LinReg bar_opens_above_after_open_below at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_lower(
            open_prices, lin_reg, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_greater(
            open_prices, lin_reg, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def bar_opens_below_after_open_above(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened below LinReg after previous bar opened above."""
        logger.info(
            "Evaluating LinReg bar_opens_below_after_open_above at shift=%d",
            shift,
            extra={"shift": shift},
        )
        return is_greater(
            open_prices, lin_reg, shift1=shift + 1, shift2=shift + 1, round_digits=8
        ) and is_lower(
            open_prices, lin_reg, shift1=shift, shift2=shift + 1, round_digits=8
        )

    @staticmethod
    def is_rising(
        lin_reg: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Linear Regression line is rising."""
        logger.info(
            "Evaluating LinReg is_rising at shift=%d", shift, extra={"shift": shift}
        )
        return is_rising(lin_reg, shift=shift)

    @staticmethod
    def is_falling(
        lin_reg: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Linear Regression line is falling."""
        logger.info(
            "Evaluating LinReg is_falling at shift=%d", shift, extra={"shift": shift}
        )
        return is_falling(lin_reg, shift=shift)
