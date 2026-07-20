"""Canonical position state for risk processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PositionState:
    """Normalized active position data used by the risk subsystem."""

    symbol: str
    lots: float
    side: str = "LONG"
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    strategy_id: str | None = None
    cluster: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
