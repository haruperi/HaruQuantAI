"""ChandeMomentumOscillator indicator.

- Calculates Tushar Chande's CMO oscillator measuring momentum on both up and down
  days without smoothing the momentum values.
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

_EPSILON: float = 1e-12
_SCALE_100: float = 100.0


class ChandeMomentumOscillator(BaseIndicator):
    """Chande Momentum Oscillator (CMO) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.chande_momentum_oscillator",
        version="1.0.0",
        name="Chande Momentum Oscillator",
        description="Calculates momentum over positive and negative days directly",
        category="momentum",
        tags=("momentum", "oscillator", "cmo", "chande"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Chande Momentum Oscillator"),),
        required_market_inputs=("close",),
        required_history_lookback=15,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 14}
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
        """Return minimum history bars needed for valid calculation."""
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Chande Momentum Oscillator values over historical bars."""
        logger.debug(
            "FR-indicator-calculation: ChandeMomentumOscillator requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        cmo = np.full(n, np.nan, dtype=np.float64)
        if n > self.period:
            diff = np.diff(close)
            up = np.where(diff > 0.0, diff, 0.0)
            down = np.where(diff < 0.0, -diff, 0.0)
            up_cs = np.insert(np.cumsum(up), 0, 0.0)
            dn_cs = np.insert(np.cumsum(down), 0, 0.0)
            p = self.period
            su = up_cs[p:] - up_cs[:-p]
            sd = dn_cs[p:] - dn_cs[:-p]
            total = su + sd
            with np.errstate(divide="ignore", invalid="ignore"):
                val = np.where(total > _EPSILON, _SCALE_100 * (su - sd) / total, 0.0)
            cmo[p:] = val
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated CMO(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(cmo, name="CMO")}


# Public exports.
__all__ = ["ChandeMomentumOscillator"]
