"""Immutable contracts for current market schedules and session windows."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import field_validator, model_validator

from app.services.data.contracts._base import TracedOpenContract
from app.services.data.time_sessions.utc import require_utc


def _text(value: str) -> str:
    """Validate one required trimmed text value."""
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


class ScheduleRequest(TracedOpenContract):
    """Request for a source's current configured hours or sessions."""

    source_id: str
    symbol: str
    view: Literal["hours", "sessions"]
    timezone: str
    request_id: str

    @field_validator("source_id", "symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate a required request field."""
        return _text(value)


class SessionWindow(TracedOpenContract):
    """Named UTC session interval."""

    label: str
    opens_at: datetime
    closes_at: datetime

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        """Validate the session label."""
        return _text(value)

    @field_validator("opens_at", "closes_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one session boundary as aware UTC."""
        return require_utc(value)

    @model_validator(mode="after")
    def _validate_window(self) -> SessionWindow:
        """Validate that the session opens before it closes."""
        if self.opens_at >= self.closes_at:
            raise ValueError("opens_at must precede closes_at")
        return self


class MarketSchedule(TracedOpenContract):
    """Current configured market hours and normalized UTC sessions."""

    source_id: str
    symbol: str
    timezone: str
    hours: tuple[SessionWindow, ...]
    sessions: tuple[SessionWindow, ...]
    observed_at: datetime
    request_id: str

    @field_validator("source_id", "symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required schedule field."""
        return _text(value)

    @field_validator("observed_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the schedule observation time as aware UTC."""
        return require_utc(value)

    @field_validator("hours", "sessions")
    @classmethod
    def _validate_order(
        cls, value: tuple[SessionWindow, ...]
    ) -> tuple[SessionWindow, ...]:
        """Validate deterministic session ordering."""
        if value != tuple(sorted(value, key=lambda window: window.opens_at)):
            raise ValueError("schedule windows must be ordered by opens_at")
        return value


__all__ = ["MarketSchedule", "ScheduleRequest", "SessionWindow"]
