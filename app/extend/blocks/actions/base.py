"""Foundational action records and constants for trading action blocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Constant matching SQX undefined order/level status (Order.NOT_DEFINED = -9.9999999E7)
ORDER_NOT_DEFINED: float = -99_999_999.0


@dataclass(frozen=True)
class ActionRecord:
    """Immutable audit record representing an executed action descriptor."""

    action_type: str
    params: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


__all__ = ["ORDER_NOT_DEFINED", "ActionRecord"]
