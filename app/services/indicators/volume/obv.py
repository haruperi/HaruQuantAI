"""On-Balance Volume (OBV) and Money Flow Index (MFI) Indicator Blocks.

Description:
    On-Balance Volume (OBV) measures cumulative buying and selling volume
    pressure based on bar-to-bar price directional changes.
    Money Flow Index (MFI) incorporates volume into a typical price oscillator
    bounded between 0 and 100 to assess institutional buying/selling momentum.

Purpose:
    FEAT-SERVICES-INDICATOR-OBV, FEAT-SERVICES-INDICATOR-MFI

Key Capabilities:
    - FR-SERVICES-OBV-CALCULATE: Computes cumulative signed volume series.
    - FR-SERVICES-OBV-CONDITIONS: Evaluates rising, falling, and crossover states.
    - FR-SERVICES-MFI-CALCULATE: Computes volume-weighted momentum oscillator.
    - FR-SERVICES-MFI-CONDITIONS: Evaluates overbought, oversold, and level crosses.

Python API Usage:
    ```python
    from app.services.indicators.volume.obv import MFI, OBV

    obv = OBV.calculate(close, volume)
    is_rising = OBV.is_rising(obv, shift=0)

    mfi = MFI.calculate(high, low, close, volume, period=14)
    is_overbought = MFI.is_above_level(mfi, level=80.0, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_MFI_PERIOD: int = 2
DEFAULT_MFI_PERIOD: int = 14
DEFAULT_OVERBOUGHT: float = 80.0
DEFAULT_OVERSOLD: float = 20.0
NEUTRAL_MFI: float = 50.0
MAX_MFI: float = 100.0
EPSILON: float = 1e-12


class OBV(BaseIndicator):
    """On-Balance Volume cumulative volume momentum indicator."""

    @classmethod
    @override
    def calculate(
        cls,
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
    ) -> IndicatorSeries:
        """Compute cumulative On-Balance Volume.

        Args:
            close: Close price series.
            volume: Volume series.

        Returns:
            IndicatorSeries containing cumulative OBV.
        """
        logger.info("OBV calculation initiated")
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        obv_vals = cls._compute_obv(c_arr, v_arr)
        return IndicatorSeries(obv_vals, name="OBV")

    @staticmethod
    def _compute_obv(
        c_arr: np.ndarray[Any, Any], v_arr: np.ndarray[Any, Any]
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        obv = np.zeros(n, dtype=np.float64)
        obv[0] = v_arr[0]
        for i in range(1, n):
            if c_arr[i] > c_arr[i - 1]:
                obv[i] = obv[i - 1] + v_arr[i]
            elif c_arr[i] < c_arr[i - 1]:
                obv[i] = obv[i - 1] - v_arr[i]
            else:
                obv[i] = obv[i - 1]
        return obv

    @classmethod
    def is_rising(cls, obv: IndicatorSeries, shift: int = 0) -> bool:
        """True if OBV is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating OBV is_rising at shift=%d", shift)
        curr = obv.get(shift)
        prev = obv.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, obv: IndicatorSeries, shift: int = 0) -> bool:
        """True if OBV is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating OBV is_falling at shift=%d", shift)
        curr = obv.get(shift)
        prev = obv.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev

    @classmethod
    def crosses_above(cls, obv: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if OBV crosses above specified level."""
        logger.info("Evaluating OBV crosses_above level=%.2f at shift=%d", level, shift)
        curr = obv.get(shift)
        prev = obv.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(cls, obv: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if OBV crosses below specified level."""
        logger.info("Evaluating OBV crosses_below level=%.2f at shift=%d", level, shift)
        curr = obv.get(shift)
        prev = obv.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)

    @classmethod
    def is_above_level(
        cls, obv: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if OBV is above specified level."""
        logger.info("Evaluating OBV is_above_level=%.2f at shift=%d", level, shift)
        val = obv.get(shift)
        return not np.isnan(val) and val > level

    @classmethod
    def is_below_level(
        cls, obv: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if OBV is below specified level."""
        logger.info("Evaluating OBV is_below_level=%.2f at shift=%d", level, shift)
        val = obv.get(shift)
        return not np.isnan(val) and val < level


class MFI(BaseIndicator):
    """Money Flow Index volume-weighted momentum oscillator."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_MFI_PERIOD,
    ) -> IndicatorSeries:
        """Compute Money Flow Index over lookback period.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Volume series.
            period: Lookback window (>= 2).

        Returns:
            IndicatorSeries containing MFI values in [0, 100].
        """
        logger.info("MFI calculation initiated: period=%d", period)
        if period < MIN_MFI_PERIOD:
            raise ValueError(f"period must be >= {MIN_MFI_PERIOD}, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        mfi_vals = cls._compute_mfi(h_arr, l_arr, c_arr, v_arr, period)
        return IndicatorSeries(mfi_vals, name=f"MFI({period})")

    @classmethod
    def _compute_mfi(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        period: int,
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        mfi = np.full(n, NEUTRAL_MFI, dtype=np.float64)
        if n < period + 1:
            return mfi

        typical = (h_arr + l_arr + c_arr) / 3.0
        raw_money = typical * v_arr

        pos_flow = np.zeros(n, dtype=np.float64)
        neg_flow = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            if typical[i] > typical[i - 1]:
                pos_flow[i] = raw_money[i]
            elif typical[i] < typical[i - 1]:
                neg_flow[i] = raw_money[i]

        for i in range(period, n):
            start = i - period + 1
            sum_pos = float(np.sum(pos_flow[start : i + 1]))
            sum_neg = float(np.sum(neg_flow[start : i + 1]))

            if sum_neg <= EPSILON:
                mfi[i] = MAX_MFI if sum_pos > 0.0 else NEUTRAL_MFI
            else:
                mr = sum_pos / sum_neg
                mfi[i] = MAX_MFI - (MAX_MFI / (1.0 + mr))

        return mfi

    @classmethod
    def is_above_level(
        cls, mfi: IndicatorSeries, level: float = DEFAULT_OVERBOUGHT, shift: int = 0
    ) -> bool:
        """True if MFI is above specified level (overbought)."""
        logger.info("Evaluating MFI is_above_level=%.2f at shift=%d", level, shift)
        val = mfi.get(shift)
        return not np.isnan(val) and val > level

    @classmethod
    def is_below_level(
        cls, mfi: IndicatorSeries, level: float = DEFAULT_OVERSOLD, shift: int = 0
    ) -> bool:
        """True if MFI is below specified level (oversold)."""
        logger.info("Evaluating MFI is_below_level=%.2f at shift=%d", level, shift)
        val = mfi.get(shift)
        return not np.isnan(val) and val < level

    @classmethod
    def is_overbought(
        cls,
        mfi: IndicatorSeries,
        threshold: float = DEFAULT_OVERBOUGHT,
        shift: int = 0,
    ) -> bool:
        """True if MFI is above overbought threshold."""
        logger.info(
            "Evaluating MFI is_overbought: threshold=%.2f, shift=%d", threshold, shift
        )
        return cls.is_above_level(mfi, level=threshold, shift=shift)

    @classmethod
    def is_oversold(
        cls,
        mfi: IndicatorSeries,
        threshold: float = DEFAULT_OVERSOLD,
        shift: int = 0,
    ) -> bool:
        """True if MFI is below oversold threshold."""
        logger.info(
            "Evaluating MFI is_oversold: threshold=%.2f, shift=%d", threshold, shift
        )
        return cls.is_below_level(mfi, level=threshold, shift=shift)

    @classmethod
    def crosses_above(cls, mfi: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if MFI crosses above level."""
        logger.info("Evaluating MFI crosses_above level=%.2f at shift=%d", level, shift)
        curr = mfi.get(shift)
        prev = mfi.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(cls, mfi: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if MFI crosses below level."""
        logger.info("Evaluating MFI crosses_below level=%.2f at shift=%d", level, shift)
        curr = mfi.get(shift)
        prev = mfi.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)

    @classmethod
    def is_rising(cls, mfi: IndicatorSeries, shift: int = 0) -> bool:
        """True if MFI is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating MFI is_rising at shift=%d", shift)
        curr = mfi.get(shift)
        prev = mfi.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, mfi: IndicatorSeries, shift: int = 0) -> bool:
        """True if MFI is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating MFI is_falling at shift=%d", shift)
        curr = mfi.get(shift)
        prev = mfi.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
