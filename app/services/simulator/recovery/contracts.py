"""Canonical replay identity and recovery checkpoint contracts."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReplayIdentity(BaseModel):
    """Canonical Simulator replay identity version 1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulator.replay_identity.v1"] = "simulator.replay_identity.v1"
    replay_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=100)
    scenario_id: str = Field(min_length=1, max_length=100)
    scenario_version: str = Field(min_length=1, max_length=50)
    scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_ref: str = Field(min_length=1, max_length=500)
    data_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_profile_id: str = Field(min_length=1, max_length=100)
    execution_profile_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rules_version: str = Field(min_length=1, max_length=50)
    seed: int = Field(ge=0)
    parent_replay_id: str | None = Field(default=None, max_length=100)
    branch_point_sequence: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_branch(self) -> ReplayIdentity:
        """Require parent and branch sequence to appear together."""
        if (self.parent_replay_id is None) != (self.branch_point_sequence is None):
            raise ValueError("branch lineage requires both parent and sequence")
        return self


class RecoveryCheckpoint(BaseModel):
    """Immutable hash-linked secured-session recovery checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str = Field(min_length=1, max_length=100)
    sequence: int = Field(ge=0)
    checkpoint_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    replay_identity: ReplayIdentity
    state_payload: Mapping[str, Any]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        """Require an aware checkpoint timestamp."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("checkpoint timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _validate_origin(self) -> RecoveryCheckpoint:
        """Require sequence zero to be the only unhashed origin."""
        if (self.sequence == 0) != (self.previous_hash is None):
            raise ValueError("checkpoint origin/hash linkage is invalid")
        return self


__all__ = ["RecoveryCheckpoint", "ReplayIdentity"]
