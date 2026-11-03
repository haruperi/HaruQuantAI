"""HighestInRange indicator.

- Calculates highest price observed within a bounded rolling window.
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

from pydantic import Field, field_validator

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
from app.extend.calculators.highest import time_window_extreme, validate_hhmm

logger = get_logger(__name__)


class HighestInRange(BaseIndicator):
    """Completed daily HHMM-window extreme with explicit chart time context."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.highest_in_range",
        version="1.0.0",
        name="HighestInRange",
        description=(
            "Calculates highest price observed within a bounded rolling window."
        ),
        category="volatility",
        tags=("volatility", "highest-in-range"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=tuple(
            InputPort(
                key,
                PortType.SERIES,
                required=True,
                description=f"{key} input series",
            )
            for key in ("high", "timestamps")
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("high", "timestamps"),
        required_history_lookback=1,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            key: {
                "type": "int",
                "values": [h * 100 + m for h in range(24) for m in (0, 30)],
                "default": 0,
            }
            for key in ("time_from", "time_to")
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    time_from: int = Field(
        default=0,
        ge=0,
        le=2359,
        title="Time from",
        description="Start of the daily calculation window in HHMM format",
    )

    time_to: int = Field(
        default=0,
        ge=0,
        le=2359,
        title="Time to",
        description="End of the daily calculation window in HHMM format",
    )

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

    # Parameter validation: only relationships and custom constraints.
    _validate_time = field_validator("time_from", "time_to")(validate_hhmm)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Validate chart calendar at configuration time."""
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("Unknown chart timezone") from exc
        return value

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
        """Replay completed windows without including the bar at the end boundary."""
        logger.debug(
            "FR-indicator-calculation: HighestInRange requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        bars.require_inputs(("high",))
        values = time_window_extreme(
            bars.timestamps,
            bars.high,
            time_from=self.time_from,
            time_to=self.time_to,
            highest=True,
            timestamp_unit=self.timestamp_unit,
            timezone=self.timezone,
        )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated HighestInRange for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="HighestInRange")}


# Public exports.
__all__ = ["HighestInRange"]
