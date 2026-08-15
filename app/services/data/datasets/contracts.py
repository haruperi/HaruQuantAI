"""Contracts for loading an approved local CSV or Parquet dataset."""

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from pydantic import ConfigDict, field_serializer, field_validator

from app.services.data.contracts._base import TracedOpenContract


def _relative_path(value: Path) -> Path:
    """Validate an approved-root-relative, traversal-free artifact path.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the operation cannot be completed safely.
    """
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise ValueError("path must be relative and traversal-free")
    if any(part.startswith(".") for part in value.parts):
        raise ValueError("hidden path segments are not allowed")
    return value


class DatasetLoadRequest(TracedOpenContract):
    """Approved-root-relative local dataset load request."""

    relative_path: Path
    format: Literal["csv", "parquet"]
    request_id: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate the requested relative artifact path.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.
        """
        return _relative_path(value)


class ManifestCompatibility(TracedOpenContract):
    """Bounded schema/normalization compatibility verdict for one manifest.

    application Phase 0 reconciliation (`feature`): an explicit,
    deterministic compatibility check against a caller-declared expectation,
    never an inferred or default-true verdict.
    """

    compatible: bool
    reasons: tuple[str, ...] = ()


class _ProviderSpecificationRevision(TracedOpenContract):
    """Immutable effective-dated provider-specification evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    revision_id: str
    broker: str
    server: str
    environment: str
    account_digest: str
    provider_symbol: str
    snapshot_checksum: str
    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None
    retrieval_provenance: str
    historical_provenance: Mapping[str, object] | None
    payload: Mapping[str, object]
    supersedes_revision_id: str | None

    @field_validator("observed_at", "effective_from", "effective_to")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        """Normalize one timestamp to aware UTC.

        Args:
            value: Timestamp or absence.

        Returns:
            Normalized timestamp or absence.

        Raises:
            ValueError: If the timestamp is naive.
        """
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("provider revision timestamps must be aware")
        return value.astimezone(UTC)

    @field_validator("payload", "historical_provenance", mode="after")
    @classmethod
    def _freeze_mapping(
        cls, value: Mapping[str, object] | None
    ) -> Mapping[str, object] | None:
        """Freeze caller-owned mappings.

        Args:
            value: Mapping or absence.

        Returns:
            Immutable defensive copy or absence.
        """
        return None if value is None else MappingProxyType(dict(value))

    @field_serializer("payload", "historical_provenance", when_used="json")
    def _serialize_mapping(
        self, value: Mapping[str, object] | None
    ) -> dict[str, object] | None:
        """Serialize immutable mappings.

        Args:
            value: Mapping or absence.

        Returns:
            JSON-safe mutable copy or absence.
        """
        return None if value is None else dict(value)


__all__ = ["DatasetLoadRequest", "ManifestCompatibility"]
