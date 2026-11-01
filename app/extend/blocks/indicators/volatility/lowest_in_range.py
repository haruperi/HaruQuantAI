"""LowestInRange numeric indicator block from the donor range family."""

from __future__ import annotations

from typing import ClassVar, Literal, override

from pydantic import Field, field_validator

from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.include.calculators.extrema import time_window_extreme, validate_hhmm


class LowestInRange(BaseIndicator):
    """Completed daily HHMM-window extreme with explicit chart time context."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.lowest_in_range",
        name="LowestInRange",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=tuple(
            InputPort(key, PortType.SERIES, required=True)
            for key in ("low", "timestamps")
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("low", "timestamps"),
        is_causal=True,
        is_generation_eligible=True,
        parameter_search_space={
            key: {
                "type": "int",
                "values": [h * 100 + m for h in range(24) for m in (0, 30)],
                "default": 0,
            }
            for key in ("time_from", "time_to")
        },
        required_history_lookback=1,
    )
    time_from: int = Field(default=0, ge=0, le=2359)
    time_to: int = Field(default=0, ge=0, le=2359)
    timestamp_unit: Literal["seconds", "milliseconds"] = "seconds"
    timezone: str = "UTC"
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

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Replay completed windows without including the bar at the end boundary."""
        bars.require_inputs(("low",))
        values = time_window_extreme(
            bars.timestamps,
            bars.low,
            time_from=self.time_from,
            time_to=self.time_to,
            highest=False,
            timestamp_unit=self.timestamp_unit,
            timezone=self.timezone,
        )
        return {"value": IndicatorSeries(values, name="LowestInRange")}
