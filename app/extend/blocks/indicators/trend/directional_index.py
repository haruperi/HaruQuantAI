"""DirectionalIndex indicator.

- Calculates Directional Movement Index (+DI, -DI) line differences and crossovers.
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
from app.extend.blocks.indicators.trend.adx import ADX

logger = get_logger(__name__)


class DirectionalIndex(BaseIndicator):
    """Directional Index indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.directional_index",
        version="1.0.0",
        name="DirectionalIndex",
        description=(
            "Calculates Directional Movement Index (+DI, -DI) line "
            "differences and crossovers."
        ),
        category="trend",
        tags=("trend", "directional-index"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("di_plus", PortType.SERIES, description="Di plus output series"),
            OutputPort(
                "di_minus", PortType.SERIES, description="Di minus output series"
            ),
            OutputPort("dx", PortType.SERIES, description="Dx output series"),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=15,
        dependencies=("indicator.trend.adx",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: DirectionalIndex requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        period = self.period
        adx_dict = ADX(period=period).calculate(bars)
        di_plus = adx_dict["di_plus"]
        di_minus = adx_dict["di_minus"]
        p_vals = di_plus.values
        m_vals = di_minus.values
        denom = p_vals + m_vals
        dx_arr = np.full_like(p_vals, np.nan)
        valid = ~np.isnan(denom) & (denom > 0)
        dx_arr[valid] = 100.0 * np.abs(p_vals[valid] - m_vals[valid]) / denom[valid]
        logger.info(
            "FR-SERVICES-DX-CALCULATE: Computed DX(period=%d) for %d bars",
            period,
            len(p_vals),
        )
        return {
            "di_plus": di_plus,
            "di_minus": di_minus,
            "dx": IndicatorSeries(dx_arr, name=f"DX({period})"),
        }


# Public exports.
__all__ = ["DirectionalIndex"]
