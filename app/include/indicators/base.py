"""Foundational data structures for quantitative indicators.

Description:
    Re-exports the shared `DataframeSeries` contract as `IndicatorSeries`
    (1D numerical arrays with bar shift indexing), along with BaseIndicator
    serving as the abstract base class for all quantitative indicator families.
    Comparison and rule condition evaluations are handled by
    app.include.comparisons.

Purpose:
    FEAT-SERVICES-INDICATOR-FOUNDATION: Universal indicator data container.

Key Capabilities:
    - FR-SERVICES-INDICATOR-SERIES-STORAGE: Typed array storage with shift indexing
      [`IndicatorSeries.get()`, `IndicatorSeries.values`] (`DEBUG`).

Python API Usage:
    ```python
    import numpy as np
    from app.include.indicators.base import IndicatorSeries

    series = IndicatorSeries(np.array([10.0, 12.0, 11.5, 13.0]))
    current_val = series.get(0)  # 13.0
    prev_val = series.get(1)  # 11.5
    ```

CLI Usage:
    ```bash
    uv run pytest tests/include/indicators/test_indicator_gaps.py --no-cov
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from app.host.logging import get_logger
from app.include.contracts import DataframeSeries

logger = get_logger(__name__)

IndicatorSeries = DataframeSeries
"""Indicator output series; alias of the shared `DataframeSeries` contract."""


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
