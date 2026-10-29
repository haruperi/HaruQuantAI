"""OBV indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-OBV: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

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

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.obv",
        name="OBV",
        category="volume",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close", "volume"),
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=1,
    )

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
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
