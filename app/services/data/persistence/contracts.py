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

from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.services.data.contracts.dataset import (  # noqa: TC001 - Pydantic runtime type.
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


_OHLC_COLUMN_COUNT: Final = 4

IMPORT_DIALECTS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "standard": (
            "Comma-delimited file whose header already uses canonical field names."
        ),
        "mt5_export": (
            "Tab-delimited MetaTrader 5 export whose header uses angle-bracket "
            "names such as <DATE>, <OPEN>, and <TICKVOL>."
        ),
    }
)


class ColumnMapping(_Contract):
    """Explicit source-column to canonical-field mapping for one import.

    Every canonical field an import needs is named here by the caller. No mapping is
    inferred from file contents, so an artifact that does not satisfy the declared
    mapping fails rather than being guessed at.
    """

    timestamp: str
    open: str | None = None
    high: str | None = None
    low: str | None = None
    close: str | None = None
    volume: str | None = None
    bid: str | None = None
    ask: str | None = None
    last: str | None = None
    spread: str | None = None

    @field_validator("*")
    @classmethod
    def _validate_optional_column(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_column")
        if value is None:
            return None
        return _text(value)

    def bar_columns(self) -> tuple[str, ...]:
        """Return the declared OHLC column names in canonical order."""
        return tuple(
            name
            for name in (self.open, self.high, self.low, self.close)
            if name is not None
        )


class ExternalImportRequest(_Contract):
    """Explicit audited admission of one externally produced artifact.

    The governed fields a foreign artifact cannot supply are caller-declared:
    `symbol`, `data_kind`, `timeframe`, `workflow_context`, and `precision_policy`.
    """

    relative_path: Path
    format: Literal["csv", "parquet"]
    dialect: str
    mapping: ColumnMapping
    symbol: str
    data_kind: Literal["bars", "ticks", "spreads"]
    timeframe: str | None = None
    source_id: str
    workflow_context: Literal[
        "research", "backtest", "validation", "risk", "execution_bound"
    ]
    precision_policy: Literal[
        "decimal_string",
        "float_research_only",
        "source_native_decimal",
        "reject_on_missing_metadata",
    ]
    price_unit: str
    volume_unit: str
    destination_path: Path
    overwrite: bool = False
    request_id: str

    @field_validator("relative_path", "destination_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_path")
        return _relative_path(value)

    @field_validator("symbol", "source_id", "price_unit", "volume_unit", "request_id")
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
        return None if value is None else _text(value)

    @field_validator("dialect")
    @classmethod
    def _validate_dialect(cls, value: str) -> str:
        """Reject any dialect outside the supported deterministic set."""
        logger.debug("Running DATA function: _validate_dialect")
        dialect = _text(value)
        if dialect not in IMPORT_DIALECTS:
            message = "unsupported import dialect"
            raise ValueError(message)
        return dialect

    @model_validator(mode="after")
    def _validate_request(self) -> ExternalImportRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if self.data_kind == "bars":
            if self.timeframe is None:
                raise ValueError("bar imports require timeframe")
            if len(self.mapping.bar_columns()) != _OHLC_COLUMN_COUNT:
                raise ValueError("bar imports require open, high, low, and close")
        if self.data_kind == "ticks" and self.mapping.bid is None:
            raise ValueError("tick imports require a bid column")
        if self.data_kind == "spreads" and self.mapping.spread is None:
            raise ValueError("spread imports require a spread column")
        if (
            self.workflow_context != "research"
            and self.precision_policy == "float_research_only"
        ):
            raise ValueError("float research precision is restricted to research")
        return self


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


class BackupTarget(_Contract):
    """One approved-root-relative file or directory selected for backup."""

    relative_path: Path
    schema_version: str
    normalization_version: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Reject absolute, traversing, or hidden backup targets."""
        logger.debug("Validating a backup target path")
        return _relative_path(value)

    @field_validator("schema_version", "normalization_version")
    @classmethod
    def _validate_versions(cls, value: str) -> str:
        """Require explicit non-empty version evidence."""
        logger.debug("Validating backup target version evidence")
        return _text(value)


class BackupEntry(_Contract):
    """Immutable integrity evidence for one file in a backup snapshot."""

    relative_path: Path
    content_hash: str
    byte_count: int
    schema_version: str
    normalization_version: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate the original approved-root-relative file identity."""
        logger.debug("Validating a backup entry path")
        return _relative_path(value)

    @field_validator("content_hash", "schema_version", "normalization_version")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Require non-empty integrity and version evidence."""
        logger.debug("Validating backup entry text evidence")
        return _text(value)

    @field_validator("byte_count")
    @classmethod
    def _validate_byte_count(cls, value: int) -> int:
        """Require a non-negative measured byte count."""
        logger.debug("Validating a backup entry byte count")
        if value < 0:
            raise ValueError("byte_count must be non-negative")
        return value


class BackupManifest(_Contract):
    """Immutable identity and integrity manifest for one backup snapshot."""

    manifest_id: str
    entries: tuple[BackupEntry, ...]
    manifest_hash: str
    created_at: datetime
    request_id: str

    @field_validator("manifest_id", "manifest_hash", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Require non-empty backup manifest identifiers."""
        logger.debug("Validating backup manifest identity evidence")
        return _text(value)

    @field_validator("entries")
    @classmethod
    def _validate_entries(
        cls,
        value: tuple[BackupEntry, ...],
    ) -> tuple[BackupEntry, ...]:
        """Require a non-empty, unique, deterministically ordered entry set."""
        logger.debug("Validating backup manifest entries")
        if not value:
            raise ValueError("backup manifest must not be empty")
        paths = tuple(str(entry.relative_path) for entry in value)
        if len(set(paths)) != len(paths):
            raise ValueError("backup entry paths must be unique")
        if paths != tuple(sorted(paths)):
            raise ValueError("backup entries must be ordered by path")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Require an aware UTC creation time."""
        logger.debug("Validating backup manifest creation time")
        return _utc(value)


class RestoreReport(_Contract):
    """Truthful outcome of one explicit atomic restore operation."""

    manifest_id: str
    restored_paths: tuple[Path, ...]
    restored_count: int
    restored_at: datetime
    request_id: str

    @field_validator("manifest_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Require non-empty restore identifiers."""
        logger.debug("Validating restore report identity evidence")
        return _text(value)

    @field_validator("restored_paths")
    @classmethod
    def _validate_paths(cls, value: tuple[Path, ...]) -> tuple[Path, ...]:
        """Validate every restored relative path."""
        logger.debug("Validating restored path evidence")
        return tuple(_relative_path(path) for path in value)

    @field_validator("restored_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Require a non-negative restored target count."""
        logger.debug("Validating restored target count")
        if value < 0:
            raise ValueError("restored_count must be non-negative")
        return value

    @field_validator("restored_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Require an aware UTC restore time."""
        logger.debug("Validating restore report time")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_report(self) -> RestoreReport:
        """Require the count to match the restored path evidence."""
        logger.debug("Validating restore report relationships")
        if self.restored_count != len(self.restored_paths):
            raise ValueError("restored_count must match restored_paths")
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


__all__ = [
    "CACHE_CLEAR_MAX_ENTRIES",
    "CACHE_TTL_MAX_SECONDS",
    "IMPORT_DIALECTS",
    "_OHLC_COLUMN_COUNT",
    "CacheClearRequest",
    "CacheClearResult",
    "CacheEntry",
    "CacheReadRequest",
    "CacheWriteRequest",
    "CacheWriteResult",
    "ColumnMapping",
    "DatasetSaveRequest",
    "ExternalImportRequest",
    "MigrationRequest",
    "MigrationResult",
    "MigrationStep",
    "StatementPlan",
    "StorageManifest",
    "TransactionRequest",
    "TransactionResult",
]
