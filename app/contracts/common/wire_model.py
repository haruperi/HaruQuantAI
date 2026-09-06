"""Cycle-free base models and datetime semantics for public wire records."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


def as_utc(value: datetime) -> datetime:
    """Normalize an aware timestamp to UTC.

    Args:
        value: Timestamp with a resolvable UTC offset.

    Returns:
        The timestamp normalized to ``datetime.UTC``.

    Raises:
        ValueError: If the timestamp is not timezone-aware.
    """
    if value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


class WireModel(BaseModel):
    """Base configuration shared by public wire records."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class StrictWireModel(WireModel):
    """Strict and immutable base for platform-neutral structure records."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class UtcWireModel(StrictWireModel):
    """Strict structure base that normalizes direct datetime fields to UTC."""

    @field_validator("*", mode="after", check_fields=False)
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        """Normalize each direct datetime field after type validation.

        Returns:
            The UTC-normalized datetime or the unchanged non-datetime value.
        """
        return as_utc(value) if isinstance(value, datetime) else value


__all__ = ["StrictWireModel", "UtcWireModel", "WireModel", "as_utc"]
