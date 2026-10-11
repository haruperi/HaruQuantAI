"""Price Gap Recognition and Tracking Indicator Block.

Description:
    Tracks price gaps (full gap vs. body gap) between consecutive bars:
    - Full Gap: Low > Previous High (Gap Up) or High < Previous Low (Gap Down).
    - Body Gap: Open > Previous High (Gap Up) or Open < Previous Low (Gap Down).
    - Gap Fill Status: Evaluates whether the bar's extreme range reached into
      or completely closed the previous bar's boundary.

Purpose:
    FEAT-BLOCKS-INDICATOR-PRICE-GAP

Key Capabilities:
    - FR-BLOCKS-PRICE-GAP-CALCULATE: Computes signed price gap size and intraday
      gap fill verification.
    - FR-BLOCKS-PRICE-GAP-CONDITIONS: Evaluates gap direction, magnitude, and
      fill predicates.

Python API Usage:
    ```python
    from app.blocks.indicators.price_action.price_gap import PriceGap

    gaps = PriceGap.calculate(open_p, high, low, close, full_gap=True)
    gap_size = gaps["gap_size"]
    gap_filled = gaps["gap_filled"]

    # Condition checks
    is_up = PriceGap.is_gap_up(gap_size, min_size=1.0, shift=0)
    is_down = PriceGap.is_gap_down(gap_size, min_size=1.0, shift=0)
    filled = PriceGap.is_gap_filled(gap_filled, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

DEFAULT_GAP_THRESHOLD: float = 0.5
EPSILON: float = 1e-12


class PriceGap(BaseIndicator):
    """Price Gap detection and fill tracking block."""

    @classmethod
    @override
    def calculate(
        cls,
        open: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        high: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        low: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        close: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        full_gap: bool = True,
    ) -> dict[str, IndicatorSeries]:
        """Compute price gap magnitude and intraday fill status.

        Args:
            open: Open price series.
            high: High price series.
            low: Low price series.
            close: Close price series.
            full_gap: If True, evaluates extreme full gaps; if False, body gaps.

        Returns:
            Dictionary containing 'gap_size' and 'gap_filled' IndicatorSeries.
        """
        logger.info("PriceGap.calculate called: full_gap=%s", full_gap)
        o_arr = cls.to_numpy(open)
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        gap_size, gap_filled = cls._compute_gaps((o_arr, h_arr, l_arr, c_arr), full_gap)
        logger.info("PriceGap completed: bars=%d", n)
        mode_label = "Full" if full_gap else "Body"
        return {
            "gap_size": IndicatorSeries(gap_size, name=f"PriceGapSize({mode_label})"),
            "gap_filled": IndicatorSeries(
                gap_filled, name=f"PriceGapFilled({mode_label})"
            ),
        }

    @classmethod
    def _compute_gaps(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        full_gap: bool,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        gap_size = np.zeros(n, dtype=np.float64)
        gap_filled = np.zeros(n, dtype=np.float64)

        for i in range(1, n):
            prev_h = h_arr[i - 1]
            prev_l = l_arr[i - 1]

            if full_gap:
                if l_arr[i] > prev_h:
                    gap_size[i] = l_arr[i] - prev_h
                elif h_arr[i] < prev_l:
                    gap_size[i] = h_arr[i] - prev_l
            elif o_arr[i] > prev_h:
                gap_size[i] = o_arr[i] - prev_h
                if l_arr[i] <= prev_h:
                    gap_filled[i] = 1.0
            elif o_arr[i] < prev_l:
                gap_size[i] = o_arr[i] - prev_l
                if h_arr[i] >= prev_l:
                    gap_filled[i] = 1.0

        return gap_size, gap_filled

    @classmethod
    def is_gap_up(
        cls,
        gap_series: IndicatorSeries,
        min_size: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """True if positive price gap exceeds minimum size at shift."""
        logger.info(
            "Evaluating PriceGap.is_gap_up: min_size=%.2f, shift=%d",
            min_size,
            shift,
        )
        val = gap_series.get(shift)
        return not np.isnan(val) and val > min_size

    @classmethod
    def is_gap_down(
        cls,
        gap_series: IndicatorSeries,
        min_size: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """True if negative price gap exceeds minimum magnitude at shift."""
        logger.info(
            "Evaluating PriceGap.is_gap_down: min_size=%.2f, shift=%d",
            min_size,
            shift,
        )
        val = gap_series.get(shift)
        return not np.isnan(val) and val < -min_size

    @classmethod
    def is_gap_filled(cls, gap_filled_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if price gap was filled within the bar at shift."""
        logger.info(
            "Evaluating PriceGap.is_gap_filled: shift=%d",
            shift,
        )
        val = gap_filled_series.get(shift)
        return not np.isnan(val) and val > DEFAULT_GAP_THRESHOLD
