"""Exclude overlapping trades."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from .base import BaseWhatIf, WhatIfRecord


class ExcludeOverlappingTrades(BaseWhatIf):
    """Exclude overlapping trades."""

    name: ClassVar[str] = "Exclude overlapping trades"

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        result = []
        close_time: int | None = None
        for trade in sorted(trades, key=lambda t: t.time_open_msc):
            if close_time is None or trade.time_open_msc > close_time:
                result.append(trade)
                close_time = trade.time_close_msc
        return result
