"""AnchoredVWAP volume indicator strategy block.

Description:
    Calculates Anchored Volume Weighted Average Price (AVWAP) from specific event.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Anchored VWAP volume weighted price.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    res = AnchoredVWAP().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, Literal, override

import numpy as np
from pydantic import Field, field_validator

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
SESSION_DAILY: int = 1
SESSION_WEEKLY: int = 2
SESSION_MONTHLY: int = 3
DEFAULT_STD_DEV_MULT: float = 1.0
MS_TIMESTAMP_THRESHOLD: float = 100000000000.0


class AnchoredVWAP(BaseIndicator):
    """Anchored VWAP indicator with volume-weighted standard deviation bands."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.anchored_vwap",
        name="AnchoredVWAP",
        category="volume",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
            InputPort("timestamps", PortType.SERIES, required=False),
        ),
        outputs=(
            OutputPort("vwap", PortType.SERIES),
            OutputPort("upper", PortType.SERIES),
            OutputPort("lower", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close", "volume"),
        parameter_search_space={
            "session_type": {"type": "int", "choices": [1, 2, 3], "default": 1},
            "std_dev_mult": {
                "type": "float",
                "min": 0.0,
                "max": 4.0,
                "default": 1.0,
                "min_exclusive": True,
            },
            "anchor_period": {"type": "int", "min": 0, "max": 4, "default": 0},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=1,
    )
    session_type: Literal[1, 2, 3] = Field(default=1)
    std_dev_mult: float = Field(default=DEFAULT_STD_DEV_MULT, gt=0.0)
    anchor_period: int = Field(default=0, ge=0)
    anchor_indices: tuple[Annotated[int, Field(ge=0)], ...] | None = Field(default=None)

    @field_validator("anchor_indices", mode="before")
    @classmethod
    def freeze_anchor_indices(cls, value: Any) -> Any:
        """Accept JSON arrays while keeping validated configuration immutable."""
        return tuple(value) if isinstance(value, list) else value

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        volume = bars.volume
        timestamps = bars.timestamps if len(bars.timestamps) else None
        session_type = self.session_type
        std_dev_mult = self.std_dev_mult
        anchor_period = self.anchor_period
        anchor_indices = self.anchor_indices
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        vwap_out = np.full(n, np.nan, dtype=np.float64)
        upper_out = np.full(n, np.nan, dtype=np.float64)
        lower_out = np.full(n, np.nan, dtype=np.float64)
        if n == 0:
            logger.info("FR-SERVICES-AVWAP-CALCULATE: Empty series supplied")
            return {
                "vwap": IndicatorSeries(vwap_out, name="AVWAP"),
                "upper": IndicatorSeries(upper_out, name="AVWAP_Upper"),
                "lower": IndicatorSeries(lower_out, name="AVWAP_Lower"),
            }
        typical_price = (h_arr + l_arr + c_arr) / 3.0
        safe_volume = np.where(v_arr <= 0.0, 1.0, v_arr)
        is_reset = self._detect_resets(
            n=n,
            timestamps=timestamps,
            session_type=session_type,
            anchor_period=anchor_period,
            anchor_indices=anchor_indices,
        )
        cum_pv = 0.0
        cum_vol = 0.0
        cum_pv2 = 0.0
        for i in range(n):
            p = typical_price[i]
            v = safe_volume[i]
            if is_reset[i] or i == 0:
                cum_pv = p * v
                cum_vol = v
                cum_pv2 = p * p * v
            else:
                cum_pv += p * v
                cum_vol += v
                cum_pv2 += p * p * v
            vwap_val = cum_pv / cum_vol if cum_vol > 0.0 else p
            variance = cum_pv2 / cum_vol - vwap_val * vwap_val if cum_vol > 0.0 else 0.0
            variance = max(0.0, variance)
            std_dev = np.sqrt(variance)
            vwap_out[i] = vwap_val
            upper_out[i] = vwap_val + std_dev_mult * std_dev
            lower_out[i] = vwap_val - std_dev_mult * std_dev
        logger.info(
            "FR-SERVICES-AVWAP-CALCULATE: "
            "Computed AVWAP(session=%d, mult=%.2f) for %d bars",
            session_type,
            std_dev_mult,
            n,
        )
        return {
            "vwap": IndicatorSeries(vwap_out, name="AVWAP"),
            "upper": IndicatorSeries(upper_out, name="AVWAP_Upper"),
            "lower": IndicatorSeries(lower_out, name="AVWAP_Lower"),
        }

    @classmethod
    def _detect_timestamp_resets(
        cls, *, ts_arr: np.ndarray[Any, Any], session_type: int, n: int
    ) -> np.ndarray[Any, np.dtype[np.bool_]]:
        """Detect session boundary resets from timestamp array."""
        is_reset = np.zeros(n, dtype=bool)
        try:
            if np.issubdtype(ts_arr.dtype, np.number):
                scale = 1000 if ts_arr[0] > MS_TIMESTAMP_THRESHOLD else 1
                dt_series = (ts_arr / scale).astype("datetime64[s]")
            else:
                dt_series = ts_arr.astype("datetime64[s]")
            if session_type == SESSION_DAILY:
                days = dt_series.astype("datetime64[D]")
                is_reset[1:] = days[1:] != days[:-1]
            elif session_type == SESSION_WEEKLY:
                weeks = dt_series.astype("datetime64[W]")
                is_reset[1:] = weeks[1:] != weeks[:-1]
            elif session_type == SESSION_MONTHLY:
                months = dt_series.astype("datetime64[M]")
                is_reset[1:] = months[1:] != months[:-1]
        except (ValueError, TypeError, KeyError) as err:
            logger.warning(
                "FR-SERVICES-AVWAP-CALCULATE: Timestamp parsing failed (%s)", err
            )
        return is_reset

    @classmethod
    def _detect_resets(
        cls,
        *,
        n: int,
        timestamps: np.ndarray[Any, Any] | list[Any] | None,
        session_type: int,
        anchor_period: int,
        anchor_indices: tuple[int, ...] | None,
    ) -> np.ndarray[Any, np.dtype[np.bool_]]:
        """Determine boolean array indicating bar indices where session resets."""
        is_reset = np.zeros(n, dtype=bool)
        is_reset[0] = True
        if anchor_indices is not None:
            for idx in anchor_indices:
                if 0 <= idx < n:
                    is_reset[idx] = True
            return is_reset
        if timestamps is not None and len(timestamps) == n:
            ts_res = cls._detect_timestamp_resets(
                ts_arr=np.asarray(timestamps), session_type=session_type, n=n
            )
            is_reset[1:] = ts_res[1:]
            return is_reset
        if anchor_period > 0:
            for i in range(anchor_period, n, anchor_period):
                is_reset[i] = True
        return is_reset
