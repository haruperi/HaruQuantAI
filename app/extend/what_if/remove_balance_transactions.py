"""Remove balance transactions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from .base import BaseWhatIf, WhatIfRecord


class RemoveBalanceTransactions(BaseWhatIf):
    """Remove balance transactions."""

    name: ClassVar[str] = "Remove balance transactions"

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        return [t for t in trades if t.kind != "balance"]
