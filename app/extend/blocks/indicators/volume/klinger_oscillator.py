"""Klinger Volume Oscillator (KO) strategy block.

Description:
    Calculates Stephen Klinger's Volume Oscillator designed to determine
    the long-term trend of money flow while remaining sensitive to
    short-term fluctuations.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-klinger-oscillator: Klinger oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.klinger_oscillator import (
        KlingerOscillator,
    )
    res = KlingerOscillator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


_SCALE_100: float = 100.0
_EPSILON: float = 1e-12
_MIN_BARS: int = 2


class KlingerOscillator(BaseIndicator):
    """Klinger Volume Oscillator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.klinger_oscillator",
        version="1.0.0",
        name="Klinger Oscillator",
        description="Stephen Klinger volume force oscillator with signal line",
        category="volume",
        tags=("volume", "oscillator", "klinger"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(
            OutputPort("ko", PortType.SERIES, "Klinger Oscillator"),
            OutputPort("signal", PortType.SERIES, "Signal Line"),
        ),
        required_market_inputs=("high", "low", "close", "volume"),
        parameter_search_space={
            "fast_period": {"type": "int", "min": 10, "max": 50, "default": 34},
            "slow_period": {"type": "int", "min": 20, "max": 100, "default": 55},
            "signal_period": {"type": "int", "min": 5, "max": 30, "default": 13},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    fast_period: int = Field(default=34, ge=1)
    slow_period: int = Field(default=55, ge=1)
    signal_period: int = Field(default=13, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.fast_period, self.slow_period) + self.signal_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Klinger Oscillator and trigger signal."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        n = len(close)
        vf = np.zeros(n, dtype=np.float64)
        if n >= _MIN_BARS:
            hlc = high + low + close
            dm = high - low
            cm = np.zeros(n, dtype=np.float64)
            prev_cm = 0.0
            for i in range(1, n):
                trend = 1.0 if hlc[i] > hlc[i - 1] else -1.0
                curr_dm = dm[i]
                if trend == (
                    1.0 if hlc[i - 1] > (hlc[i - 2] if i > 1 else hlc[i - 1]) else -1.0
                ):
                    curr_cm = prev_cm + curr_dm
                else:
                    curr_cm = curr_dm
                prev_cm = curr_cm
                cm[i] = curr_cm
                ratio = (2.0 * (curr_dm / curr_cm) - 1.0) if curr_cm > _EPSILON else 0.0
                vf[i] = volume[i] * abs(ratio) * trend * _SCALE_100
        fast_ema = ema_kernel(vf, self.fast_period)
        slow_ema = ema_kernel(vf, self.slow_period)
        ko = fast_ema - slow_ema
        signal = _safe_ema(ko, self.signal_period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated Klinger for %d bars",
            len(bars),
        )
        return {
            "ko": IndicatorSeries(ko, name="KO"),
            "signal": IndicatorSeries(signal, name="Signal"),
        }


__all__ = ["KlingerOscillator"]
