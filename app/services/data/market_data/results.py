"""Temporary market-data result contracts pending FEAT-DATA-02 migration."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import field_serializer, field_validator, model_validator

from app.composition.logging import get_logger
from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.dataset import (  # noqa: TC001 - Pydantic runtime types.
    DataGap,
    DataKind,
    DataRange,
)

logger = get_logger(__name__)


def _text(value: str) -> str:
    """Validate a required trimmed text value.

    Args:
        value: Candidate text.

    Returns:
        The validated text.

    Raises:
        ValueError: If the value is empty or untrimmed.
    """
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _optional_text(value: str | None) -> str | None:
    """Validate optional trimmed text.

    Args:
        value: Candidate text or ``None``.

    Returns:
        The validated text or ``None``.
    """
    return None if value is None else _text(value)


class DataAvailability(_Contract):
    """Represent measured indexed availability without materialized records."""

    source_id: str
    symbol: str
    data_kind: DataKind
    timeframe: str | None = None
    ranges: tuple[DataRange, ...]
    gaps: tuple[DataGap, ...]
    completeness: Decimal
    record_count: int
    source_revision: str
    source_readiness: Literal["disabled", "staging", "production"]
    provenance: Mapping[str, str]
    request_id: str

    @field_validator("source_id", "symbol", "source_revision", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required text fields.

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
        """Validate the optional timeframe.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _validate_timeframe")
        return _optional_text(value)

    @field_validator("completeness")
    @classmethod
    def _validate_completeness(cls, value: Decimal) -> Decimal:
        """Validate the measured completeness ratio.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_completeness")
        if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("completeness must be finite and between zero and one")
        return value

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate the non-negative record count.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("record_count must be non-negative")
        return value

    @field_validator("provenance", mode="after")
    @classmethod
    def _freeze_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze provenance against mutation.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _freeze_provenance")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize provenance deterministically.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)

    @model_validator(mode="after")
    def _validate_availability(self) -> DataAvailability:
        """Validate availability ordering and bar timeframe evidence.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Running DATA function: _validate_availability")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bar availability requires timeframe")
        starts = tuple(item.start for item in self.ranges)
        if starts != tuple(sorted(starts)):
            raise ValueError("ranges must be ordered")
        gap_starts = tuple(item.start for item in self.gaps)
        if gap_starts != tuple(sorted(gap_starts)):
            raise ValueError("gaps must be ordered")
        return self

    @field_serializer("completeness", when_used="json")
    def _serialize_completeness(self, value: Decimal) -> str:
        """Serialize completeness deterministically.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        logger.debug("Running DATA function: _serialize_completeness")
        return str(value)


__all__ = ["DataAvailability"]
