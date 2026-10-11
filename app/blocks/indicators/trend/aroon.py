"""Aroon indicator family implementation.

Description:
    Computes Tushar Chande's Aroon indicator system measuring the time elapsed
    between price highs and lows over a specified lookback period:
    Aroon Up = ((Period - Bars Since Highest High) / Period) * 100
    Aroon Down = ((Period - Bars Since Lowest Low) / Period) * 100
    Aroon Oscillator = Aroon Up - Aroon Down.
    Provides condition helpers for crossovers, top departures, and bottom rises.

Purpose:
    FEAT-BLOCKS-INDICATOR-AROON: Aroon trend strength and timing indicator.

Key Capabilities:
    - FR-BLOCKS-AROON-CALCULATE: Vectorized calculation of Up, Down, and Oscillator.
      Associated: `Aroon.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-AROON-CONDITIONS: Crossover and threshold condition evaluation.
      Associated: `Aroon.crosses_above()`, `Aroon.up_rises_from_bottom()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.aroon import Aroon

    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 12.5])
    low = np.array([9.0, 9.5, 10.0, 10.2, 11.0, 11.2])

    res = Aroon.calculate(high, low, period=5)
    up = res["up"].get(0)
    down = res["down"].get(0)
    osc = res["oscillator"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.aroon
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)


class Aroon(BaseIndicator):
    """Aroon indicator family."""

    name: str = "Aroon"
    category: str = "Trend"

    BOTTOM_LEVEL: float = 8.0
    TOP_LEVEL: float = 99.9
    MID_LOW_LEVEL: float = 30.0
    MID_HIGH_LEVEL: float = 70.0

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute Aroon Up, Down, and Oscillator series.

        Args:
            high: High prices array.
            low: Low prices array.
            period: Lookback window period (default 14).

        Returns:
            Dictionary with 'up', 'down', and 'oscillator' IndicatorSeries.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)

        if n != len(low_arr):
            raise ValueError("High and Low arrays must have equal length.")

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-AROON-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        up = np.zeros(n, dtype=np.float64)
        down = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start_idx = max(0, i - period)
            window_h = high_arr[start_idx : i + 1]
            window_l = low_arr[start_idx : i + 1]

            # Highest high bars ago (0 = current bar)
            hh_idx = len(window_h) - 1 - int(np.argmax(window_h))
            # Lowest low bars ago (0 = current bar)
            ll_idx = len(window_l) - 1 - int(np.argmin(window_l))

            up[i] = 100.0 - (100.0 / float(period)) * float(hh_idx)
            down[i] = 100.0 - (100.0 / float(period)) * float(ll_idx)

        oscillator = up - down

        logger.info(
            "FR-BLOCKS-AROON-CALCULATE: Computed Aroon(period=%d) for %d bars",
            period,
            n,
        )
        return {
            "up": IndicatorSeries(up, name=f"Aroon.Up({period})"),
            "down": IndicatorSeries(down, name=f"Aroon.Down({period})"),
            "oscillator": IndicatorSeries(
                oscillator, name=f"Aroon.Oscillator({period})"
            ),
        }

    # Condition helpers
    @classmethod
    def crosses_above(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if Aroon Up crosses above Aroon Down."""
        return aroon_dict["up"].crosses_above(aroon_dict["down"], shift)

    @classmethod
    def crosses_below(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if Aroon Up crosses below Aroon Down."""
        return aroon_dict["up"].crosses_below(aroon_dict["down"], shift)

    @classmethod
    def up_rises_from_bottom(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Up rises from bottom condition."""
        up0 = aroon_dict["up"].get(shift)
        up1 = aroon_dict["up"].get(shift + 1)
        down0 = aroon_dict["down"].get(shift)
        res = bool(
            up1 <= cls.BOTTOM_LEVEL
            and up0 > cls.BOTTOM_LEVEL
            and down0 > cls.MID_LOW_LEVEL
        )
        logger.debug(
            "FR-BLOCKS-AROON-CONDITIONS up_rises_from_bottom up1=%.2f up0=%.2f "
            "down0=%.2f res=%s",
            up1,
            up0,
            down0,
            res,
        )
        return res

    @classmethod
    def down_falls_from_top(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Down falls from top condition."""
        down0 = aroon_dict["down"].get(shift)
        down1 = aroon_dict["down"].get(shift + 1)
        up0 = aroon_dict["up"].get(shift)
        res = bool(
            down1 >= cls.TOP_LEVEL
            and down0 < cls.TOP_LEVEL
            and up0 < cls.MID_HIGH_LEVEL
        )
        logger.debug(
            "FR-BLOCKS-AROON-CONDITIONS down_falls_from_top down1=%.2f down0=%.2f "
            "up0=%.2f res=%s",
            down1,
            down0,
            up0,
            res,
        )
        return res

    @classmethod
    def down_rises_from_bottom(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Down rises from bottom condition."""
        down0 = aroon_dict["down"].get(shift)
        down1 = aroon_dict["down"].get(shift + 1)
        up0 = aroon_dict["up"].get(shift)
        res = bool(
            down1 <= cls.BOTTOM_LEVEL
            and down0 > cls.BOTTOM_LEVEL
            and up0 > cls.MID_LOW_LEVEL
        )
        logger.debug(
            "FR-BLOCKS-AROON-CONDITIONS down_rises_from_bottom down1=%.2f down0=%.2f "
            "up0=%.2f res=%s",
            down1,
            down0,
            up0,
            res,
        )
        return res

    @classmethod
    def up_falls_from_top(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Up falls from top condition."""
        up0 = aroon_dict["up"].get(shift)
        up1 = aroon_dict["up"].get(shift + 1)
        down0 = aroon_dict["down"].get(shift)
        res = bool(
            up1 >= cls.TOP_LEVEL and up0 < cls.TOP_LEVEL and down0 < cls.MID_HIGH_LEVEL
        )
        logger.debug(
            "FR-BLOCKS-AROON-CONDITIONS up_falls_from_top up1=%.2f up0=%.2f "
            "down0=%.2f res=%s",
            up1,
            up0,
            down0,
            res,
        )
        return res

    @classmethod
    def up_is_rising(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Aroon Up is rising."""
        return aroon_dict["up"].is_rising(shift)

    @classmethod
    def up_is_falling(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Aroon Up is falling."""
        return aroon_dict["up"].is_falling(shift)

    @classmethod
    def down_is_rising(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Aroon Down is rising."""
        return aroon_dict["down"].is_rising(shift)

    @classmethod
    def down_is_falling(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Aroon Down is falling."""
        return aroon_dict["down"].is_falling(shift)
