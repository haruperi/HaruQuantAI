"""Exclude a percentage of short duration entries."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import ClassVar, override

from pydantic import Field

from .base import BaseWhatIf, WhatIfRecord


class ExcludeShortTrades(BaseWhatIf):
    """Exclude a percentage of short duration entries."""

    name: ClassVar[str] = "Exclude a percentage of short duration entries"
    trades_pct: int = Field(default=5, ge=1, le=100)
    minutes: int = Field(default=10, ge=1, le=100000)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        count = ceil(len(trades) * self.trades_pct / 100)
        removed = 0
        result = []
        for trade in trades:
            duration = (trade.time_close_msc - trade.time_open_msc) // 60000
            if trade.kind != "balance" and removed < count and duration < self.minutes:
                removed += 1
            else:
                result.append(trade)
        return result
