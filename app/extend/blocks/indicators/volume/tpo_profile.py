"""TPOProfile indicator.

- Calculates Time Price Opportunity (TPO) Market Profile distributions.
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
    ExecutionKind,
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

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.tpo_profile",
        version="2.0.0",
        name="TPOProfile",
        description=(
            "Calculates Time Price Opportunity (TPO) Market Profile distributions."
        ),
        category="volume",
        tags=("volume", "tpo-profile"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=tuple(
            InputPort(
                name,
                PortType.SERIES,
                required=True,
                description=f"{name} input series",
            )
            for name in ("open", "high", "low", "close", "volume", "timestamps")
        ),
        outputs=tuple(
            OutputPort(name, PortType.SERIES, description=f"{name} output series")
            for name in TPO_OUTPUTS
        ),
        required_market_inputs=("open", "high", "low", "close", "volume", "timestamps"),
        required_history_lookback=1,
        dependencies=(),
        is_generation_eligible=False,
        parameter_search_space={},
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    timestamp_unit: Literal["seconds", "milliseconds"] = Field(
        default="seconds",
        title="Timestamp unit",
        description="Unit used by the supplied chart timestamps",
    )

    timezone: str = Field(
        default="UTC",
        title="Timezone",
        description="Chart timezone used for calendar and session boundaries",
    )

    bin_size_mode: Literal[1, 2] = Field(
        default=2,
        title="Bin size mode",
        description="Selector for tick-based or row-based profile bin sizing",
    )

    tick_size: float | None = Field(
        default=None,
        gt=0,
        title="Tick size",
        description="Minimum price increment for tick-based profile bins",
    )

    ticks_per_bin: int = Field(
        default=1,
        ge=1,
        le=1000,
        title="Ticks per bin",
        description="Number of price ticks in each profile bin",
    )

    value_area_pct: float = Field(
        default=70.0,
        ge=30,
        le=95,
        title="Value area pct",
        description="Percentage of profile activity included in the value area",
    )

    session_type: int = Field(
        default=1,
        ge=1,
        le=8,
        title="Session type",
        description="Session calendar selector",
    )

    profile_rows: int = Field(
        default=150,
        ge=10,
        le=500,
        title="Profile rows",
        description="Target number of price rows in the session profile",
    )

    use_custom_hours: bool = Field(
        default=False,
        title="Use custom hours",
        description="Whether to restrict daily profiles to custom hours",
    )

    session_start: int = Field(
        default=0,
        ge=0,
        le=1439,
        title="Session start",
        description="Session start in minutes after midnight",
    )

    session_end: int = Field(
        default=1439,
        ge=0,
        le=1439,
        title="Session end",
        description="Session end in minutes after midnight",
    )

    bracket_min_daily: int = Field(
        default=30,
        ge=1,
        le=120,
        title="Bracket min daily",
        description="Bracket min daily used by the indicator calculation",
    )

    bracket_min_weekly: int = Field(
        default=240,
        ge=1,
        le=10000,
        title="Bracket min weekly",
        description="Bracket min weekly used by the indicator calculation",
    )

    bracket_min_monthly: int = Field(
        default=720,
        ge=1,
        le=10000,
        title="Bracket min monthly",
        description="Bracket min monthly used by the indicator calculation",
    )

    bracket_min_yearly: int = Field(
        default=720,
        ge=1,
        le=10000,
        title="Bracket min yearly",
        description="Bracket min yearly used by the indicator calculation",
    )

    # Parameter validation: only relationships and custom constraints.
    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        """Require a real chart timezone rather than guessing broker local time."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown chart timezone") from exc
        return value

    @model_validator(mode="after")
    def custom_daily_only(self) -> TPOProfile:
        """Reject custom-hour settings when a non-daily calendar is selected."""
        if self.use_custom_hours and self.session_type not in (1, 5):
            raise ValueError("Custom hours require a daily TPO session")
        return self

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the existing startup requirement for this calculation."""
        return self.spec.required_history_lookback

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Count distinct time brackets at each price within the selected session."""
        logger.debug(
            "FR-indicator-calculation: TPOProfile requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        custom = (
            (self.session_start, self.session_end) if self.use_custom_hours else None
        )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated TPOProfile for %d bars",
            len(bars),
        )
        return calculate_sessions(bars, self.model_dump(), tpo=True, custom=custom)

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["TPOProfile"]
