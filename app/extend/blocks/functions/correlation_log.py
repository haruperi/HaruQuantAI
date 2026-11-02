"""Correlation Log statistical analysis block.

Description:
    Calculates the rolling Pearson correlation coefficient between the
    logarithmic returns of two asset series over a lookback window.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative mathematical function library.
Key Capabilities:
    - FR-function-correlation-log: Logarithmic returns correlation computation.
    - FR-function-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.functions.correlation_log import CorrelationLog
    res = CorrelationLog().calculate(series_a, series_b)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import BaseBlock
from app.extend.blocks.functions.correlation_coefficient import (
    correlation_kernel,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import IndicatorSeries

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_MIN_POINTS: int = 2


class CorrelationLog(BaseBlock):
    """Rolling Logarithmic Return Correlation block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="function.correlation_log",
        version="1.0.0",
        name="Correlation - Log",
        description="Rolling correlation computed on logarithmic returns",
        category="functions",
        tags=("math", "statistics", "correlation", "log"),
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(
            InputPort("source_a", PortType.SERIES, "First price series", required=True),
            InputPort(
                "source_b", PortType.SERIES, "Second price series", required=True
            ),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Log Correlation (-1 to 1)"),),
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
        """Compute rolling logarithmic correlation."""
        arr_a = np.asarray(source_a, dtype=np.float64)
        arr_b = np.asarray(source_b, dtype=np.float64)
        n = min(len(arr_a), len(arr_b))
        out = np.full(n, np.nan, dtype=np.float64)
        if n >= _MIN_POINTS:
            log_a = np.diff(np.log(np.maximum(arr_a[:n], _EPSILON)))
            log_b = np.diff(np.log(np.maximum(arr_b[:n], _EPSILON)))
            log_corr = correlation_kernel(log_a, log_b, self.period)
            out[1:] = log_corr
        logger.debug(
            "FR-SERVICES-FUNCTION-CORRELATION: Calculated log_corr(%d) for %d pts",
            self.period,
            n,
        )
        return {"value": IndicatorSeries(out, name="CorrelationLog")}


__all__ = ["CorrelationLog"]
