"""Exclude percentage of trades with lowest profit."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import ClassVar, override

from pydantic import Field

from .base import BaseWhatIf, WhatIfRecord, exclude_ranked


class ExcludePctTradesWithLowestPl(BaseWhatIf):
    """Exclude percentage of trades with lowest profit."""

    name: ClassVar[str] = "Exclude percentage of trades with lowest profit"
    trades_pct: int = Field(default=5, ge=1, le=100)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        count = ceil(sum(t.kind == "trade" for t in trades) * self.trades_pct / 100)
        return exclude_ranked(trades, count, lowest=True, include_pending=False)
