"""Foundational data structures and condition evaluators for indicators.

Description:
    Provides the core IndicatorSeries abstraction wrapping 1D numerical
    arrays with bar shift indexing, vectorization, and universal condition
    evaluation (rising, falling, crosses above, crosses below, higher, lower).
    Serves as the base framework for all 53 StrategyQuant X indicator families.

Purpose:
    FEAT-SERVICES-INDICATOR-FOUNDATION: Universal indicator data and conditions.

Key Capabilities:
    - FR-SERVICES-INDICATOR-SERIES-STORAGE: Typed array storage with shift indexing.
      Associated: `IndicatorSeries.get()`, `IndicatorSeries.values`
      Logging: DEBUG on series instantiation and out-of-bounds access.
    - FR-SERVICES-SERIES-CONDITION-EVALUATOR: Universal rule condition evaluations.
      Associated: `IndicatorSeries.is_rising()`, `IndicatorSeries.crosses_above()`
      Logging: DEBUG on condition evaluation outcomes.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.base import IndicatorSeries

    series = IndicatorSeries(np.array([10.0, 12.0, 11.5, 13.0]))
    current_val = series.get(0)  # 13.0
    prev_val = series.get(1)  # 11.5
    is_rising = series.is_rising(shift=0)  # True
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_indicators.py --no-cov
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

import numpy as np

from app.host.logging import get_logger

logger = get_logger(__name__)


class IndicatorSeries:
    """Numerical time series wrapper with shift-based quantitative indexing."""

    def __init__(self, values: np.ndarray | Sequence[float], name: str = "") -> None:
        """Initialize an IndicatorSeries.

        Args:
            values: 1D array or sequence of float values.
            name: Optional descriptive series name.
        """
        if isinstance(values, np.ndarray):
            self._values: np.ndarray = values.astype(np.float64)
        else:
            self._values = np.array(values, dtype=np.float64)

        self._name = name
        logger.debug(
            "FR-SERVICES-INDICATOR-SERIES-STORAGE: Initialized series '%s' (%d bars)",
            self._name,
            len(self._values),
        )

    @property
    def name(self) -> str:
        """Return the series identifier name."""
        return self._name

    @property
    def values(self) -> np.ndarray:
        """Return underlying NumPy array of values."""
        return self._values

    def __len__(self) -> int:
        """Return total bar count."""
        return len(self._values)

    def get(self, shift: int = 0) -> float:
        """Get series value at the specified historical bar shift.

        Args:
            shift: Historical offset where 0 is newest bar, 1 is 1 bar ago.

        Returns:
            Float value at the given shift, or NaN if outside range.
        """
        if shift < 0 or shift >= len(self._values):
            logger.debug(
                "FR-SERVICES-INDICATOR-SERIES-STORAGE: Shift %d out of bounds (len=%d)",
                shift,
                len(self._values),
            )
            return float("nan")
        return float(self._values[-(1 + shift)])

    def is_rising(self, shift: int = 0) -> bool:
        """Check if indicator value at shift is strictly greater than shift + 1.

        Args:
            shift: Bar shift to evaluate.

        Returns:
            True if rising, False otherwise.
        """
        val0 = self.get(shift)
        val1 = self.get(shift + 1)
        res = not (np.isnan(val0) or np.isnan(val1)) and val0 > val1
        logger.debug(
            "FR-SERVICES-SERIES-CONDITION-EVALUATOR: is_rising(shift=%d) = %s",
            shift,
            res,
        )
        return res

    def is_falling(self, shift: int = 0) -> bool:
        """Check if indicator value at shift is strictly lower than shift + 1.

        Args:
            shift: Bar shift to evaluate.

        Returns:
            True if falling, False otherwise.
        """
        val0 = self.get(shift)
        val1 = self.get(shift + 1)
        res = not (np.isnan(val0) or np.isnan(val1)) and val0 < val1
        logger.debug(
            "FR-SERVICES-SERIES-CONDITION-EVALUATOR: is_falling(shift=%d) = %s",
            shift,
            res,
        )
        return res

    def crosses_above(self, level: float | IndicatorSeries, shift: int = 0) -> bool:
        """Check if series crossed above a level/series between shift+1 and shift.

        Args:
            level: Constant float threshold or another IndicatorSeries.
            shift: Bar shift to evaluate.

        Returns:
            True if crossing upwards occurred.
        """
        curr_val = self.get(shift)
        prev_val = self.get(shift + 1)
        curr_lvl = level.get(shift) if isinstance(level, IndicatorSeries) else level
        prev_lvl = level.get(shift + 1) if isinstance(level, IndicatorSeries) else level
        nan_check = (
            np.isnan(curr_val)
            or np.isnan(prev_val)
            or np.isnan(curr_lvl)
            or np.isnan(prev_lvl)
        )
        if nan_check:
            return False

        res = prev_val <= prev_lvl and curr_val > curr_lvl
        logger.debug(
            "FR-SERVICES-SERIES-CONDITION-EVALUATOR: crosses_above(shift=%d) = %s",
            shift,
            res,
        )
        return res

    def crosses_below(self, level: float | IndicatorSeries, shift: int = 0) -> bool:
        """Check if series crossed below a level/series between shift+1 and shift.

        Args:
            level: Constant float threshold or another IndicatorSeries.
            shift: Bar shift to evaluate.

        Returns:
            True if crossing downwards occurred.
        """
        curr_val = self.get(shift)
        prev_val = self.get(shift + 1)
        curr_lvl = level.get(shift) if isinstance(level, IndicatorSeries) else level
        prev_lvl = level.get(shift + 1) if isinstance(level, IndicatorSeries) else level

        nan_check = (
            np.isnan(curr_val)
            or np.isnan(prev_val)
            or np.isnan(curr_lvl)
            or np.isnan(prev_lvl)
        )
        if nan_check:
            return False

        res = prev_val >= prev_lvl and curr_val < curr_lvl
        logger.debug(
            "FR-SERVICES-SERIES-CONDITION-EVALUATOR: crosses_below(shift=%d) = %s",
            shift,
            res,
        )
        return res

    def is_greater(self, other: float | IndicatorSeries, shift: int = 0) -> bool:
        """Check if series value at shift is greater than another level or series.

        Args:
            other: Constant float threshold or another IndicatorSeries.
            shift: Bar shift to evaluate.

        Returns:
            True if strictly greater.
        """
        val = self.get(shift)
        other_val = other.get(shift) if isinstance(other, IndicatorSeries) else other
        if np.isnan(val) or np.isnan(other_val):
            return False
        return val > other_val

    def is_lower(self, other: float | IndicatorSeries, shift: int = 0) -> bool:
        """Check if series value at shift is lower than another level or series.

        Args:
            other: Constant float threshold or another IndicatorSeries.
            shift: Bar shift to evaluate.

        Returns:
            True if strictly lower.
        """
        val = self.get(shift)
        other_val = other.get(shift) if isinstance(other, IndicatorSeries) else other
        if np.isnan(val) or np.isnan(other_val):
            return False
        return val < other_val

    def is_higher(self, lookback: int = 1, shift: int = 0) -> bool:
        """Check if series value at shift is higher than shift + lookback.

        Args:
            lookback: Historical bar distance to compare against.
            shift: Reference bar shift.

        Returns:
            True if value is higher than lookback bars ago.
        """
        val0 = self.get(shift)
        val_past = self.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 > val_past

    def changes_up(self, shift: int = 0) -> bool:
        """Check if indicator turned upwards (was flat/falling, now rising).

        Args:
            shift: Bar shift to evaluate.

        Returns:
            True if momentum turned upward.
        """
        v0 = self.get(shift)
        v1 = self.get(shift + 1)
        v2 = self.get(shift + 2)
        if np.isnan(v0) or np.isnan(v1) or np.isnan(v2):
            return False
        return v0 > v1 and v1 <= v2

    def changes_down(self, shift: int = 0) -> bool:
        """Check if indicator turned downwards (was flat/rising, now falling).

        Args:
            shift: Bar shift to evaluate.

        Returns:
            True if momentum turned downward.
        """
        v0 = self.get(shift)
        v1 = self.get(shift + 1)
        v2 = self.get(shift + 2)
        if np.isnan(v0) or np.isnan(v1) or np.isnan(v2):
            return False
        return v0 < v1 and v1 >= v2


class BaseIndicator(ABC):
    """Abstract base class for all indicator family implementations."""

    name: str = "BaseIndicator"
    category: str = "Indicators"

    @staticmethod
    def to_numpy(val: Any) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Convert input sequence or IndicatorSeries to a 1D float64 numpy array."""
        if isinstance(val, IndicatorSeries):
            return val.values
        return np.asarray(val, dtype=np.float64)

    _to_numpy = to_numpy

    @classmethod
    @abstractmethod
    def calculate(cls, *args: Any, **kwargs: Any) -> Any:
        """Compute the indicator series."""


__all__ = ["BaseIndicator", "IndicatorSeries"]
