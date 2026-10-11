"""Price Velocity and Acceleration Momentum Indicator Block.

Description:
    Computes price velocity measuring the first derivative rate of price
    travel per bar over a lookback window, alongside percentage normalized
    velocity. Captures rapid speed changes and momentum acceleration.

Purpose:
    FEAT-BLOCKS-INDICATOR-PRICE-VELOCITY

Key Capabilities:
    - FR-BLOCKS-PRICEVELOCITY-CALCULATE: Computes raw and normalized price velocity.
      Associated: `PriceVelocity.calculate()`
      Logging: INFO level logging of period, smoothing, and bar count.
    - FR-BLOCKS-PRICEVELOCITY-CONDITIONS: Evaluates acceleration and zero crosses.
      Associated: `PriceVelocity.is_accelerating_up()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.blocks.indicators.momentum.price_velocity import PriceVelocity

    res = PriceVelocity.calculate(close, period=10, smooth_period=3)
    vel = res["velocity"]
    norm = res["normalized"]
    is_speeding_up = PriceVelocity.is_accelerating_up(vel, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

MIN_VELOCITY_PERIOD: int = 1
DEFAULT_VELOCITY_PERIOD: int = 10
DEFAULT_SMOOTH_PERIOD: int = 1
PERCENT_MULTIPLIER: float = 100.0
EPSILON: float = 1e-12


class PriceVelocity(BaseIndicator):
    """Price velocity and momentum acceleration indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_VELOCITY_PERIOD,
        smooth_period: int = DEFAULT_SMOOTH_PERIOD,
    ) -> dict[str, IndicatorSeries]:
        """Compute raw and normalized price velocity per bar.

        Args:
            price: Input price series (e.g. Close).
            period: Lookback displacement window (>= 1).
            smooth_period: Smoothing SMA period (>= 1).

        Returns:
            Dictionary containing:
                - 'velocity': Raw price change per bar.
                - 'normalized': Percentage price change per bar.
        """
        logger.info(
            "PriceVelocity initiated: period=%d, smooth=%d",
            period,
            smooth_period,
        )
        if period < MIN_VELOCITY_PERIOD:
            raise ValueError(f"period must be >= {MIN_VELOCITY_PERIOD}, got {period}")
        if smooth_period < 1:
            raise ValueError(f"smooth_period must be >= 1, got {smooth_period}")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Price array cannot be empty")

        vel, norm = cls._compute_velocity(p_arr, period, smooth_period, n)
        logger.info("PriceVelocity completed: bars=%d", n)
        return {
            "velocity": IndicatorSeries(vel, name=f"PriceVelocity({period})"),
            "normalized": IndicatorSeries(norm, name=f"PriceVelocityNorm({period})"),
        }

    @classmethod
    def _compute_velocity(
        cls,
        p_arr: np.ndarray[Any, Any],
        period: int,
        smooth_period: int,
        n: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        raw_vel = np.zeros(n, dtype=np.float64)
        raw_norm = np.zeros(n, dtype=np.float64)

        for i in range(n):
            past_idx = max(0, i - period)
            span = i - past_idx
            if span > 0:
                past_val = p_arr[past_idx]
                diff = p_arr[i] - past_val
                raw_vel[i] = diff / float(span)
                if abs(past_val) > EPSILON:
                    raw_norm[i] = ((diff / past_val) / float(span)) * PERCENT_MULTIPLIER
                else:
                    raw_norm[i] = 0.0

        if smooth_period > 1:
            vel = cls._smooth_series(raw_vel, smooth_period, n)
            norm = cls._smooth_series(raw_norm, smooth_period, n)
        else:
            vel = raw_vel
            norm = raw_norm

        return vel, norm

    @staticmethod
    def _smooth_series(
        data: np.ndarray[Any, Any], smooth_period: int, n: int
    ) -> np.ndarray[Any, Any]:
        smoothed = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - smooth_period + 1)
            window_len = i - start + 1
            smoothed[i] = float(np.sum(data[start : i + 1])) / window_len
        return smoothed

    @classmethod
    def is_accelerating_up(
        cls,
        velocity: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if velocity is positive and rising (upward acceleration)."""
        logger.info("Evaluating PriceVelocity is_accelerating_up at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > 0.0 and curr > prev

    @classmethod
    def is_accelerating_down(
        cls,
        velocity: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if velocity is negative and falling (downward acceleration)."""
        logger.info("Evaluating PriceVelocity is_accelerating_down at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < 0.0 and curr < prev

    @classmethod
    def crosses_above_zero(
        cls,
        velocity: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if velocity crosses above zero at shift."""
        logger.info("Evaluating PriceVelocity crosses_above_zero at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= 0.0 and curr > 0.0)

    @classmethod
    def crosses_below_zero(
        cls,
        velocity: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """True if velocity crosses below zero at shift."""
        logger.info("Evaluating PriceVelocity crosses_below_zero at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= 0.0 and curr < 0.0)

    @classmethod
    def is_rising(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is rising between shift+1 and shift."""
        logger.info("Evaluating PriceVelocity is_rising at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, velocity: IndicatorSeries, shift: int = 0) -> bool:
        """True if velocity is falling between shift+1 and shift."""
        logger.info("Evaluating PriceVelocity is_falling at shift=%d", shift)
        curr = velocity.get(shift)
        prev = velocity.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
