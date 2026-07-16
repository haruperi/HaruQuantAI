"""Availability, current-schedule, and historical-volume contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import (
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts._base import DataContractModel
from app.services.data.contracts._validation import validate_request_id
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


def _finite(value: Decimal) -> Decimal:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _finite")
    if not value.is_finite():
        raise ValueError("numeric value must be finite")
    return value


class _Contract(DataContractModel):
    """Private immutable reference-contract behavior."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class AvailabilityRequest(_Contract):
    """Bounded request for indexed availability evidence."""

    source_id: str
    symbol: str
    data_kind: Literal["ohlcv", "tick", "spread"]
    timeframe: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    max_probe_records: int
    request_id: str

    @field_validator("source_id", "symbol", "request_id")
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

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @field_validator("max_probe_records")
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_bound")
        if value <= 0:
            raise ValueError("max_probe_records must be positive")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> AvailabilityRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be supplied together")
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "ohlcv" and self.timeframe is None:
            raise ValueError("OHLCV availability requires a timeframe")
        return self


class ScheduleRequest(_Contract):
    """Request for a source's current configured hours or sessions."""

    source_id: str
    symbol: str
    view: Literal["hours", "sessions"]
    timezone: str
    request_id: str

    @field_validator("source_id", "symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class SessionWindow(_Contract):
    """Named UTC session interval."""

    label: str
    opens_at: datetime
    closes_at: datetime

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_label")
        return _text(value)

    @field_validator("opens_at", "closes_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_window(self) -> SessionWindow:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_window")
        if self.opens_at >= self.closes_at:
            raise ValueError("opens_at must precede closes_at")
        return self


class MarketSchedule(_Contract):
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
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("observed_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("hours", "sessions")
    @classmethod
    def _validate_order(
        cls, value: tuple[SessionWindow, ...]
    ) -> tuple[SessionWindow, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_order")
        if value != tuple(sorted(value, key=lambda window: window.opens_at)):
            raise ValueError("schedule windows must be ordered by opens_at")
        return value


class VolumeRequest(_Contract):
    """Bounded request for source-native or derived historical volume."""

    source_id: str
    symbol: str
    start: datetime
    end: datetime
    mode: Literal["records", "buckets", "summary"]
    bucket_seconds: int | None = None
    limit: int
    request_id: str

    @field_validator("source_id", "symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_limit")
        if value <= 0:
            raise ValueError("limit must be positive")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> VolumeRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if self.start >= self.end:
            raise ValueError("start must precede end")
        if self.mode == "buckets" and (
            self.bucket_seconds is None or self.bucket_seconds <= 0
        ):
            raise ValueError("bucket mode requires positive bucket_seconds")
        if self.mode != "buckets" and self.bucket_seconds is not None:
            raise ValueError("bucket_seconds is valid only for bucket mode")
        return self


class VolumeRecord(_Contract):
    """One exact historical-volume observation or bucket."""

    timestamp: datetime
    volume: Decimal

    @field_validator("timestamp")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("volume")
    @classmethod
    def _validate_volume(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_volume")
        validated = _finite(value)
        if validated < 0:
            raise ValueError("volume must be non-negative")
        return validated

    @field_serializer("volume", when_used="json")
    def _serialize_volume(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_volume")
        return str(value)


class VolumeSummary(_Contract):
    """Exact aggregate volume evidence."""

    total: Decimal
    average: Decimal
    minimum: Decimal
    maximum: Decimal
    record_count: int

    @field_validator("total", "average", "minimum", "maximum")
    @classmethod
    def _validate_volume(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_volume")
        validated = _finite(value)
        if validated < 0:
            raise ValueError("volume aggregates must be non-negative")
        return validated

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value <= 0:
            raise ValueError("record_count must be positive")
        return value

    @model_validator(mode="after")
    def _validate_summary(self) -> VolumeSummary:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_summary")
        if self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum")
        return self

    @field_serializer("total", "average", "minimum", "maximum", when_used="json")
    def _serialize_volume(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_volume")
        return str(value)


class VolumeResult(_Contract):
    """Bounded volume records or summary with provenance and units."""

    source_id: str
    symbol: str
    mode: Literal["records", "buckets", "summary"]
    volume_kind: str
    volume_unit: str
    records: tuple[VolumeRecord, ...]
    summary: VolumeSummary | None = None
    provenance: Mapping[str, str]
    truncated: bool
    request_id: str

    @field_validator("source_id", "symbol", "volume_kind", "volume_unit", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _freeze_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_provenance")
        frozen = MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )
        if not frozen:
            raise ValueError("provenance must not be empty")
        return frozen

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)

    @model_validator(mode="after")
    def _validate_result(self) -> VolumeResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if self.mode == "summary":
            if self.summary is None or self.records:
                raise ValueError("summary mode requires only summary evidence")
        elif self.summary is not None:
            raise ValueError("record and bucket modes cannot contain summary")
        if self.records != tuple(sorted(self.records, key=lambda item: item.timestamp)):
            raise ValueError("volume records must be timestamp ordered")
        return self


__all__ = [
    "AvailabilityRequest",
    "MarketSchedule",
    "ScheduleRequest",
    "SessionWindow",
    "VolumeRecord",
    "VolumeRequest",
    "VolumeResult",
    "VolumeSummary",
]
