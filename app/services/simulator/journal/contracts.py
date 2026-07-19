"""Immutable versioned Simulation journal event contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.utils import canonical_json, logger

_HASH_LENGTH = 64
_SENSITIVE_PARTS = ("password", "secret", "token", "credential", "private_key")


class JournalEvent(BaseModel):
    """Canonical append-only Simulation journal event version 1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    sequence: int
    occurred_at: datetime
    event_type: str
    payload: Mapping[str, object]
    previous_hash: str
    event_hash: str
    correlation_id: str
    causation_id: str | None
    schema_version: Literal["v1"] = "v1"

    @field_validator("run_id", "event_type", "correlation_id", "causation_id")
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        """Validate required or optional event text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating Simulation journal event text")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("Journal event text must be non-empty and trimmed")
        return value

    @field_validator("occurred_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate aware UTC occurrence time.

        Args:
            value: Candidate occurrence time.

        Returns:
            Validated UTC time.

        Raises:
            ValueError: If time is not aware UTC.
        """
        logger.debug("Validating Simulation journal event time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("Journal occurrence time must be aware UTC")
        return value

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate a non-negative event sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Validated sequence.

        Raises:
            ValueError: If negative.
        """
        logger.debug("Validating Simulation journal event sequence")
        if value < 0:
            raise ValueError("Journal sequence must be non-negative")
        return value

    @field_validator("previous_hash", "event_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate a lowercase SHA-256 journal hash.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If malformed.
        """
        logger.debug("Validating Simulation journal hash")
        if len(value) != _HASH_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("Journal hashes must be lowercase SHA-256 hex")
        return value

    @field_validator("payload", mode="after")
    @classmethod
    def _validate_payload(cls, value: Mapping[str, object]) -> Mapping[str, object]:
        """Validate, canonicalize, and freeze a secret-safe payload.

        Args:
            value: Candidate event payload.

        Returns:
            Immutable shallow payload copy.

        Raises:
            ValueError: If a sensitive key is present.
        """
        logger.debug("Validating Simulation journal payload")
        if any(
            sensitive in key.casefold()
            for key in value
            for sensitive in _SENSITIVE_PARTS
        ):
            raise ValueError("Journal payload contains sensitive key material")
        canonical_json(value)
        return MappingProxyType(dict(value))

    @field_serializer("payload", when_used="json")
    def _serialize_payload(self, value: Mapping[str, object]) -> dict[str, object]:
        """Serialize immutable journal payload data.

        Args:
            value: Immutable payload.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Simulation journal payload")
        return dict(value)


__all__ = ["JournalEvent"]
