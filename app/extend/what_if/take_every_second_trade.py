"""Keep the first and every other completed trade."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from .base import BaseWhatIf, WhatIfRecord


class TakeEverySecondTrade(BaseWhatIf):
    """Keep the first and every other completed trade."""

    name: ClassVar[str] = "Keep the first and every other completed trade"

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        result = []
        keep = True
        for trade in sorted(trades, key=lambda t: t.time_open_msc):
            if trade.kind != "trade":
                result.append(trade)
                continue
            if keep:
                result.append(trade)
            keep = not keep
        return result
