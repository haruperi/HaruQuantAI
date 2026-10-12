"""Bill Williams Fractal Indicator Block.

Description:
    Identifies multi-bar bullish (trough/support) and bearish (peak/resistance)
    fractal reversal patterns. Implements standard 3-bar and 5-bar middle-extremum
    recognition algorithms with condition evaluators.

Purpose:
    FEAT-SERVICES-INDICATOR-FRACTAL

Key Capabilities:
    - FR-SERVICES-FRACTAL-CALCULATE: Computes confirmed up/down fractal levels.
    - FR-SERVICES-FRACTAL-CONDITIONS: Evaluates bullish/bearish reversal signals.

Python API Usage:
    ```python
    from app.services.indicators.fractal import Fractal

    fractals = Fractal.calculate(high, low, fractal_bars=5)
    up_fractals = fractals["up"]
    down_fractals = fractals["down"]

    # Condition checks
    is_bull = Fractal.is_bullish_fractal(fractals, shift=0)
    is_bear = Fractal.is_bearish_fractal(fractals, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_FRACTAL_BARS: int = 3


class Fractal(BaseIndicator):
    """Bill Williams Fractal indicator detecting local peak and trough formations."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        fractal_bars: int = 5,
    ) -> dict[str, IndicatorSeries]:
        """Compute up and down fractal reversal levels.

        Args:
            high: High price series.
            low: Low price series.
            fractal_bars: Number of bars in pattern (must be odd >= 3).

        Returns:
            Dictionary containing:
                - 'up': Price of confirmed up fractal (peak), or 0.0 if none.
                - 'down': Price of confirmed down fractal (trough), or 0.0 if none.

        Raises:
            ValueError: If fractal_bars < 3, is even, or input arrays mismatch.
        """
        logger.info(
            "Fractal calculation initiated with fractal_bars=%d",
            fractal_bars,
            extra={"fractal_bars": fractal_bars},
        )
        if fractal_bars < MIN_FRACTAL_BARS or fractal_bars % 2 == 0:
            raise ValueError(
                f"fractal_bars must be an odd integer >= 3, got {fractal_bars}"
            )

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)

        if len(h_arr) == 0:
            raise ValueError("Input series cannot be empty")
        if len(h_arr) != len(l_arr):
            raise ValueError(
                f"High and low series length mismatch: {len(h_arr)} vs {len(l_arr)}"
            )

        n = len(h_arr)
        up_vals = np.zeros(n, dtype=np.float64)
        down_vals = np.zeros(n, dtype=np.float64)
        each_side = (fractal_bars - 1) // 2

        for i in range(fractal_bars - 1, n):
            up_p, down_p = cls._check_fractal_at_bar(
                h_arr, l_arr, i, each_side, fractal_bars
            )
            up_vals[i] = up_p
            down_vals[i] = down_p

        logger.info(
            "Fractal calculation complete: bars=%d, fractal_bars=%d",
            n,
            fractal_bars,
            extra={"bars": n, "fractal_bars": fractal_bars},
        )

        return {
            "up": IndicatorSeries(up_vals, name=f"FractalUp({fractal_bars})"),
            "down": IndicatorSeries(down_vals, name=f"FractalDown({fractal_bars})"),
        }

    @staticmethod
    def _check_fractal_at_bar(
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        curr_i: int,
        each_side: int,
        fractal_bars: int,
    ) -> tuple[float, float]:
        """Check if middle bar in window forms an up or down fractal."""
        middle_idx = curr_i - each_side
        middle_high = h_arr[middle_idx]
        middle_low = l_arr[middle_idx]

        is_up = True
        is_down = True

        for offset in range(fractal_bars):
            check_idx = curr_i - offset
            if check_idx == middle_idx:
                continue
            if h_arr[check_idx] >= middle_high:
                is_up = False
            if l_arr[check_idx] <= middle_low:
                is_down = False

        up_val = middle_high if is_up else 0.0
        down_val = middle_low if is_down else 0.0
        return up_val, down_val

    @staticmethod
    def is_bullish_fractal(
        fractals: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if a bullish fractal formed at shift.

        Formula:
            fractals['down'][shift] > 0
        """
        logger.info(
            "Evaluating is_bullish_fractal at shift=%d",
            shift,
            extra={"shift": shift},
        )
        down_series = fractals["down"]
        val = down_series.get(shift)
        return bool(not np.isnan(val) and val > 0.0)

    @staticmethod
    def is_bearish_fractal(
        fractals: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if a bearish fractal formed at shift.

        Formula:
            fractals['up'][shift] > 0
        """
        logger.info(
            "Evaluating is_bearish_fractal at shift=%d",
            shift,
            extra={"shift": shift},
        )
        up_series = fractals["up"]
        val = up_series.get(shift)
        return bool(not np.isnan(val) and val > 0.0)
