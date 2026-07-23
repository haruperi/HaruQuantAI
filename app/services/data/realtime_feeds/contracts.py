"""Public bounded live-feed configuration, event, and status contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import (
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.utils import logger


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _optional_text(value: str | None) -> str | None:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _optional_text")
    return None if value is None else _text(value)


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _utc")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


class ReconnectPolicy(_Contract):
    """Bounded retry and circuit-cooldown policy."""

    max_retries: int
    initial_backoff_seconds: int
    max_backoff_seconds: int
    jitter_seconds: int
    circuit_cooldown_seconds: int

    @field_validator(
        "max_retries",
        "initial_backoff_seconds",
        "max_backoff_seconds",
        "jitter_seconds",
        "circuit_cooldown_seconds",
    )
    @classmethod
    def _validate_non_negative(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_non_negative")
        if value < 0:
            raise ValueError("reconnect policy values must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_policy(self) -> ReconnectPolicy:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_policy")
        if self.max_retries <= 0:
            raise ValueError("max_retries must be positive")
        if self.initial_backoff_seconds <= 0:
            raise ValueError("initial_backoff_seconds must be positive")
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds cannot be below initial backoff")
        if self.circuit_cooldown_seconds <= 0:
            raise ValueError("circuit_cooldown_seconds must be positive")
        return self


class FeedConfig(_Contract):
    """Internal feed configuration for a declared live-capable source."""

    feed_id: str
    source_id: str
    symbol: str
    data_kind: Literal["ohlcv", "tick", "spread"]
    timeframe: str | None = None
    source_capability: str
    buffer_capacity: int
    overflow_policy: Literal["halt", "drop_and_reconcile", "backpressure"]
    heartbeat_timeout_seconds: int
    reconnect_policy: ReconnectPolicy
    request_id: str

    @field_validator(
        "feed_id", "source_id", "symbol", "source_capability", "request_id"
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_timeframe")
        return _optional_text(value)

    @field_validator("buffer_capacity", "heartbeat_timeout_seconds")
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_bound")
        if value <= 0:
            raise ValueError("feed bounds must be positive")
        return value

    @model_validator(mode="after")
    def _validate_config(self) -> FeedConfig:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_config")
        if self.data_kind == "ohlcv" and self.timeframe is None:
            raise ValueError("OHLCV feeds require a timeframe")
        return self


class RawFeedEvent(_Contract):
    """Bounded provider-neutral raw event submitted to feed normalization."""

    feed_id: str
    sequence: int
    event_timestamp: datetime
    received_at: datetime
    payload: Mapping[str, None | bool | int | float | str]
    request_id: str

    @field_validator("feed_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_sequence")
        if value < 0:
            raise ValueError("sequence must be non-negative")
        return value

    @field_validator("event_timestamp", "received_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("payload", mode="after")
    @classmethod
    def _freeze_payload(
        cls, value: Mapping[str, None | bool | int | float | str]
    ) -> Mapping[str, None | bool | int | float | str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_payload")
        frozen = MappingProxyType({_text(key): item for key, item in value.items()})
        if not frozen:
            raise ValueError("payload must not be empty")
        return frozen

    @field_serializer("payload", when_used="json")
    def _serialize_payload(
        self, value: Mapping[str, None | bool | int | float | str]
    ) -> dict[str, None | bool | int | float | str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_payload")
        return dict(value)

    @model_validator(mode="after")
    def _validate_event(self) -> RawFeedEvent:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_event")
        if self.received_at < self.event_timestamp:
            raise ValueError("received_at cannot precede event_timestamp")
        return self


class FeedEventResult(_Contract):
    """Evidence that one event was accepted, dropped, or gap-recorded."""

    feed_id: str
    sequence: int
    accepted: bool
    buffer_depth: int
    gap_recorded: bool
    dropped_count: int
    request_id: str

    @field_validator("feed_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("sequence", "buffer_depth", "dropped_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("feed event counters must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_result(self) -> FeedEventResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if self.dropped_count > 0 and not self.gap_recorded:
            raise ValueError("dropped events require gap evidence")
        if not self.accepted and self.dropped_count == 0:
            raise ValueError("rejected events require a recorded drop")
        return self


class FeedStatusRequest(_Contract):
    """Request for one persisted feed's status evidence."""

    feed_id: str
    request_id: str

    @field_validator("feed_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class FeedStatus(_Contract):
    """Persisted heartbeat, buffer, gap, breaker, and error evidence."""

    feed_id: str
    source_id: str
    symbol: str
    data_kind: Literal["ohlcv", "tick", "spread"]
    state: Literal["starting", "running", "stopped", "failed", "blocked"]
    heartbeat_at: datetime | None = None
    last_event_at: datetime | None = None
    buffer_depth: int
    buffer_capacity: int
    dropped_count: int
    gap_count: int
    reconnect_count: int
    breaker_state: Literal["closed", "open", "half_open"]
    drift_ms: int | None = None
    last_error: str | None = None
    request_id: str

    @field_validator("feed_id", "source_id", "symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("last_error")
    @classmethod
    def _validate_error(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_error")
        return _optional_text(value)

    @field_validator("heartbeat_at", "last_event_at")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @field_validator(
        "buffer_depth",
        "buffer_capacity",
        "dropped_count",
        "gap_count",
        "reconnect_count",
    )
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("feed status counters must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_status(self) -> FeedStatus:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_status")
        if self.buffer_capacity <= 0 or self.buffer_depth > self.buffer_capacity:
            raise ValueError("buffer evidence is outside capacity")
        if self.dropped_count > 0 and self.gap_count <= 0:
            raise ValueError("dropped events require gap evidence")
        if self.state == "running" and self.heartbeat_at is None:
            raise ValueError("running status requires heartbeat evidence")
        if self.state in {"failed", "blocked"} and self.last_error is None:
            raise ValueError("failed status requires a safe last error")
        if self.breaker_state == "open" and self.last_error is None:
            raise ValueError("open breaker requires a safe last error")
        return self


__all__ = [
    "FeedConfig",
    "FeedEventResult",
    "FeedStatus",
    "FeedStatusRequest",
    "RawFeedEvent",
    "ReconnectPolicy",
]
