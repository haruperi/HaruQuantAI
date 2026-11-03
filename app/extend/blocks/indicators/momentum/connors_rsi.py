"""ConnorsRSI indicator.

- Calculates Larry Connors' 3-component composite RSI: average of standard RSI,
  Streak RSI, and PercentRank of 1-day rate of change.
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
from app.extend.calculators.rsi import rsi_kernel

logger = get_logger(__name__)

_SCALE_100: float = 100.0


class ConnorsRSI(BaseIndicator):
    """Connors RSI (CRSI) composite indicator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.connors_rsi",
        version="1.0.0",
        name="Connors RSI",
        description="Composite momentum combining RSI, Streak, and PercentRank",
        category="momentum",
        tags=("momentum", "oscillator", "rsi", "connors"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Connors RSI"),),
        required_market_inputs=("close",),
        required_history_lookback=101,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "rsi_period": {"type": "int", "min": 2, "max": 20, "default": 3},
            "streak_period": {"type": "int", "min": 2, "max": 20, "default": 2},
            "rank_period": {"type": "int", "min": 10, "max": 250, "default": 100},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    rsi_period: int = Field(
        default=3,
        ge=1,
        title="Rsi period",
        description="Number of bars in the rsi window",
    )

    streak_period: int = Field(
        default=2,
        ge=1,
        title="Streak period",
        description="Number of bars in the streak window",
    )

    rank_period: int = Field(
        default=100,
        ge=1,
        title="Rank period",
        description="Number of bars in the rank window",
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
        return max(self.rsi_period, self.streak_period, self.rank_period) + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Connors RSI values over historical bars."""
        logger.debug(
            "FR-indicator-calculation: ConnorsRSI requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        crsi = np.full(n, np.nan, dtype=np.float64)
        if n >= self.required_history():
            rsi_price = rsi_kernel(close, self.rsi_period)
            streak = _compute_streak(close)
            rsi_streak = rsi_kernel(streak, self.streak_period)
            roc1 = np.zeros(n, dtype=np.float64)
            with np.errstate(divide="ignore", invalid="ignore"):
                roc1[1:] = (close[1:] - close[:-1]) / close[:-1]
            pr = _compute_percent_rank(roc1, self.rank_period)
            crsi = (rsi_price + rsi_streak + pr) / 3.0
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated ConnorsRSI(%d, %d, %d) "
            "for %d bars",
            self.rsi_period,
            self.streak_period,
            self.rank_period,
            len(bars),
        )
        return {"value": IndicatorSeries(crsi, name="CRSI")}


# Private helpers: used only by this indicator.
def _compute_streak(close: np.ndarray) -> np.ndarray:
    n = len(close)
    streak = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        if close[i] > close[i - 1]:
            streak[i] = streak[i - 1] + 1.0 if streak[i - 1] > 0.0 else 1.0
        elif close[i] < close[i - 1]:
            streak[i] = streak[i - 1] - 1.0 if streak[i - 1] < 0.0 else -1.0
        else:
            streak[i] = 0.0
    return streak


def _compute_percent_rank(roc: np.ndarray, period: int) -> np.ndarray:
    n = len(roc)
    pr = np.full(n, np.nan, dtype=np.float64)
    for i in range(period, n):
        window = roc[i - period : i]
        current = roc[i]
        pr[i] = (np.sum(window < current) / float(period)) * _SCALE_100
    return pr


# Public exports.
__all__ = ["ConnorsRSI"]
