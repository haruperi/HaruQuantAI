"""Immutable canonical tick used by the Simulation execution clock."""

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

_MAX_BAR_PHASE = 15


class Tick(BaseModel):
    """Canonical immutable UTC bid/ask tick with availability evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    source_id: str
    sequence: int
    available_at: datetime
    volume: Decimal | None = None
    volume_unit: str | None = None
    source_bar_time: datetime | None = None
    tick_index_in_bar: int | None = None
    bar_phase: int | None = None

    @field_validator("symbol", "source_id", "volume_unit")
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        """Validate required or optional trimmed text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating Simulation Tick text")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("Tick text must be non-empty and trimmed")
        return value

    @field_validator("timestamp", "available_at", "source_bar_time")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one optional aware UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If supplied time is not UTC.
        """
        logger.debug("Validating Simulation Tick timestamp")
        if value is not None and (
            value.tzinfo is None or value.utcoffset() != timedelta(0)
        ):
            raise ValueError("Tick timestamps must be aware UTC")
        return value

    @field_validator("bid", "ask", "volume")
    @classmethod
    def _validate_decimal(cls, value: Decimal | None, info: object) -> Decimal | None:
        """Validate finite positive price or non-negative volume.

        Args:
            value: Candidate Decimal.
            info: Pydantic field information.

        Returns:
            Validated Decimal.

        Raises:
            ValueError: If the value is non-finite or outside its range.
        """
        logger.debug("Validating Simulation Tick Decimal")
        if value is None:
            return None
        if not value.is_finite():
            raise ValueError("Tick Decimal must be finite")
        field_name = str(getattr(info, "field_name", "price"))
        if (field_name == "volume" and value < 0) or (
            field_name != "volume" and value <= 0
        ):
            raise ValueError("Tick Decimal is outside its valid range")
        return value

    @model_validator(mode="after")
    def _validate_tick(self) -> Tick:
        """Validate spread, ordering, and optional evidence relationships.

        Returns:
            Validated tick.

        Raises:
            ValueError: If relationships are inconsistent.
        """
        logger.debug("Validating Simulation Tick relationships")
        if self.ask < self.bid:
            raise ValueError("Tick ask must not be below bid")
        if self.sequence < 0:
            raise ValueError("Tick sequence must be non-negative")
        if self.available_at < self.timestamp:
            raise ValueError("Tick availability cannot precede timestamp")
        if (self.volume is None) != (self.volume_unit is None):
            raise ValueError("Tick volume and volume_unit must be supplied together")
        bar_fields = (self.source_bar_time, self.tick_index_in_bar, self.bar_phase)
        if any(value is not None for value in bar_fields) and any(
            value is None for value in bar_fields
        ):
            raise ValueError("Tick intra-bar evidence must be complete")
        if self.tick_index_in_bar is not None and self.tick_index_in_bar < 0:
            raise ValueError("tick_index_in_bar must be non-negative")
        if self.bar_phase is not None and not 0 <= self.bar_phase <= _MAX_BAR_PHASE:
            raise ValueError("bar_phase must be a 4-bit mask")
        return self

    @field_serializer("bid", "ask", "volume", when_used="json")
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one Decimal deterministically.

        Args:
            value: Decimal to serialize.

        Returns:
            Exact string or ``None``.
        """
        logger.debug("Serializing Simulation Tick Decimal")
        return None if value is None else str(value)


__all__ = ["Tick"]
