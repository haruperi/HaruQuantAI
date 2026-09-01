"""Bounded market, synthetic, availability, schedule, and volume requests."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import (
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger
from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord

logger = get_logger(__name__)

type WorkflowContext = Literal[
    "research", "backtest", "validation", "risk", "execution_bound"
]
type PrecisionPolicy = Literal[
    "decimal_string",
    "float_research_only",
    "source_native_decimal",
    "reject_on_missing_metadata",
]
type QualityFailureBehavior = Literal["reject", "warn"]
type DataKind = Literal["bars", "ticks", "spreads", "volume"]
type CanonicalRecord = OHLCVRecord | TickRecord | SpreadRecord


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


def _unique_texts(values: tuple[str, ...]) -> tuple[str, ...]:
    """Execute one private DATA operation.

    Args:
        values: The ``values`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the operation cannot be completed safely.
    """
    logger.debug("Running DATA function: _unique_texts")
    validated = tuple(_text(value) for value in values)
    if len(set(validated)) != len(validated):
        raise ValueError("values must be unique")
    return validated


class MarketDataRequest(_Contract):
    """Typed bounded market-data retrieval request."""

    source_id: str
    symbol: str
    data_kind: Literal["bars", "ticks", "spreads"]
    timeframe: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int
    use_cache: bool
    cache_ttl_seconds: int | None = None
    quality_failure_behavior: QualityFailureBehavior
    workflow_context: WorkflowContext
    precision_policy: PrecisionPolicy
    stale_cache_policy: Literal["refresh", "fail_closed", "serve_stale"] = "refresh"
    fallback_sources: tuple[str, ...] = ()
    source_timezone: str | None = None
    request_id: str

    @field_validator("source_id", "symbol", "request_id")
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

    @field_validator("timeframe", "source_timezone")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_optional_text")
        return _optional_text(value)

    @field_validator("start", "end")
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

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_limit")
        if value <= 0:
            raise ValueError("limit must be positive")
        return value

    @field_validator("cache_ttl_seconds")
    @classmethod
    def _validate_ttl(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_ttl")
        if value is not None and value < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        return value

    @field_validator("fallback_sources")
    @classmethod
    def _validate_fallbacks(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_fallbacks")
        return _unique_texts(value)

    @model_validator(mode="after")
    def _validate_request(self) -> MarketDataRequest:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_request")
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be supplied together")
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bar requests require timeframe")
        if self.source_id in self.fallback_sources:
            raise ValueError("fallback_sources must not repeat source_id")
        if (
            self.stale_cache_policy == "serve_stale"
            and self.workflow_context != "research"
        ):
            raise ValueError("serve_stale is restricted to the research context")
        if (
            self.workflow_context != "research"
            and self.precision_policy == "float_research_only"
        ):
            raise ValueError("float research precision is restricted to research")
        return self


__all__ = [
    "AvailabilityRequest",
    "MarketDataRequest",
    "VolumeRequest",
]


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

    @field_validator("start", "end")
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

    @field_validator("max_probe_records")
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
            raise ValueError("max_probe_records must be positive")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> AvailabilityRequest:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_request")
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be supplied together")
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "ohlcv" and self.timeframe is None:
            raise ValueError("OHLCV availability requires a timeframe")
        return self


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
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("start", "end")
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

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate one DATA value or contract invariant.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_limit")
        if value <= 0:
            raise ValueError("limit must be positive")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> VolumeRequest:
        """Validate one DATA value or contract invariant.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
