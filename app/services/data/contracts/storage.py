"""Typed storage, transaction, migration, cache, and manifest contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

from pydantic import (
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts._base import DataContractModel
from app.services.data.contracts._validation import validate_request_id
from app.services.data.contracts.market import (  # noqa: TC001 - Pydantic runtime type.
    MarketDataset,
)
from app.utils import logger

type SqlScalar = None | bool | int | float | str | bytes
type ResultScalar = None | bool | int | float | str

CACHE_TTL_MAX_SECONDS: Final = 604_800
CACHE_CLEAR_MAX_ENTRIES: Final = 10_000


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


def _relative_path(value: Path) -> Path:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _relative_path")
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise ValueError("path must be relative and traversal-free")
    if any(part.startswith(".") for part in value.parts):
        raise ValueError("hidden path segments are not allowed")
    return value


class _Contract(DataContractModel):
    """Private immutable storage-contract behavior."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class StatementPlan(_Contract):
    """Bounded SQL statement and parameter plan without a connection handle."""

    statements: tuple[str, ...]
    parameter_sets: tuple[tuple[SqlScalar, ...], ...]
    max_rows: int

    @field_validator("statements")
    @classmethod
    def _validate_statements(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_statements")
        validated = tuple(_text(statement) for statement in value)
        if not validated:
            raise ValueError("statement plan must not be empty")
        return validated

    @field_validator("max_rows")
    @classmethod
    def _validate_rows(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_rows")
        if value <= 0:
            raise ValueError("max_rows must be positive")
        return value

    @model_validator(mode="after")
    def _validate_plan(self) -> StatementPlan:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_plan")
        if len(self.statements) != len(self.parameter_sets):
            raise ValueError("each statement requires one parameter set")
        return self


class TransactionRequest(_Contract):
    """Caller-owned bounded transaction request."""

    plan: StatementPlan
    request_id: str

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)


class TransactionResult(_Contract):
    """Normalized committed transaction result without storage handles."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    rows: tuple[Mapping[str, ResultScalar], ...]
    affected_rows: int
    committed: bool
    request_id: str

    @field_validator("rows", mode="after")
    @classmethod
    def _freeze_rows(
        cls, value: tuple[Mapping[str, ResultScalar], ...]
    ) -> tuple[Mapping[str, ResultScalar], ...]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_rows")
        return tuple(MappingProxyType(dict(row)) for row in value)

    @field_serializer("rows", when_used="json")
    def _serialize_rows(
        self, value: tuple[Mapping[str, ResultScalar], ...]
    ) -> tuple[dict[str, ResultScalar], ...]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_rows")
        return tuple(dict(row) for row in value)

    @field_validator("affected_rows")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("affected_rows must be non-negative")
        return value

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)


class MigrationStep(_Contract):
    """Immutable domain-owned migration definition."""

    domain: str
    migration_id: str
    checksum: str
    statements: tuple[str, ...]

    @field_validator("domain", "migration_id", "checksum")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("statements")
    @classmethod
    def _validate_statements(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_statements")
        validated = tuple(_text(statement) for statement in value)
        if not validated:
            raise ValueError("migration statements must not be empty")
        return validated


class MigrationRequest(_Contract):
    """Ordered migration execution request for one owning domain."""

    domain: str
    steps: tuple[MigrationStep, ...]
    request_id: str

    @field_validator("domain", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @model_validator(mode="after")
    def _validate_steps(self) -> MigrationRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_steps")
        if not self.steps:
            raise ValueError("migration request must not be empty")
        if any(step.domain != self.domain for step in self.steps):
            raise ValueError("migration step ownership must match request domain")
        identifiers = tuple(step.migration_id for step in self.steps)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("migration identifiers must be unique")
        if identifiers != tuple(sorted(identifiers)):
            raise ValueError("migration steps must be ordered")
        return self


class MigrationResult(_Contract):
    """Applied and idempotently skipped migration evidence."""

    domain: str
    applied_ids: tuple[str, ...]
    skipped_ids: tuple[str, ...]
    request_id: str

    @field_validator("domain", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("applied_ids", "skipped_ids")
    @classmethod
    def _validate_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_ids")
        validated = tuple(_text(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("migration result identifiers must be unique")
        return validated

    @model_validator(mode="after")
    def _validate_result(self) -> MigrationResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if set(self.applied_ids) & set(self.skipped_ids):
            raise ValueError("migration cannot be both applied and skipped")
        return self


class DatasetLoadRequest(_Contract):
    """Approved-root-relative local dataset load request."""

    relative_path: Path
    format: Literal["csv", "parquet"]
    request_id: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_path")
        return _relative_path(value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)


class DatasetSaveRequest(_Contract):
    """Atomic approved-root-relative normalized dataset save request."""

    dataset: MarketDataset
    relative_path: Path
    format: Literal["csv", "parquet"]
    overwrite: bool
    request_id: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_path")
        return _relative_path(value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)

    @model_validator(mode="after")
    def _validate_request(self) -> DatasetSaveRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if self.dataset.request_id != self.request_id:
            raise ValueError("dataset and save request IDs must match")
        return self


class StorageManifest(_Contract):
    """Immutable normalized artifact identity and integrity manifest."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    artifact_id: str
    relative_path: Path
    format: Literal["csv", "parquet"]
    content_hash: str
    schema_version: str
    normalization_version: str
    source_revision: str
    row_count: int
    start: datetime
    end: datetime
    license_metadata: Mapping[str, str]
    provenance: Mapping[str, str]
    created_at: datetime
    request_id: str

    @field_validator(
        "artifact_id",
        "content_hash",
        "schema_version",
        "normalization_version",
        "source_revision",
        "request_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_path")
        return _relative_path(value)

    @field_validator("row_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("row_count must be non-negative")
        return value

    @field_validator("start", "end", "created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("license_metadata", "provenance", mode="after")
    @classmethod
    def _freeze_metadata(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_metadata")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_serializer("license_metadata", "provenance", when_used="json")
    def _serialize_metadata(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_metadata")
        return dict(value)

    @model_validator(mode="after")
    def _validate_manifest(self) -> StorageManifest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_manifest")
        if self.start > self.end:
            raise ValueError("start must not follow end")
        return self


class CacheReadRequest(_Contract):
    """Versioned cache read request."""

    key: str
    allow_stale: bool
    request_id: str

    @field_validator("key", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class CacheEntry(_Contract):
    """Immutable cache entry carrying complete invalidation evidence."""

    key: str
    dataset: MarketDataset
    created_at: datetime
    expires_at: datetime | None
    source_revision: str
    raw_data_hash: str
    schema_version: str
    normalization_version: str
    request_id: str

    @field_validator(
        "key",
        "source_revision",
        "raw_data_hash",
        "schema_version",
        "normalization_version",
        "request_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @model_validator(mode="after")
    def _validate_entry(self) -> CacheEntry:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_entry")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must follow created_at")
        return self


class CacheWriteRequest(_Contract):
    """Bounded cache write request with explicit TTL and revision."""

    key: str
    dataset: MarketDataset
    ttl_seconds: int
    source_revision: str
    raw_data_hash: str
    request_id: str

    @field_validator("key", "source_revision", "raw_data_hash", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("ttl_seconds")
    @classmethod
    def _validate_ttl(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_ttl")
        if not 0 <= value <= CACHE_TTL_MAX_SECONDS:
            raise ValueError("ttl_seconds is outside the bounded cache policy")
        return value


class CacheWriteResult(_Contract):
    """Truthful cache write outcome."""

    key: str
    written: bool
    request_id: str

    @field_validator("key", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class CacheClearRequest(_Contract):
    """Bounded explicit-selector cache clear request."""

    namespace: str
    source_id: str | None = None
    symbol: str | None = None
    data_kind: str | None = None
    dry_run: bool
    max_entries: int
    request_id: str

    @field_validator("namespace", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("source_id", "symbol", "data_kind")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_text")
        return _optional_text(value)

    @field_validator("max_entries")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_limit")
        if not 0 < value <= CACHE_CLEAR_MAX_ENTRIES:
            raise ValueError("max_entries is outside the bounded cache policy")
        return value


class CacheClearResult(_Contract):
    """Bounded cache clear preview or committed outcome."""

    matched_count: int
    deleted_count: int
    dry_run: bool
    request_id: str

    @field_validator("matched_count", "deleted_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("cache counts must be non-negative")
        return value

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)

    @model_validator(mode="after")
    def _validate_result(self) -> CacheClearResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if self.deleted_count > self.matched_count:
            raise ValueError("deleted_count must not exceed matched_count")
        if self.dry_run and self.deleted_count:
            raise ValueError("dry-run cache clear cannot delete entries")
        return self


class AuditPersistenceResult(_Contract):
    """Idempotent durable audit-event persistence outcome."""

    event_id: str
    persisted: bool
    idempotent: bool
    request_id: str

    @field_validator("event_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


__all__ = [
    "CACHE_CLEAR_MAX_ENTRIES",
    "CACHE_TTL_MAX_SECONDS",
    "AuditPersistenceResult",
    "CacheClearRequest",
    "CacheClearResult",
    "CacheEntry",
    "CacheReadRequest",
    "CacheWriteRequest",
    "CacheWriteResult",
    "DatasetLoadRequest",
    "DatasetSaveRequest",
    "MigrationRequest",
    "MigrationResult",
    "MigrationStep",
    "StatementPlan",
    "StorageManifest",
    "TransactionRequest",
    "TransactionResult",
]
