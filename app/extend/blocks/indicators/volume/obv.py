"""OBV indicator.

- Calculates On-Balance Volume (OBV) cumulative volume flow momentum.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np

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
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_MFI_PERIOD: int = 2
DEFAULT_MFI_PERIOD: int = 14
DEFAULT_OVERBOUGHT: float = 80.0
DEFAULT_OVERSOLD: float = 20.0
NEUTRAL_MFI: float = 50.0
MAX_MFI: float = 100.0
EPSILON: float = 1e-12


class OBV(BaseIndicator):
    """On-Balance Volume cumulative volume momentum indicator."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.obv",
        version="1.0.0",
        name="OBV",
        description=(
            "Calculates On-Balance Volume (OBV) cumulative volume flow momentum."
        ),
        category="volume",
        tags=("volume", "obv"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
            InputPort(
                "volume",
                PortType.SERIES,
                required=True,
                description="Volume input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("close", "volume"),
        required_history_lookback=1,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={},
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
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
        return 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: OBV requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        close = bars.close
        volume = bars.volume
        logger.info("OBV calculation initiated")
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        obv_vals = self._compute_obv(c_arr, v_arr)
        return {"value": IndicatorSeries(obv_vals, name="OBV")}

    # Specialized methods: indicator-specific behavior only.
    @staticmethod
    def _compute_obv(
        c_arr: np.ndarray[Any, Any], v_arr: np.ndarray[Any, Any]
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        obv = np.zeros(n, dtype=np.float64)
        obv[0] = v_arr[0]
        for i in range(1, n):
            if c_arr[i] > c_arr[i - 1]:
                obv[i] = obv[i - 1] + v_arr[i]
            elif c_arr[i] < c_arr[i - 1]:
                obv[i] = obv[i - 1] - v_arr[i]
            else:
                obv[i] = obv[i - 1]
        return obv

    @classmethod
    def is_rising(cls, obv: IndicatorSeries, shift: int = 0) -> bool:
        """True if OBV is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating OBV is_rising at shift=%d", shift)
        return is_rising(obv, shift=shift)

    @classmethod
    def is_falling(cls, obv: IndicatorSeries, shift: int = 0) -> bool:
        """True if OBV is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating OBV is_falling at shift=%d", shift)
        return is_falling(obv, shift=shift)

    @classmethod
    def crosses_above(cls, obv: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if OBV crosses above specified level."""
        logger.info("Evaluating OBV crosses_above level=%.2f at shift=%d", level, shift)
        return crosses_above(obv, level, shift=shift)

    @classmethod
    def crosses_below(cls, obv: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """True if OBV crosses below specified level."""
        logger.info("Evaluating OBV crosses_below level=%.2f at shift=%d", level, shift)
        return crosses_below(obv, level, shift=shift)

    @classmethod
    def is_above_level(
        cls, obv: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if OBV is above specified level."""
        logger.info("Evaluating OBV is_above_level=%.2f at shift=%d", level, shift)
        return is_greater(obv, level, shift1=shift)

    @classmethod
    def is_below_level(
        cls, obv: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if OBV is below specified level."""
        logger.info("Evaluating OBV is_below_level=%.2f at shift=%d", level, shift)
        return is_lower(obv, level, shift1=shift)


# Public exports.
__all__ = ["OBV"]
