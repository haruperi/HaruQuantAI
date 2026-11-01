"""Remove pending orders."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from .base import BaseWhatIf, WhatIfRecord


class RemovePendingTrades(BaseWhatIf):
    """Remove pending orders."""

    name: ClassVar[str] = "Remove pending orders"

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        return [t for t in trades if t.kind != "pending"]
