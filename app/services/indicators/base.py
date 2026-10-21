"""Foundational data structures for quantitative indicators.

Description:
    Provides the core IndicatorSeries abstraction wrapping 1D numerical
    arrays with bar shift indexing and vectorization, along with BaseIndicator
    serving as the abstract base class for all quantitative indicator families.
    Comparison and rule condition evaluations are handled by
    app.services.include.comparisons.

Purpose:
    FEAT-SERVICES-INDICATOR-FOUNDATION: Universal indicator data container.

Key Capabilities:
    - FR-SERVICES-INDICATOR-SERIES-STORAGE: Typed array storage with shift indexing
      [`IndicatorSeries.get()`, `IndicatorSeries.values`] (`DEBUG`).

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.base import IndicatorSeries

    series = IndicatorSeries(np.array([10.0, 12.0, 11.5, 13.0]))
    current_val = series.get(0)  # 13.0
    prev_val = series.get(1)  # 11.5
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py --no-cov
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
            return float("nan")
        return float(self._values[-(1 + shift)])


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

    @classmethod
    @abstractmethod
    def calculate(cls, *args: Any, **kwargs: Any) -> Any:
        """Compute the indicator series."""


__all__ = ["BaseIndicator", "IndicatorSeries"]
