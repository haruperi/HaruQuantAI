"""Canonical market data state for risk processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MarketState:
    """Normalized market slice for one symbol and timeframe."""

    symbol: str
    timeframe: str
    bars: pd.DataFrame
    as_of: pd.Timestamp | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return int(len(self.bars))

    @property
    def last_close(self) -> float | None:
        if self.bars.empty:
            return None

        close_col = "close" if "close" in self.bars.columns else "Close"
        if close_col not in self.bars.columns:
            return None
        return float(self.bars[close_col].iloc[-1])
