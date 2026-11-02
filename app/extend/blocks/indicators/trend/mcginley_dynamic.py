"""McGinley Dynamic tracking moving average strategy block.

Description:
    Calculates John McGinley's dynamic tracking moving average that automatically
    adjusts its speed according to market acceleration.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-mcginley-dynamic: McGinley dynamic computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.mcginley_dynamic import (
        McGinleyDynamic,
    )
    res = McGinleyDynamic().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)

_K_FACTOR: float = 0.6
_POWER_FACTOR: float = 4.0
_EPSILON: float = 1e-12


def mcginley_kernel(data: np.ndarray, period: int, k: float = _K_FACTOR) -> np.ndarray:
    """Compute McGinley Dynamic over 1D series."""
    n = len(data)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n == 0:
        return out
    out[0] = data[0]
    for i in range(1, n):
        prev = out[i - 1]
        c = data[i]
        if prev > _EPSILON:
            ratio = c / prev
            denom = k * period * (ratio**_POWER_FACTOR)
            out[i] = prev + (c - prev) / denom if denom > _EPSILON else prev
        else:
            out[i] = c
    return out


class McGinleyDynamic(BaseIndicator):
    """McGinley Dynamic tracking moving average block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.mcginley_dynamic",
        version="1.0.0",
        name="McGinley Dynamic",
        description="Speed-adaptive tracking moving average (John McGinley)",
        category="trend",
        tags=("trend", "ma", "mcginley", "adaptive"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "McGinley Dynamic"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 14},
            "k": {"type": "float", "min": 0.1, "max": 2.0, "default": 0.6},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=14, ge=1)
    k: float = Field(default=0.6, gt=0.0)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute McGinley Dynamic values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        md = mcginley_kernel(close, self.period, self.k)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated McGinley(%d, %.2f) for %d bars",
            self.period,
            self.k,
            len(bars),
        )
        return {"value": IndicatorSeries(md, name="McGinley")}


__all__ = ["McGinleyDynamic", "mcginley_kernel"]
