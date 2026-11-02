"""DirectionalIndex trend indicator strategy block.

Description:
    Calculates Directional Movement Index (+DI, -DI) line differences
    and crossovers.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Directional Index trend component calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.directional_index import DirectionalIndex
    res = DirectionalIndex().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.trend.adx import ADX
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class DirectionalIndex(BaseIndicator):
    """Directional Index indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.directional_index",
        name="DirectionalIndex",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("di_plus", PortType.SERIES),
            OutputPort("di_minus", PortType.SERIES),
            OutputPort("dx", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.trend.adx",),
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
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
