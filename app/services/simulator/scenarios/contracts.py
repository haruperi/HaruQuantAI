"""Validated scenario-engine contracts."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InjectedEvent(BaseModel):
    """One immutable simulated event with explicit timing and priority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    priority: int = Field(ge=0, le=10_000)
    causative_at: datetime
    effective_at: datetime
    venue_at: datetime
    perceived_at: datetime
    suspends_normal_transitions: bool = False
    payload: Mapping[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_timing(self) -> InjectedEvent:
        """Require aware, causal event timestamps."""
        timestamps = (
            self.causative_at,
            self.effective_at,
            self.venue_at,
            self.perceived_at,
        )
        if any(
            value.tzinfo is None or value.utcoffset() is None for value in timestamps
        ):
            raise ValueError("scenario timestamps must be timezone-aware")
        if (
            not self.causative_at
            <= self.effective_at
            <= self.venue_at
            <= self.perceived_at
        ):
            raise ValueError("scenario timestamps must preserve causality")
        return self


class MissionDefinition(BaseModel):
    """Simulator-owned blocking scenario and mission definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mission_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    market_data_ref: str = Field(min_length=1, max_length=500)
    difficulty: int = Field(ge=1, le=10)
    seed: int = Field(ge=0)
    triggers: tuple[Mapping[str, Any], ...] = Field(min_length=1, max_length=100)
    events: tuple[InjectedEvent, ...] = Field(min_length=1, max_length=100)
    competence_tags: tuple[str, ...] = ()

    @field_validator("triggers")
    @classmethod
    def _validate_triggers(
        cls, value: tuple[Mapping[str, Any], ...]
    ) -> tuple[Mapping[str, Any], ...]:
        """Validate the bounded trigger DSL at the contract boundary."""
        allowed = {
            "time",
            "price",
            "volatility",
            "liquidity",
            "player_action",
            "checklist",
            "account_state",
            "compound",
            "probability",
        }
        for trigger in value:
            trigger_type = trigger.get("type")
            if trigger_type not in allowed:
                raise ValueError("unsupported scenario trigger type")
            if not isinstance(trigger.get("trigger_id"), str):
                raise TypeError("scenario trigger requires trigger_id")
        return value


def build_mission_definition(**fields: object) -> MissionDefinition:
    """Build one validated mission definition.

    Args:
        **fields: Mission definition fields.

    Returns:
        Validated immutable mission definition.
    """
    return MissionDefinition.model_validate(fields)


def build_injected_event(**fields: object) -> InjectedEvent:
    """Build one validated injected event.

    Args:
        **fields: Injected-event fields.

    Returns:
        Validated immutable event.
    """
    return InjectedEvent.model_validate(fields)


__all__ = [
    "InjectedEvent",
    "MissionDefinition",
    "build_injected_event",
    "build_mission_definition",
]
