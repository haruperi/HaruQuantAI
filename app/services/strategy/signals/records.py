"""Internal model for durable Strategy signal records."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.services.strategy.contracts import StrategySignal


class _StrategySignalRecord(BaseModel):
    """Internal model for durable signal record persistence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    signal: StrategySignal
    config_id: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=0)
    intent_id: str | None = None
    publication_status: Literal[
        "generated",
        "submitted",
        "submission_failed",
        "expired_before_submission",
    ]
    risk_submission_ref: str | None = None
    request_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    created_at: datetime
    updated_at: datetime


__all__: list[str] = []
