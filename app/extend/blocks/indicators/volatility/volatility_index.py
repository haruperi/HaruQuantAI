"""VolatilityIndex indicator.

- Calculates a standardized percentage Volatility Index based on rolling annualized
  log-return standard deviation (historical VIX model).
"""

from __future__ import annotations

import math
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

_SCALE_100: float = 100.0
_MIN_BARS: int = 2


class VolatilityIndex(BaseIndicator):
    """Volatility Index historical model block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.volatility_index",
        version="1.0.0",
        name="Volatility Index",
        description="Standardized annualized volatility percentage index",
        category="volatility",
        tags=("volatility", "volatility_index", "vix"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Volatility Index"),),
        required_market_inputs=("close",),
        required_history_lookback=31,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 30},
            "annual_days": {"type": "int", "min": 1, "max": 365, "default": 252},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=30,
        ge=2,
        title="Period",
        description="Number of bars in the calculation window",
    )

    annual_days: int = Field(
        default=252,
        ge=1,
        title="Annual days",
        description="Number of trading days used for annualization",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Volatility Index values."""
        logger.debug(
            "FR-indicator-calculation: VolatilityIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        out = np.full(n, np.nan, dtype=np.float64)
        p = self.period
        if n >= p + 1:
            log_ret = np.diff(np.log(np.maximum(close, 1e-12)))
            scale = math.sqrt(float(self.annual_days)) * _SCALE_100
            for i in range(p - 1, len(log_ret)):
                window = log_ret[i - p + 1 : i + 1]
                std = float(np.std(window, ddof=1))
                out[i + 1] = std * scale
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated VolIndex(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(out, name="VolIndex")}


# Public exports.
__all__ = ["VolatilityIndex"]
