"""Immutable contracts for current market schedules and session windows."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Literal

from pydantic import field_validator, model_validator

from app.services.data.contracts._base import FrozenContract, TracedOpenContract
from app.services.data.time_sessions.utc import _require_utc_raw as require_utc

_LAST_WEEKDAY = 6


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


class TradingSession(FrozenContract):
    """Venue-authoritative UTC trading interval."""

    symbol: str
    opens_at: datetime
    closes_at: datetime
    source: str
    label: str | None = None

    @field_validator("symbol", "source")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required session identity."""
        return _text(value)

    @field_validator("label")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate an optional session label."""
        return None if value is None else _text(value)

    @field_validator("opens_at", "closes_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one session boundary as aware UTC."""
        return require_utc(value)

    @model_validator(mode="after")
    def _validate_window(self) -> TradingSession:
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


class MarketHoursRequest(TracedOpenContract):
    """Request for current venue-authoritative market hours."""

    source_id: str
    symbol: str
    timezone: str = "UTC"
    request_id: str

    @field_validator("source_id", "symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required request field."""
        return _text(value)


class MarketHours(MarketSchedule):
    """Evaluated venue tradability derived from authoritative sessions.

    `halted`, `halt_reason`, and `reopen_at` (application Phase 0
    `feature`) default to the safe "no halt evidence supplied" state
    and are only ever set from genuine caller-supplied venue evidence (for
    example a Data-owned `halt`/`venue_state` stream event) through
    `apply_venue_halt`; this contract never infers a halt on its own.
    `close_window` and `roll_window` are likewise only populated from
    genuine caller-supplied schedule evidence.
    """

    is_open: bool
    checked_at: datetime
    current_session: SessionWindow | None
    next_session: SessionWindow | None
    halted: bool = False
    halt_reason: str | None = None
    reopen_at: datetime | None = None
    close_window: SessionWindow | None = None
    roll_window: SessionWindow | None = None

    @field_validator("checked_at")
    @classmethod
    def _validate_checked_at(cls, value: datetime) -> datetime:
        """Validate the evaluation time as aware UTC."""
        return require_utc(value)

    @field_validator("halt_reason")
    @classmethod
    def _validate_halt_reason(cls, value: str | None) -> str | None:
        """Validate an optional halt reason."""
        return None if value is None else _text(value)

    @field_validator("reopen_at")
    @classmethod
    def _validate_reopen_at(cls, value: datetime | None) -> datetime | None:
        """Validate an optional expected reopening time as aware UTC."""
        return None if value is None else require_utc(value)

    @model_validator(mode="after")
    def _validate_selection(self) -> MarketHours:
        """Validate deterministic current-session selection."""
        if self.is_open != (self.current_session is not None):
            raise ValueError("is_open must match current_session presence")
        if self.current_session is not None and not (
            self.current_session.opens_at
            <= self.checked_at
            < self.current_session.closes_at
        ):
            raise ValueError("current_session must contain checked_at")
        if (
            self.next_session is not None
            and self.next_session.opens_at <= self.checked_at
        ):
            raise ValueError("next_session must open after checked_at")
        if self.halted and self.is_open:
            raise ValueError("a halted venue cannot report is_open")
        if not self.halted and (
            self.halt_reason is not None or self.reopen_at is not None
        ):
            raise ValueError("halt_reason and reopen_at require halted=True")
        return self


class NamedSessionDefinition(FrozenContract):
    """Configurable analytical session expressed in one regional timezone."""

    name: str
    timezone: str
    opens_at: time
    closes_at: time

    @field_validator("name", "timezone")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate session identity."""
        return _text(value)


class ActiveMarketSessionsRequest(TracedOpenContract):
    """Request for analytical named sessions active at one instant."""

    symbol: str
    at: datetime
    request_id: str

    @field_validator("symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate request identity."""
        return _text(value)

    @field_validator("at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the evaluation time as aware UTC."""
        return require_utc(value)


class ActiveMarketSessions(TracedOpenContract):
    """Analytical session labels active at one instant."""

    symbol: str
    checked_at: datetime
    sessions: tuple[str, ...]
    request_id: str

    @field_validator("symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate result identity."""
        return _text(value)

    @field_validator("checked_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the evaluation time as aware UTC."""
        return require_utc(value)

    @field_validator("sessions")
    @classmethod
    def _validate_sessions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate unique deterministic label order."""
        if any(_text(item) != item for item in value) or len(set(value)) != len(value):
            raise ValueError("sessions must contain unique non-empty labels")
        return value


class WeeklyHoliday(FrozenContract):
    """Date override for an explicit configured weekly schedule."""

    date: date
    opens_at: time | None = None
    closes_at: time | None = None

    @model_validator(mode="after")
    def _validate_override(self) -> WeeklyHoliday:
        """Require both boundaries for a shortened day, or neither for closure."""
        if (self.opens_at is None) != (self.closes_at is None):
            raise ValueError("holiday boundaries must both be set or both be absent")
        return self


class WeeklyScheduleDefinition(FrozenContract):
    """Revisioned explicit weekly schedule used when no provider API exists."""

    source_id: str
    symbol: str
    timezone: str
    sessions: Mapping[int, tuple[tuple[time, time], ...]]
    effective_from: date
    effective_to: date | None = None
    holidays: tuple[WeeklyHoliday, ...] = ()
    revision: str

    @field_validator("source_id", "symbol", "timezone", "revision")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate schedule identity."""
        return _text(value)

    @model_validator(mode="after")
    def _validate_definition(self) -> WeeklyScheduleDefinition:
        """Validate weekday keys, effective bounds, and holiday uniqueness."""
        if any(day < 0 or day > _LAST_WEEKDAY for day in self.sessions):
            raise ValueError("weekly session keys must be Python weekdays 0 through 6")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        holiday_dates = tuple(item.date for item in self.holidays)
        if len(set(holiday_dates)) != len(holiday_dates):
            raise ValueError("holiday dates must be unique")
        return self


class ExchangeSessionRequest(TracedOpenContract):
    """Bounded exchange-calendar session request."""

    symbol: str
    calendar_code: str
    start: date
    end: date
    request_id: str

    @field_validator("symbol", "calendar_code", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate request identity."""
        return _text(value)

    @model_validator(mode="after")
    def _validate_range(self) -> ExchangeSessionRequest:
        """Validate the inclusive date range."""
        if self.start > self.end:
            raise ValueError("start must not follow end")
        return self


__all__ = [
    "ActiveMarketSessions",
    "ActiveMarketSessionsRequest",
    "ExchangeSessionRequest",
    "MarketHours",
    "MarketHoursRequest",
    "MarketSchedule",
    "NamedSessionDefinition",
    "ScheduleRequest",
    "SessionWindow",
    "TradingSession",
    "WeeklyHoliday",
    "WeeklyScheduleDefinition",
]
