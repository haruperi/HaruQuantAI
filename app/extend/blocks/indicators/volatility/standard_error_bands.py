"""Standard Error Bands volatility strategy block.

Description:
    Calculates Standard Error Bands around a Linear Regression curve with
    specified standard error envelope multipliers.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-standard-error-bands: Standard error bands computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.standard_error_bands import (
        StandardErrorBands,
    )
    res = StandardErrorBands().calculate(bars)
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
from app.extend.blocks.indicators.trend.lin_reg import LinReg
from app.extend.blocks.indicators.volatility.standard_error import (
    standard_error_kernel,
)

logger = get_logger(__name__)


class StandardErrorBands(BaseIndicator):
    """Standard Error Bands block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.standard_error_bands",
        version="1.0.0",
        name="Standard Error Bands",
        description="Linear regression curve with standard error envelope bands",
        category="volatility",
        tags=("volatility", "bands", "standard_error", "linreg"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Standard Error Band"),
            OutputPort("middle", PortType.SERIES, "Middle Linear Regression Line"),
            OutputPort("lower", PortType.SERIES, "Lower Standard Error Band"),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 3, "max": 100, "default": 20},
            "multiplier": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=3)
    multiplier: float = Field(default=2.0, gt=0.0)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Standard Error Bands."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        middle = LinReg(period=self.period).calculate(bars)["lin_reg"].values
        se = standard_error_kernel(close, self.period)
        upper = middle + self.multiplier * se
        lower = middle - self.multiplier * se
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated SEB(%d, %.2f) for %d bars",
            self.period,
            self.multiplier,
            len(bars),
        )
        return {
            "upper": IndicatorSeries(upper, name="SEB.Upper"),
            "middle": IndicatorSeries(middle, name="SEB.Middle"),
            "lower": IndicatorSeries(lower, name="SEB.Lower"),
        }


__all__ = ["StandardErrorBands"]
