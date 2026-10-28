"""Recompute gross profit with fixed lots."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from pydantic import Field

from .base import BaseWhatIf, WhatIfRecord, replace_record


class UseFixedLots(BaseWhatIf):
    """Recompute gross profit with fixed lots."""

    name: ClassVar[str] = "Recompute gross profit with fixed lots"
    size: float = Field(default=0.1, ge=0.01, le=100)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        return [
            replace_record(t, volume=self.size, profit=t.profit / t.volume * self.size)
            if t.kind == "trade"
            else t
            for t in trades
        ]
