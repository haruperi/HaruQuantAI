"""Internal Strategy registry models and records."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _StrategyDefinition(BaseModel):
    """Internal model for strategy definition persistence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(..., min_length=1)
    evaluator_key: str = Field(..., min_length=1)
    strategy_code: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    strategy_class: Literal[
        "trend",
        "mean_reversion",
        "breakout",
        "structure",
        "hedging",
        "basket",
        "composite",
    ]
    owner_ref: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    lifecycle_status: Literal["active", "paused", "retired"]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class _StrategyConfigRecord(BaseModel):
    """Internal model for strategy configuration record persistence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    config_id: str = Field(..., min_length=1)
    version_id: str = Field(..., min_length=1)
    strategy_id: str = Field(..., min_length=1)
    strategy_version: str = Field(..., min_length=1)
    config_hash: str = Field(..., min_length=64, max_length=64)
    config_schema_version: str = Field(..., min_length=1)
    config_json: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    runtime_profile: Literal["RESEARCH", "SIMULATION", "DEMO", "LIVE"]
    lifecycle_status: Literal["active", "paused", "archived"]
    request_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    created_at: datetime


class _StrategyBootstrapSummary(BaseModel):
    """Internal model for bootstrap operation results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bootstrap_status: str = Field(..., min_length=1)
    registered_strategies: int = Field(..., ge=0)
    configured_strategies: int = Field(..., ge=0)
    descriptors: tuple[Mapping[str, Any], ...]


__all__: list[str] = []
