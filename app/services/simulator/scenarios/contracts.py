"""Validated scenario-engine contracts."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.simulator.realism.random_streams import sample, serialize

_FAULT_TYPES = frozenset(
    {
        "timeout",
        "ambiguous_response",
        "rate_limit",
        "malformed_success",
        "disconnect",
        "reconnect",
        "stale_delivery",
        "gapped_delivery",
        "duplicate_delivery",
        "late_delivery",
        "out_of_order_delivery",
    }
)
_SHA256_LENGTH = 64


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


def build_seeded_fault_event(
    *,
    stream: object,
    fault_type: str,
    probability: Decimal,
    occurred_at: datetime,
    artifact_checksum: str,
) -> InjectedEvent | None:
    """Create a seeded transport/delivery/lifecycle fault in the scenario engine.

    Args:
        stream: Concern-specific deterministic fault stream.
        fault_type: Registered fault vocabulary.
        probability: Exact occurrence probability in ``[0, 1]``.
        occurred_at: Aware causal/effective/venue/perception instant.
        artifact_checksum: Exact calibration artifact identity.

    Returns:
        Injected fault or ``None`` when the deterministic draw does not trigger.

    Raises:
        ValueError: If fault type, probability, or artifact identity is invalid.
    """
    if fault_type not in _FAULT_TYPES:
        raise ValueError("fault type is not scenario-owned")
    if not probability.is_finite() or probability < 0 or probability > 1:
        raise ValueError("fault probability must be in [0, 1]")
    if (
        len(artifact_checksum) != _SHA256_LENGTH
        or artifact_checksum != artifact_checksum.lower()
        or any(character not in "0123456789abcdef" for character in artifact_checksum)
    ):
        raise ValueError("fault calibration checksum is invalid")
    draw = sample(stream)
    if draw >= probability:
        return None
    state = serialize(stream)
    return InjectedEvent(
        event_id=f"fault-{fault_type}-{state['counter']}",
        event_type=fault_type,
        priority=9_000,
        causative_at=occurred_at,
        effective_at=occurred_at,
        venue_at=occurred_at,
        perceived_at=occurred_at,
        suspends_normal_transitions=True,
        payload={
            "artifact_checksum": artifact_checksum,
            "stream_id": state["stream_id"],
            "stream_counter": state["counter"],
            "draw": str(draw),
            "journal_event_type": "seeded_scenario_fault",
        },
    )


__all__ = [
    "InjectedEvent",
    "MissionDefinition",
    "build_injected_event",
    "build_mission_definition",
    "build_seeded_fault_event",
]
