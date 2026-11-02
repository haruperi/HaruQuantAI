"""Foundational action records and constants for trading action blocks.

Description:
    Provides core action execution data models, including immutable ActionRecord
    descriptors and StrategyQuant-compatible constants like ORDER_NOT_DEFINED.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-BASE-RECORD: Immutable action audit execution descriptor.
Python API Usage:
    from app.extend.blocks.actions.base import ORDER_NOT_DEFINED, ActionRecord
    rec = ActionRecord(action_type="custom", params={})
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

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
