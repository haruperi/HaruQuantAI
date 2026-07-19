"""Immutable canonical market-record contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import logger


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _utc")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _finite(value: Decimal | None) -> Decimal | None:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _finite")
    if value is not None and not value.is_finite():
        raise ValueError("numeric value must be finite")
    return value


class _Record(BaseModel):
    """Private immutable canonical record behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    source: str
    source_symbol: str
    source_revision: str | None = None
    available_at: datetime

    @field_validator("timestamp", "available_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_timestamp")
        return _utc(value)

    @field_validator("source", "source_symbol", "source_revision")
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return None if value is None else _text(value)

    @model_validator(mode="after")
    def _validate_availability(self) -> _Record:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_availability")
        if self.available_at < self.timestamp:
            raise ValueError("available_at must not precede timestamp")
        return self


class OHLCVRecord(_Record):
    """Canonical UTC OHLCV record with optional exact spread evidence."""

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    price_unit: str
    volume_unit: str
    spread: Decimal | None = None
    spread_unit: str | None = None

    @field_validator("open", "high", "low", "close", "volume")
    @classmethod
    def _validate_numeric(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        validated = _finite(value)
        if validated is None:
            raise ValueError("numeric value is required")
        return validated

    @field_validator("spread")
    @classmethod
    def _validate_optional_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate optional spread evidence.

        Returns:
            The exact finite spread, or None when the provider supplied none.
        """
        logger.debug("Running DATA function: _validate_optional_numeric")
        return _finite(value)

    @field_validator("price_unit", "volume_unit", "spread_unit")
    @classmethod
    def _validate_unit(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_unit")
        return None if value is None else _text(value)

    @model_validator(mode="after")
    def _validate_ohlcv(self) -> OHLCVRecord:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_ohlcv")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")
        if self.spread is not None and self.spread < 0:
            raise ValueError("spread must be non-negative")
        if (self.spread is None) != (self.spread_unit is None):
            raise ValueError("spread and spread_unit must be provided together")
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        if not self.low <= self.open <= self.high:
            raise ValueError("open must be within the low/high range")
        if not self.low <= self.close <= self.high:
            raise ValueError("close must be within the low/high range")
        return self

    @field_serializer(
        "open",
        "high",
        "low",
        "close",
        "volume",
        "spread",
        when_used="json",
    )
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_decimal")
        return None if value is None else str(value)


class TickRecord(_Record):
    """Canonical UTC tick record preserving genuine quote sides.

    The optional ``source_bar_time``, ``tick_index_in_bar``, and ``bar_phase``
    fields carry intra-bar position evidence for ticks derived from bars. They
    default to ``None`` for provider-sourced ticks. ``bar_phase`` is a 4-bit mask
    of open (1), high (2), low (4), and close (8) observations within the source
    bar and carries no trading meaning.
    """

    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    volume: Decimal | None = None
    price_unit: str
    volume_unit: str | None = None
    source_bar_time: datetime | None = None
    tick_index_in_bar: int | None = None
    bar_phase: int | None = None

    @field_validator("bid", "ask", "last", "volume")
    @classmethod
    def _validate_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        return _finite(value)

    @field_validator("source_bar_time")
    @classmethod
    def _validate_source_bar_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_source_bar_time")
        return None if value is None else _utc(value)

    @field_validator("tick_index_in_bar")
    @classmethod
    def _validate_tick_index(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_tick_index")
        if value is not None and value < 0:
            raise ValueError("tick_index_in_bar must be non-negative")
        return value

    @field_validator("bar_phase")
    @classmethod
    def _validate_bar_phase(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_bar_phase")
        if value is not None and not 0 <= value <= 15:  # noqa: PLR2004
            raise ValueError("bar_phase must be a 4-bit open/high/low/close mask")
        return value

    @field_validator("price_unit", "volume_unit")
    @classmethod
    def _validate_unit(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_unit")
        return None if value is None else _text(value)

    @model_validator(mode="after")
    def _validate_tick(self) -> TickRecord:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_tick")
        if self.bid is None and self.ask is None and self.last is None:
            raise ValueError("at least one genuine price must be present")
        if self.bid is not None and self.ask is not None and self.ask < self.bid:
            raise ValueError("ask must not be below bid")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume must be non-negative")
        if self.volume is not None and self.volume_unit is None:
            raise ValueError("volume_unit is required when volume is present")
        return self

    @field_serializer("bid", "ask", "last", "volume", when_used="json")
    def _serialize_optional_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_optional_decimal")
        return None if value is None else str(value)


class SpreadRecord(_Record):
    """Canonical UTC spread record with explicit unit and scale."""

    spread: Decimal
    unit: str
    scale: int

    @field_validator("spread")
    @classmethod
    def _validate_spread(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_spread")
        validated = _finite(value)
        if validated is None:
            raise ValueError("spread is required")
        if validated < 0:
            raise ValueError("spread must be non-negative")
        return validated

    @field_validator("unit")
    @classmethod
    def _validate_unit(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_unit")
        return _text(value)

    @field_validator("scale")
    @classmethod
    def _validate_scale(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_scale")
        if value < 0:
            raise ValueError("scale must be non-negative")
        return value

    @field_serializer("spread", when_used="json")
    def _serialize_spread(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_spread")
        return str(value)


__all__ = ["OHLCVRecord", "SpreadRecord", "TickRecord"]
