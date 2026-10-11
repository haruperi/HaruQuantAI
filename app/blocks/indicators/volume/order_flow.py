"""Order Flow Indicators: Cumulative Volume Delta and Aggressive Trade Imbalance.

Description:
    Provides order flow analysis blocks for market microstructure evaluation.
    CumulativeVolumeDelta (CVD) tracks net buyer versus seller aggressive volume
    both as a cumulative running total and as a rolling lookback window delta.
    AggressiveTradeImbalance (ATI) calculates the normalized ratio of aggressive
    buying volume to aggressive selling volume over a rolling window in [-1.0, 1.0].
    When tick-level taker volumes are not available, bar-level signed volume
    approximations based on bar close relative to open are used.

Purpose:
    FEAT-BLOCKS-INDICATOR-CVD, FEAT-BLOCKS-INDICATOR-ATI

Key Capabilities:
    - FR-BLOCKS-CVD-CALCULATE: Computes cumulative volume delta and rolling delta.
      Associated: `CumulativeVolumeDelta.calculate()`
      Logging: INFO level logging of input sizes, window parameter, and completion.
    - FR-BLOCKS-CVD-CONDITIONS: Evaluates positive, negative, rising, and zero-crossing.
      Associated: `CumulativeVolumeDelta.is_positive()`, `is_rising()`, etc.
      Logging: INFO level logging of evaluation parameters and result.
    - FR-BLOCKS-ATI-CALCULATE: Computes rolling aggressive trade imbalance ratio.
      Associated: `AggressiveTradeImbalance.calculate()`
      Logging: INFO level logging of input sizes, window parameter, and completion.
    - FR-BLOCKS-ATI-CONDITIONS: Evaluates buyer/seller dominance and crosses.
      Associated: `AggressiveTradeImbalance.is_buyer_dominated()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.blocks.indicators.volume.order_flow import (
        AggressiveTradeImbalance,
        CumulativeVolumeDelta,
    )

    res = CumulativeVolumeDelta.calculate(open_arr, close_arr, volume_arr, window=14)
    cvd = res["cvd"]
    delta = res["delta"]
    is_bull = CumulativeVolumeDelta.is_positive(cvd, shift=0)

    ati = AggressiveTradeImbalance.calculate(open_arr, close_arr, volume_arr, window=14)
    buyer_dom = AggressiveTradeImbalance.is_buyer_dominated(ati, threshold=0.2, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

MIN_CVD_WINDOW: int = 1
DEFAULT_CVD_WINDOW: int = 14
MIN_ATI_WINDOW: int = 1
DEFAULT_ATI_WINDOW: int = 14
DEFAULT_BUYER_THRESHOLD: float = 0.2
DEFAULT_SELLER_THRESHOLD: float = -0.2
EPSILON: float = 1e-12


class CumulativeVolumeDelta(BaseIndicator):
    """Cumulative Volume Delta (CVD) tracking net aggressive buying/selling volume."""

    @classmethod
    @override
    def calculate(
        cls,
        open: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        window: int = DEFAULT_CVD_WINDOW,
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None = None,
    ) -> dict[str, IndicatorSeries]:
        """Compute Cumulative Volume Delta and rolling window delta.

        Args:
            open: Open price series.
            close: Close price series.
            volume: Total volume series.
            window: Rolling window size for delta calculation (>= 1).
            buy_volume: Optional explicit aggressive buyer volume series.
            sell_volume: Optional explicit aggressive seller volume series.

        Returns:
            Dictionary containing:
                - 'cvd': IndicatorSeries with cumulative running volume delta.
                - 'delta': IndicatorSeries with rolling window volume delta.
        """
        logger.info("CumulativeVolumeDelta calculation initiated: window=%d", window)
        if window < MIN_CVD_WINDOW:
            raise ValueError(f"window must be >= {MIN_CVD_WINDOW}, got {window}")

        o_arr = cls.to_numpy(open)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)

        if n == 0 or len(o_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        bar_deltas = cls._extract_bar_deltas(
            o_arr, c_arr, v_arr, buy_volume, sell_volume
        )

        cvd_vals = np.cumsum(bar_deltas)
        rolling_delta = cls._compute_rolling_delta(bar_deltas, window, n)

        logger.info("CumulativeVolumeDelta calculation completed: bars=%d", n)
        return {
            "cvd": IndicatorSeries(cvd_vals, name="CVD"),
            "delta": IndicatorSeries(rolling_delta, name=f"CVD_Delta({window})"),
        }

    @classmethod
    def _extract_bar_deltas(
        cls,
        o_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> np.ndarray[Any, Any]:
        """Extract bar delta values from taker volumes or price direction."""
        n = len(c_arr)
        if buy_volume is not None and sell_volume is not None:
            b_arr = cls.to_numpy(buy_volume)
            s_arr = cls.to_numpy(sell_volume)
            if len(b_arr) != n or len(s_arr) != n:
                raise ValueError("buy_volume and sell_volume lengths must match price")
            diff: np.ndarray[Any, Any] = np.asarray(b_arr - s_arr, dtype=np.float64)
            return diff

        sign = np.where(c_arr >= o_arr, 1.0, -1.0)
        res: np.ndarray[Any, Any] = np.asarray(sign * v_arr, dtype=np.float64)
        return res

    @classmethod
    def _compute_rolling_delta(
        cls, bar_deltas: np.ndarray[Any, Any], window: int, n: int
    ) -> np.ndarray[Any, Any]:
        """Compute rolling window delta over specified lookback."""
        rolling = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - window + 1)
            rolling[i] = float(np.sum(bar_deltas[start : i + 1]))
        return rolling

    @classmethod
    def is_positive(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD value is positive at shift."""
        logger.info("Evaluating CVD is_positive at shift=%d", shift)
        val = cvd.get(shift)
        return not np.isnan(val) and val > 0.0

    @classmethod
    def is_negative(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD value is negative at shift."""
        logger.info("Evaluating CVD is_negative at shift=%d", shift)
        val = cvd.get(shift)
        return not np.isnan(val) and val < 0.0

    @classmethod
    def crosses_above_zero(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD crosses above zero at shift."""
        logger.info("Evaluating CVD crosses_above_zero at shift=%d", shift)
        curr = cvd.get(shift)
        prev = cvd.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= 0.0 and curr > 0.0)

    @classmethod
    def crosses_below_zero(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD crosses below zero at shift."""
        logger.info("Evaluating CVD crosses_below_zero at shift=%d", shift)
        curr = cvd.get(shift)
        prev = cvd.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= 0.0 and curr < 0.0)

    @classmethod
    def is_rising(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating CVD is_rising at shift=%d", shift)
        curr = cvd.get(shift)
        prev = cvd.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating CVD is_falling at shift=%d", shift)
        curr = cvd.get(shift)
        prev = cvd.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev


class AggressiveTradeImbalance(BaseIndicator):
    """Aggressive Trade Imbalance (ATI) normalized ratio in [-1.0, 1.0]."""

    @classmethod
    @override
    def calculate(
        cls,
        open: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        window: int = DEFAULT_ATI_WINDOW,
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None = None,
    ) -> IndicatorSeries:
        """Compute rolling Aggressive Trade Imbalance ratio.

        Args:
            open: Open price series.
            close: Close price series.
            volume: Total volume series.
            window: Rolling window size (>= 1).
            buy_volume: Optional explicit aggressive buyer volume series.
            sell_volume: Optional explicit aggressive seller volume series.

        Returns:
            IndicatorSeries with ATI values bounded in [-1.0, 1.0].
        """
        logger.info("AggressiveTradeImbalance calculation initiated: window=%d", window)
        if window < MIN_ATI_WINDOW:
            raise ValueError(f"window must be >= {MIN_ATI_WINDOW}, got {window}")

        o_arr = cls.to_numpy(open)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)

        if n == 0 or len(o_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        b_vol, s_vol = cls._extract_volume_components(
            o_arr, c_arr, v_arr, buy_volume, sell_volume
        )

        ati_vals = cls._compute_ati(b_vol, s_vol, window, n)
        logger.info("AggressiveTradeImbalance calculation completed: bars=%d", n)
        return IndicatorSeries(ati_vals, name=f"ATI({window})")

    @classmethod
    def _extract_volume_components(
        cls,
        o_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Extract separate buyer and seller volume components."""
        n = len(c_arr)
        if buy_volume is not None and sell_volume is not None:
            b_arr = cls.to_numpy(buy_volume)
            s_arr = cls.to_numpy(sell_volume)
            if len(b_arr) != n or len(s_arr) != n:
                raise ValueError("buy_volume and sell_volume lengths must match price")
            return b_arr, s_arr

        b_arr = np.where(c_arr >= o_arr, v_arr, 0.0)
        s_arr = np.where(c_arr < o_arr, v_arr, 0.0)
        return b_arr, s_arr

    @classmethod
    def _compute_ati(
        cls,
        b_vol: np.ndarray[Any, Any],
        s_vol: np.ndarray[Any, Any],
        window: int,
        n: int,
    ) -> np.ndarray[Any, Any]:
        """Compute rolling imbalance ratio clamped in [-1.0, 1.0]."""
        ati = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - window + 1)
            sum_b = float(np.sum(b_vol[start : i + 1]))
            sum_s = float(np.sum(s_vol[start : i + 1]))
            total = sum_b + sum_s
            if total > EPSILON:
                ratio = (sum_b - sum_s) / total
                ati[i] = float(np.clip(ratio, -1.0, 1.0))
            else:
                ati[i] = 0.0
        return ati

    @classmethod
    def is_buyer_dominated(
        cls,
        ati: IndicatorSeries,
        threshold: float = DEFAULT_BUYER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if ATI is greater than buyer dominance threshold."""
        logger.info(
            "Evaluating ATI is_buyer_dominated: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        val = ati.get(shift)
        return not np.isnan(val) and val > threshold

    @classmethod
    def is_seller_dominated(
        cls,
        ati: IndicatorSeries,
        threshold: float = DEFAULT_SELLER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if ATI is less than seller dominance threshold."""
        logger.info(
            "Evaluating ATI is_seller_dominated: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        val = ati.get(shift)
        return not np.isnan(val) and val < threshold

    @classmethod
    def crosses_above(
        cls, ati: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if ATI crosses above level at shift."""
        logger.info("Evaluating ATI crosses_above level=%.2f at shift=%d", level, shift)
        curr = ati.get(shift)
        prev = ati.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(
        cls, ati: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if ATI crosses below level at shift."""
        logger.info("Evaluating ATI crosses_below level=%.2f at shift=%d", level, shift)
        curr = ati.get(shift)
        prev = ati.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)

    @classmethod
    def is_rising(cls, ati: IndicatorSeries, shift: int = 0) -> bool:
        """True if ATI is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating ATI is_rising at shift=%d", shift)
        curr = ati.get(shift)
        prev = ati.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, ati: IndicatorSeries, shift: int = 0) -> bool:
        """True if ATI is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating ATI is_falling at shift=%d", shift)
        curr = ati.get(shift)
        prev = ati.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
