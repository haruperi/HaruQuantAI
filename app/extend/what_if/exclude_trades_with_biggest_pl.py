"""Exclude trades with biggest profit."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from pydantic import Field

from .base import BaseWhatIf, WhatIfRecord, exclude_ranked


class ExcludeTradesWithBiggestPl(BaseWhatIf):
    """Exclude trades with biggest profit."""

    name: ClassVar[str] = "Exclude trades with biggest profit"
    trades: int = Field(default=2, ge=1, le=10000)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        count = self.trades
        return exclude_ranked(trades, count, lowest=False, include_pending=True)
