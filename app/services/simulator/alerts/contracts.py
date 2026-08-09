"""Immutable simulated alert contract."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AlertState = Literal[
    "INACTIVE",
    "ACTIVE_UNACKNOWLEDGED",
    "ACTIVE_ACKNOWLEDGED",
    "RESOLVED",
    "CLEARED",
]


class AlertEvent(BaseModel):
    """One immutable simulated-session alert projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    alert_id: str = Field(min_length=1, max_length=100)
    source_event_id: str = Field(min_length=1, max_length=100)
    root_cause_id: str = Field(min_length=1, max_length=100)
    severity: Literal["info", "warning", "error", "critical"]
    state: AlertState = "INACTIVE"
    first_observed_at: datetime
    perceived_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    cleared_at: datetime | None = None
    latched: bool = True
    details: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator(
        "first_observed_at",
        "perceived_at",
        "acknowledged_at",
        "resolved_at",
        "cleared_at",
    )
    @classmethod
    def _aware(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware alert evidence."""
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("alert timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _validate_causality(self) -> AlertEvent:
        """Validate perception and lifecycle timestamp causality."""
        if self.perceived_at < self.first_observed_at:
            raise ValueError("alert perception cannot precede observation")
        lifecycle = [
            value
            for value in (self.acknowledged_at, self.resolved_at, self.cleared_at)
            if value is not None
        ]
        if any(value < self.first_observed_at for value in lifecycle):
            raise ValueError("alert lifecycle evidence cannot precede observation")
        return self


def build_simulation_alert(**fields: object) -> AlertEvent:
    """Build one validated simulated alert."""
    return AlertEvent.model_validate(fields)


__all__ = ["AlertEvent", "build_simulation_alert"]
