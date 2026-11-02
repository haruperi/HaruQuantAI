"""Correlation Coefficient statistical analysis block.

Description:
    Calculates the rolling Pearson correlation coefficient between two series
    over a specified lookback period.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative mathematical function library.
Key Capabilities:
    - FR-function-correlation-coefficient: Pearson correlation computation.
    - FR-function-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.functions.correlation_coefficient import (
        CorrelationCoefficient,
    )
    res = CorrelationCoefficient().calculate(series_a, series_b)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

import math
from typing import ClassVar

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import BaseBlock
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import IndicatorSeries

logger = get_logger(__name__)

_MIN_PERIOD: int = 2

_EPSILON: float = 1e-12


def correlation_kernel(x: np.ndarray, y: np.ndarray, period: int) -> np.ndarray:
    """Compute rolling Pearson correlation coefficient between two series."""
    n = min(len(x), len(y))
    out = np.full(n, np.nan, dtype=np.float64)
    if period < _MIN_PERIOD or n < period:
        return out
    for i in range(period - 1, n):
        wx = x[i - period + 1 : i + 1]
        wy = y[i - period + 1 : i + 1]
        mx = float(np.mean(wx))
        my = float(np.mean(wy))
        dx = wx - mx
        dy = wy - my
        cov = float(np.sum(dx * dy))
        var_x = float(np.sum(dx**2))
        var_y = float(np.sum(dy**2))
        denom = math.sqrt(var_x * var_y)
        out[i] = cov / denom if denom > _EPSILON else 0.0
    return out


class CorrelationCoefficient(BaseBlock):
    """Rolling Pearson Correlation Coefficient block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="function.correlation_coefficient",
        version="1.0.0",
        name="Correlation Coefficient",
        description="Rolling Pearson correlation coefficient between two series",
        category="functions",
        tags=("math", "statistics", "correlation"),
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(
            InputPort("source_a", PortType.SERIES, "First data series", required=True),
            InputPort("source_b", PortType.SERIES, "Second data series", required=True),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, "Correlation Coefficient (-1 to 1)"),
        ),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=2)

    def calculate(
        self,
        source_a: list[float] | np.ndarray,
        source_b: list[float] | np.ndarray,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling Pearson correlation."""
        arr_a = np.asarray(source_a, dtype=np.float64)
        arr_b = np.asarray(source_b, dtype=np.float64)
        corr = correlation_kernel(arr_a, arr_b, self.period)
        logger.debug(
            "FR-SERVICES-FUNCTION-CORRELATION: Calculated corr(%d) for %d points",
            self.period,
            len(arr_a),
        )
        return {"value": IndicatorSeries(corr, name="Correlation")}


__all__ = ["CorrelationCoefficient", "correlation_kernel"]
