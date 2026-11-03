"""LinReg indicator.

- Calculates Linear Regression slope, intercept, and rolling trend projection.
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
from app.extend.blocks.comparisons import is_falling, is_lower, is_rising
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_LINREG_PERIOD: int = 2


class LinReg(BaseIndicator):
    """Linear Regression indicator calculating least-squares regression lines."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.lin_reg",
        version="1.0.0",
        name="LinReg",
        description=(
            "Calculates Linear Regression slope, intercept, and rolling trend"
            " projection."
        ),
        category="trend",
        tags=("trend", "lin-reg"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("lin_reg", PortType.SERIES, description="Lin reg output series"),
            OutputPort("slope", PortType.SERIES, description="Slope output series"),
            OutputPort(
                "intercept", PortType.SERIES, description="Intercept output series"
            ),
        ),
        required_market_inputs=("close",),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=MIN_LINREG_PERIOD,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_LINREG_PERIOD:
            raise ValueError(f"Period must be >= 2, got {self.period}")
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
        logger.debug("FR-indicator-calculation: LinReg requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
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

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["LinReg"]
