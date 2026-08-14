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
from app.utils import get_logger

logger = get_logger(__name__)


def _text(value: str) -> str:
    """Execute one private DATA operation.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the operation cannot be completed safely.
    """
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _optional_text(value: str | None) -> str | None:
    """Execute one private DATA operation.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Running DATA function: _optional_text")
    return None if value is None else _text(value)


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the operation cannot be completed safely.
    """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_non_negative")
        if value < 0:
            raise ValueError("reconnect policy values must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_policy(self) -> ReconnectPolicy:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_timeframe")
        return _optional_text(value)

    @field_validator("buffer_capacity", "heartbeat_timeout_seconds")
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_bound")
        if value <= 0:
            raise ValueError("feed bounds must be positive")
        return value

    @model_validator(mode="after")
    def _validate_config(self) -> FeedConfig:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_sequence")
        if value < 0:
            raise ValueError("sequence must be non-negative")
        return value

    @field_validator("event_timestamp", "received_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("payload", mode="after")
    @classmethod
    def _freeze_payload(
        cls, value: Mapping[str, None | bool | int | float | str]
    ) -> Mapping[str, None | bool | int | float | str]:
        """Freeze one DATA contract value against mutation.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _freeze_payload")
        frozen = MappingProxyType({_text(key): item for key, item in value.items()})
        if not frozen:
            raise ValueError("payload must not be empty")
        return frozen

    @field_serializer("payload", when_used="json")
    def _serialize_payload(
        self, value: Mapping[str, None | bool | int | float | str]
    ) -> dict[str, None | bool | int | float | str]:
        """Serialize one DATA contract value deterministically.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _serialize_payload")
        return dict(value)

    @model_validator(mode="after")
    def _validate_event(self) -> RawFeedEvent:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("sequence", "buffer_depth", "dropped_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("feed event counters must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_result(self) -> FeedEventResult:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("last_error")
    @classmethod
    def _validate_error(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_error")
        return _optional_text(value)

    @field_validator("heartbeat_at", "last_event_at")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("feed status counters must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_status(self) -> FeedStatus:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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


class MarketStreamRequest(_Contract):
    """Bounded request for one Data-owned real-time market stream."""

    source_id: str
    symbol: str
    mode: Literal["ticks"]
    timeframe: str
    request_id: str
    resume_after: int | None = None

    @field_validator("source_id", "symbol", "timeframe", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required stream identifier.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)

    @field_validator("resume_after")
    @classmethod
    def _validate_resume_after(cls, value: int | None) -> int | None:
        """Validate an optional last-observed sequence.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-negative sequence or ``None``.

        Raises:
            ValueError: If the sequence is negative.
        """
        if value is not None and value < 0:
            raise ValueError("resume_after must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_mt5_request(self) -> MarketStreamRequest:
        """Restrict the first released stream source to MT5.

        Returns:
            Validated MT5 request.

        Raises:
            ValueError: If another source is requested.
        """
        if self.source_id != "mt5":
            raise ValueError("the initial market stream source must be mt5")
        return self


class TradePayload(_Contract):
    """Single executed-trade print for the`trade` market event family."""

    price: float
    size: float
    side: Literal["buy", "sell", "unknown"]
    trade_id: str

    @field_validator("trade_id")
    @classmethod
    def _validate_trade_id(cls, value: str) -> str:
        """Validate the required trade identifier.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed trade identifier.
        """
        return _text(value)

    @field_validator("price", "size")
    @classmethod
    def _validate_positive(cls, value: float) -> float:
        """Validate a required positive trade magnitude.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated positive value.

        Raises:
            ValueError: If the value is not strictly positive.
        """
        if value <= 0:
            raise ValueError("trade price and size must be positive")
        return value


class DepthUpdatePayload(_Contract):
    """Book-level bid/ask update for the`depth` market event family."""

    side: Literal["bid", "ask"]
    level: int
    price: float
    size: float

    @field_validator("level")
    @classmethod
    def _validate_level(cls, value: int) -> int:
        """Validate the required non-negative book level.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated non-negative level.

        Raises:
            ValueError: If the level is negative.
        """
        if value < 0:
            raise ValueError("depth level must be non-negative")
        return value

    @field_validator("price", "size")
    @classmethod
    def _validate_non_negative(cls, value: float) -> float:
        """Validate a required non-negative depth magnitude.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated non-negative value.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError("depth price and size must be non-negative")
        return value


class VenueStatePayload(_Contract):
    """Venue trading-state transition for the`venue_state` event family."""

    state: Literal["open", "closed", "pre_open", "pre_close", "auction", "halted"]
    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str | None) -> str | None:
        """Validate an optional venue-state reason.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed reason or ``None``.
        """
        return _optional_text(value)


class HaltPayload(_Contract):
    """Trading halt for the`halt` market event family."""

    reason: str
    resumes_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        """Validate the required halt reason.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed reason.
        """
        return _text(value)

    @field_validator("resumes_at")
    @classmethod
    def _validate_resumes_at(cls, value: datetime | None) -> datetime | None:
        """Validate an optional expected resumption time as aware UTC.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated timestamp or ``None``.
        """
        return None if value is None else _utc(value)


class AuctionPayload(_Contract):
    """Opening/closing auction state for the`auction` event family."""

    reference_price: float
    matched_size: float
    imbalance: float

    @field_validator("reference_price", "matched_size")
    @classmethod
    def _validate_non_negative(cls, value: float) -> float:
        """Validate a required non-negative auction magnitude.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated non-negative value.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(
                "auction reference price and matched size must be non-negative"
            )
        return value


class CorporateActionPayload(_Contract):
    """Corporate-action notice for the`corporate_action` event family."""

    action_type: Literal["split", "dividend", "merger", "symbol_change"]
    effective_date: datetime
    ratio: float | None = None

    @field_validator("effective_date")
    @classmethod
    def _validate_effective_date(cls, value: datetime) -> datetime:
        """Validate the effective date as aware UTC.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated timestamp.
        """
        return _utc(value)

    @field_validator("ratio")
    @classmethod
    def _validate_ratio(cls, value: float | None) -> float | None:
        """Validate an optional required-positive corporate-action ratio.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated positive ratio or ``None``.

        Raises:
            ValueError: If the ratio is not strictly positive.
        """
        if value is not None and value <= 0:
            raise ValueError("corporate action ratio must be positive")
        return value


_MARKET_PAYLOAD_EVENT_TYPES = frozenset(
    {
        "tick",
        "bar",
        "trade",
        "depth",
        "venue_state",
        "halt",
        "auction",
        "corporate_action",
    }
)

_TYPED_PAYLOAD_CLASSES: Mapping[str, type[_Contract]] = MappingProxyType(
    {
        "trade": TradePayload,
        "depth": DepthUpdatePayload,
        "venue_state": VenueStatePayload,
        "halt": HaltPayload,
        "auction": AuctionPayload,
        "corporate_action": CorporateActionPayload,
    }
)


class MarketStreamEvent(_Contract):
    """Ordered canonical event emitted by a Data-owned market stream."""

    feed_id: str
    sequence: int
    event_type: Literal[
        "tick",
        "bar",
        "trade",
        "depth",
        "venue_state",
        "halt",
        "auction",
        "corporate_action",
        "heartbeat",
        "gap",
        "error",
    ]
    mode: Literal["ticks"]
    source_id: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    payload: object | None = None
    cursor: str
    error: str | None = None
    terminal: bool = False
    request_id: str

    @field_validator(
        "feed_id",
        "source_id",
        "symbol",
        "timeframe",
        "cursor",
        "request_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required event identifier.

        Args:
            value: The ``value`` argument.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate one non-negative stream sequence.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated sequence.

        Raises:
            ValueError: If the sequence is negative.
        """
        if value < 0:
            raise ValueError("stream sequence must be non-negative")
        return value

    @field_validator("occurred_at")
    @classmethod
    def _validate_occurred_at(cls, value: datetime) -> datetime:
        """Validate the event time as aware UTC.

        Args:
            value: The ``value`` argument.

        Returns:
            Validated timestamp.
        """
        return _utc(value)

    @model_validator(mode="after")
    def _validate_event_shape(self) -> MarketStreamEvent:
        """Validate payload and terminal-error invariants.

        Returns:
            Validated event.

        Raises:
            ValueError: If the event family has an inconsistent shape.
        """
        if self.event_type in _MARKET_PAYLOAD_EVENT_TYPES and self.payload is None:
            raise ValueError("market payload events require payload")
        if (
            self.event_type in {"heartbeat", "gap", "error"}
            and self.payload is not None
        ):
            raise ValueError("control stream events cannot include payload")
        typed_payload_class = _TYPED_PAYLOAD_CLASSES.get(self.event_type)
        if typed_payload_class is not None and not isinstance(
            self.payload, typed_payload_class
        ):
            message = (
                f"{self.event_type} events require a "
                f"{typed_payload_class.__name__} payload"
            )
            raise ValueError(message)
        if self.event_type in {"gap", "error"} and self.error is None:
            raise ValueError("gap and error events require an error code")
        if self.event_type not in {"gap", "error"} and self.error is not None:
            raise ValueError("only gap and error events may include an error code")
        if self.terminal and self.event_type not in {"gap", "error"}:
            raise ValueError("only gap and error events may be terminal")
        return self


__all__ = [
    "AuctionPayload",
    "CorporateActionPayload",
    "DepthUpdatePayload",
    "FeedConfig",
    "FeedEventResult",
    "FeedStatus",
    "FeedStatusRequest",
    "HaltPayload",
    "MarketStreamEvent",
    "MarketStreamRequest",
    "RawFeedEvent",
    "ReconnectPolicy",
    "TradePayload",
    "VenueStatePayload",
]
