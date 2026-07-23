"""Private immutable validation evidence for official Simulation runs."""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import logger

_SHA256_HEX_LENGTH = 64


class MarketDataValidationContext(BaseModel):
    """Exact evidence required to validate one market dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_data_hash: str
    requested_start: datetime
    requested_end: datetime
    evaluated_at: datetime
    maximum_staleness: timedelta
    allowed_tick_models: tuple[str, ...]

    @field_validator("expected_data_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate a lowercase SHA-256 digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If the digest is malformed.
        """
        logger.debug("Validating expected Simulation dataset hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("expected_data_hash must be lowercase SHA-256 hex")
        return value

    @field_validator("requested_start", "requested_end", "evaluated_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one aware UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If the timestamp is not UTC.
        """
        logger.debug("Validating Simulation market-data context time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("market-data validation time must be aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_context(self) -> MarketDataValidationContext:
        """Validate coverage, staleness, and model invariants.

        Returns:
            Validated context.

        Raises:
            ValueError: If context relationships are invalid.
        """
        logger.debug("Validating Simulation market-data context relationships")
        if self.requested_end < self.requested_start:
            raise ValueError("requested_end must not precede requested_start")
        if self.maximum_staleness < timedelta(0):
            raise ValueError("maximum_staleness must be non-negative")
        if not self.allowed_tick_models or len(set(self.allowed_tick_models)) != len(
            self.allowed_tick_models
        ):
            raise ValueError("allowed_tick_models must be non-empty and unique")
        return self


class ValidatedMarketDataEvidence(BaseModel):
    """Immutable proof that a dataset passed the Simulation gate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    data_hash: str
    dataset_schema_id: str
    tick_model: str
    record_count: int
    validated_at: datetime

    @field_validator("data_hash", "dataset_schema_id", "tick_model")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required evidence text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank.
        """
        logger.debug("Validating Simulation market-data evidence text")
        if not value or value != value.strip():
            raise ValueError("validation evidence text must be non-empty and trimmed")
        return value


__all__: tuple[str, ...] = ()
