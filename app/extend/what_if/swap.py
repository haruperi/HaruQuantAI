"""Add hypothetical monetary rollover charges."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, time, timedelta
from typing import ClassVar, override
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator

from .base import (
    BaseWhatIf,
    WhatIfRecord,
    local_open,
    replace_record,
    validate_timezone,
)


class Swap(BaseWhatIf):
    """Add hypothetical monetary rollover charges."""

    name: ClassVar[str] = "Add hypothetical monetary rollover charges"
    swap_long: float = Field(default=10.0, ge=-1000, le=1000)
    swap_short: float = Field(default=-10.0, ge=-1000, le=1000)
    timezone: str = "UTC"
    rollover_hour: int = Field(default=23, ge=0, le=23)
    rollover_minute: int = Field(default=0, ge=0, le=59)
    triple_swap_day: int = Field(default=3, ge=1, le=7)

    _timezone = field_validator("timezone")(validate_timezone)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        result = []
        zone = ZoneInfo(self.timezone)
        for trade in trades:
            if trade.kind != "trade":
                result.append(trade)
                continue
            day = local_open(trade, self.timezone).date()
            end = datetime.fromtimestamp(trade.time_close_msc / 1000, zone).date()
            units = 0
            while day <= end:
                rollover = (
                    datetime.combine(
                        day, time(self.rollover_hour, self.rollover_minute), zone
                    ).timestamp()
                    * 1000
                )
                if trade.time_open_msc < rollover <= trade.time_close_msc:
                    units += 3 if day.isoweekday() == self.triple_swap_day else 1
                day += timedelta(days=1)
            rate = self.swap_long if trade.direction == 1 else self.swap_short
            result.append(
                replace_record(trade, swap=trade.swap + rate * trade.volume * units)
            )
        return result
