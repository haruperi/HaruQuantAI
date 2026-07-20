"""Canonical symbol specification state for risk processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SymbolState:
    """Normalized symbol specification snapshot used by risk math."""

    symbol: str
    contract_size: float | None = None
    tick_value: float | None = None
    tick_size: float | None = None
    volume_min: float | None = None
    volume_max: float | None = None
    volume_step: float | None = None
    currency_base: str | None = None
    currency_profit: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
