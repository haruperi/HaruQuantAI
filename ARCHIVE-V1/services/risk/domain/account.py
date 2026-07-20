"""Canonical account state for risk processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AccountState:
    """Normalized account inputs used by the risk subsystem."""

    equity: float
    balance: float | None = None
    free_margin: float | None = None
    margin_used: float | None = None
    currency: str | None = None
    account_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
