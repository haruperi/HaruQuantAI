"""Limit daily trade entries."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import ClassVar, override

from pydantic import Field, field_validator

from .base import BaseWhatIf, WhatIfRecord, local_open, validate_timezone


class TakeMaxTradesPerDay(BaseWhatIf):
    """Limit daily trade entries."""

    name: ClassVar[str] = "Limit daily trade entries"
    trades: int = Field(default=2, ge=1, le=10000)
    timezone: str = "UTC"

    _timezone = field_validator("timezone")(validate_timezone)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        result = []
        counts: dict[date, int] = {}
        for trade in sorted(trades, key=lambda t: t.time_open_msc):
            if trade.kind == "balance":
                result.append(trade)
                continue
            day = local_open(trade, self.timezone).date()
            count = counts.get(day, 0)
            if count < self.trades:
                result.append(trade)
                counts[day] = count + 1
        return result
