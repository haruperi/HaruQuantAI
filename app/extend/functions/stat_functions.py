"""Statistical calculation functions (matching donor StatFunctions.java).

Description:
    Implements StatFunctions computing mean average and standard deviation over
    sequences of float values with optional index range bounds and safe division
    handling, conforming to StrategyQuant StatFunctions.

Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions.

Key Capabilities:
    - FR-FUNCTIONS-STAT-AVERAGE: Compute mean average over value sequence or slice.
    - FR-FUNCTIONS-STAT-STDEV: Compute population standard deviation over slice.

Python API Usage:
    from app.extend.functions.stat_functions import StatFunctions
    avg = StatFunctions.compute_average([10.0, 20.0, 30.0])
    sd = StatFunctions.compute_stdev(avg, [10.0, 20.0, 30.0])

CLI Usage:
    uv run pytest tests/extend/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class StatFunctions:
    """Statistical utility functions for average and standard deviation."""

    @classmethod
    def compute_average(
        cls,
        values: Sequence[float],
        from_idx: int = 0,
        to_idx: int = -1,
    ) -> float:
        """Compute mean average of values in specified slice range.

        Args:
            values: Sequence of numeric float values.
            from_idx: Starting index inclusive (default 0).
            to_idx: Ending index exclusive (-1 means end of sequence).

        Returns:
            Calculated mean average, or 0.0 if empty or invalid range.
        """
        if not values:
            return 0.0

        end = len(values) if to_idx == -1 else min(to_idx, len(values))
        count = end - from_idx

        if count <= 0 or from_idx < 0:
            return 0.0

        total = sum(values[from_idx:end])
        result = total / count

        logger.debug(
            "FR-FUNCTIONS-STAT-AVERAGE: average=%f for count=%d (from=%d, to=%d)",
            result,
            count,
            from_idx,
            end,
        )
        return float(result)

    @classmethod
    def compute_stdev(
        cls,
        mean: float,
        values: Sequence[float],
        from_idx: int = 0,
        to_idx: int = -1,
    ) -> float:
        """Compute population standard deviation relative to given mean.

        Args:
            mean: Precomputed mean average of values.
            values: Sequence of numeric float values.
            from_idx: Starting index inclusive (default 0).
            to_idx: Ending index exclusive (-1 means end of sequence).

        Returns:
            Calculated standard deviation, or 0.0 if empty or invalid range.
        """
        if not values:
            return 0.0

        end = len(values) if to_idx == -1 else min(to_idx, len(values))
        count = end - from_idx

        if count <= 0 or from_idx < 0:
            return 0.0

        variance_sum = sum((val - mean) ** 2 for val in values[from_idx:end])
        stdev = math.sqrt(variance_sum / count)

        logger.debug(
            "FR-FUNCTIONS-STAT-STDEV: stdev=%f for count=%d (from=%d, to=%d)",
            stdev,
            count,
            from_idx,
            end,
        )
        return float(stdev)
