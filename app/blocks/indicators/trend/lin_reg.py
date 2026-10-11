"""Linear Regression Indicator Block.

Description:
    Computes ordinary least squares linear regression end-value, slope, and
    intercept over a sliding lookback window. Provides condition evaluators
    for bar penetration, breakout open crossovers, and trend slope persistence.

Purpose:
    FEAT-BLOCKS-INDICATOR-LINREG

Key Capabilities:
    - FR-BLOCKS-LINREG-CALCULATE: Computes LinReg fitted value, slope, and intercept.
    - FR-BLOCKS-LINREG-CONDITIONS: Evaluates price penetration and directional slope.

Python API Usage:
    ```python
    from app.blocks.indicators.lin_reg import LinReg

    lr = LinReg.calculate(close, period=14)
    line = lr["lin_reg"]
    slope = lr["slope"]

    # Condition checks
    closes_above = LinReg.bar_closes_above(close, line, shift=0)
    is_rising = LinReg.is_rising(line, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

MIN_LINREG_PERIOD: int = 2


class LinReg(BaseIndicator):
    """Linear Regression indicator calculating least-squares regression lines."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute Linear Regression endpoint value, slope, and intercept.

        Formula:
            y_end = mean(y) + slope * ((period - 1) / 2.0)
            slope = sum((t - mean(t)) * (y - mean(y))) / sum((t - mean(t))^2)

        Args:
            price: Input price series (typically Close).
            period: Lookback window length in bars (must be >= 2).

        Returns:
            Dictionary containing:
                - 'lin_reg': Linear regression endpoint series.
                - 'slope': Slope per bar of the regression line.
                - 'intercept': Regression line intercept.

        Raises:
            ValueError: If period < 2 or price series is empty.
        """
        logger.info(
            "LinReg calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        if period < MIN_LINREG_PERIOD:
            raise ValueError(f"Period must be >= 2, got {period}")

        p_arr = cls.to_numpy(price)
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
            intercept = y_mean - (slope * t_mean)
            end_val = intercept + (slope * (period - 1.0))

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
        c = BaseIndicator.to_numpy(close_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        idx = len(c) - 1 - shift
        if idx < 0 or idx >= len(c) or idx >= len(lr) or np.isnan(lr[idx]):
            return False
        return bool(c[idx] > lr[idx])

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
        c = BaseIndicator.to_numpy(close_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        idx = len(c) - 1 - shift
        if idx < 0 or idx >= len(c) or idx >= len(lr) or np.isnan(lr[idx]):
            return False
        return bool(c[idx] < lr[idx])

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
        o = BaseIndicator.to_numpy(open_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        idx = len(o) - 1 - shift
        if idx < 0 or idx >= len(o) or idx >= len(lr) or np.isnan(lr[idx]):
            return False
        return bool(o[idx] > lr[idx])

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
        o = BaseIndicator.to_numpy(open_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        idx = len(o) - 1 - shift
        if idx < 0 or idx >= len(o) or idx >= len(lr) or np.isnan(lr[idx]):
            return False
        return bool(o[idx] < lr[idx])

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
        o = BaseIndicator.to_numpy(open_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        curr = len(o) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(o) or prev >= len(lr) or np.isnan(lr[prev]):
            return False
        return bool(o[prev] < lr[prev] and o[curr] > lr[prev])

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
        o = BaseIndicator.to_numpy(open_prices)
        lr = BaseIndicator.to_numpy(lin_reg)
        curr = len(o) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(o) or prev >= len(lr) or np.isnan(lr[prev]):
            return False
        return bool(o[prev] > lr[prev] and o[curr] < lr[prev])

    @staticmethod
    def is_rising(
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Linear Regression line is rising."""
        logger.info(
            "Evaluating LinReg is_rising at shift=%d",
            shift,
            extra={"shift": shift},
        )
        lr = BaseIndicator.to_numpy(lin_reg)
        curr = len(lr) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(lr) or np.isnan(lr[curr]) or np.isnan(lr[prev]):
            return False
        return bool(lr[curr] > lr[prev])

    @staticmethod
    def is_falling(
        lin_reg: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Linear Regression line is falling."""
        logger.info(
            "Evaluating LinReg is_falling at shift=%d",
            shift,
            extra={"shift": shift},
        )
        lr = BaseIndicator.to_numpy(lin_reg)
        curr = len(lr) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(lr) or np.isnan(lr[curr]) or np.isnan(lr[prev]):
            return False
        return bool(lr[curr] < lr[prev])
