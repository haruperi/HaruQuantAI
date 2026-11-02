"""Balance of Power momentum indicator strategy block.

Description:
    Calculates Igor Livshin's Balance of Power (BOP) comparing buyer vs seller
    ability to push price to extreme levels, smoothed by a moving average.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-balance-of-power: Balance of power computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.balance_of_power import (
        BalanceOfPower,
    )
    res = BalanceOfPower().calculate(bars)
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)

_EPSILON: float = 1e-12


class BalanceOfPower(BaseIndicator):
    """Balance of Power (BOP) indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.balance_of_power",
        version="1.0.0",
        name="Balance of Power",
        description="Measures the market power of buyers versus sellers",
        category="momentum",
        tags=("momentum", "oscillator", "balance_of_power", "bop"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, "Open price series", required=True),
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Balance of Power"),),
        required_market_inputs=("open", "high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 100, "default": 14},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Balance of Power values over historical bars."""
        bars.require_inputs(self.spec.required_market_inputs)
        open_arr = np.asarray(bars.open, dtype=np.float64)
        high_arr = np.asarray(bars.high, dtype=np.float64)
        low_arr = np.asarray(bars.low, dtype=np.float64)
        close_arr = np.asarray(bars.close, dtype=np.float64)
        hl_range = high_arr - low_arr
        raw_bop = np.zeros_like(close_arr)
        with np.errstate(divide="ignore", invalid="ignore"):
            valid_mask = hl_range > _EPSILON
            raw_bop[valid_mask] = (
                close_arr[valid_mask] - open_arr[valid_mask]
            ) / hl_range[valid_mask]
        bop = sma_kernel(raw_bop, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated BOP(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(bop, name="BOP")}


__all__ = ["BalanceOfPower"]
