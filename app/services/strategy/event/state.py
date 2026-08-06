"""Internal model for Strategy runtime state persistence."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _StrategyRuntimeState(BaseModel):
    """Internal model representing current evaluator-local state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    config_id: str = Field(..., min_length=1)
    state_version: int = Field(..., ge=0)
    evaluation_status: Literal[
        "initialized",
        "ready",
        "evaluating",
        "halted",
        "error",
    ]
    bars_processed: int = Field(..., ge=0)
    last_evidence_at: datetime | None = None
    last_signal_id: str | None = None
    local_state: Mapping[str, Any]
    local_state_hash: str = Field(..., min_length=64, max_length=64)
    request_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    created_at: datetime
    updated_at: datetime


__all__: list[str] = []
