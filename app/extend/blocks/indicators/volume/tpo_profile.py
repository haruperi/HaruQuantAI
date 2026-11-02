"""TPOProfile volume indicator strategy block.

Description:
    Calculates Time Price Opportunity (TPO) Market Profile distributions.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Time Price Opportunity profile calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.tpo_profile import TPOProfile
    res = TPOProfile().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, Literal, override
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np
from pydantic import Field, field_validator, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.profile import TPO_OUTPUTS
from app.extend.calculators.profile_sessions import calculate_sessions

logger = get_logger(__name__)


class TPOProfile(BaseIndicator):
    """Donor session profiles with validated in-class configuration."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.tpo_profile",
        version="2.0.0",
        name="TPOProfile",
        category="volume",
        chart_pane=ChartPane.MAIN,
        inputs=tuple(
            InputPort(name, PortType.SERIES, required=True)
            for name in ("open", "high", "low", "close", "volume", "timestamps")
        ),
        outputs=tuple(OutputPort(name, PortType.SERIES) for name in TPO_OUTPUTS),
        required_market_inputs=("open", "high", "low", "close", "volume", "timestamps"),
        is_causal=True,
        is_generation_eligible=False,
        required_history_lookback=1,
    )
    timestamp_unit: Literal["seconds", "milliseconds"] = "seconds"
    timezone: str = "UTC"
    bin_size_mode: Literal[1, 2] = 2
    tick_size: float | None = Field(default=None, gt=0)
    ticks_per_bin: int = Field(default=1, ge=1, le=1000)
    value_area_pct: float = Field(default=70.0, ge=30, le=95)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        """Require a real chart timezone rather than guessing broker local time."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown chart timezone") from exc
        return value

    session_type: int = Field(default=1, ge=1, le=8)
    profile_rows: int = Field(default=150, ge=10, le=500)
    use_custom_hours: bool = False
    session_start: int = Field(default=0, ge=0, le=1439)
    session_end: int = Field(default=1439, ge=0, le=1439)
    bracket_min_daily: int = Field(default=30, ge=1, le=120)
    bracket_min_weekly: int = Field(default=240, ge=1, le=10000)
    bracket_min_monthly: int = Field(default=720, ge=1, le=10000)
    bracket_min_yearly: int = Field(default=720, ge=1, le=10000)

    @model_validator(mode="after")
    def custom_daily_only(self) -> TPOProfile:
        """Reject custom-hour settings when a non-daily calendar is selected."""
        if self.use_custom_hours and self.session_type not in (1, 5):
            raise ValueError("Custom hours require a daily TPO session")
        return self

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Count distinct time brackets at each price within the selected session."""
        custom = (
            (self.session_start, self.session_end) if self.use_custom_hours else None
        )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated TPOProfile for %d bars",
            len(bars),
        )
        return calculate_sessions(bars, self.model_dump(), tpo=True, custom=custom)

    @classmethod
    def price_inside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is within TPO Value Area."""
        c = close.get(shift)
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return lower <= c <= upper

    @classmethod
    def price_outside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is outside TPO Value Area."""
        c = close.get(shift)
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return c > upper or c < lower
