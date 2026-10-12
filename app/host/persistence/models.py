"""Authoritative domain records and pagination envelopes for host persistence.

Description:
    Declares Pydantic data models representing migration records, entity records,
    database health statuses, generic paginated pages, setting records, and
    host session metadata envelopes.

Purpose:
    FEAT-HOST-PERSISTENCE: Domain models and paginated record structures.

Key Capabilities:
    - FR-HOST-PERSISTENCE-MODELS: Typed models and serialization representations.
      Associated: `MigrationRecord`, `EntityRecord`, `DatabaseStatus`, `Page`,
        `SettingRecord`, `SettingsPage`, `HostSessionRecord`
      Logging: Models are instantiated and validated during store operations.

Python API Usage:
    ```python
    from app.host.persistence.models import DatabaseStatus, EntityRecord, Page
    ```

CLI Usage:
    No direct CLI for domain records. Diagnostics reports status:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "DatabaseStatus",
    "EntityRecord",
    "HostSessionRecord",
    "MigrationRecord",
    "Page",
    "SettingRecord",
    "SettingsPage",
]


class MigrationRecord(BaseModel):
    """Schema migration ledger entry."""

    version: int = Field(ge=1, description="Monotonic schema version number.")
    name: str = Field(description="Descriptive identifier of migration.")
    applied_at_utc: datetime = Field(description="UTC timestamp of migration commit.")
    checksum: str = Field(description="SHA-256 digest of migration SQL script.")


class EntityRecord(BaseModel):
    """Authoritative storage envelope for a persisted domain entity."""

    entity_id: str = Field(description="Unique entity identifier within type.")
    entity_type: str = Field(description="Categorical entity type name.")
    scope: str = Field(description="Tenant or namespace scope.")
    payload: dict[str, Any] = Field(description="Structured JSON payload.")
    revision: int = Field(
        ge=1, description="Monotonic optimistic concurrency revision."
    )
    created_at_utc: datetime = Field(description="UTC timestamp of creation.")
    updated_at_utc: datetime = Field(description="UTC timestamp of last write.")


class DatabaseStatus(BaseModel):
    """Operational health snapshot of the host SQLite persistence engine."""

    database_path: str = Field(description="Absolute path to database file.")
    is_connected: bool = Field(description="Whether database responds to queries.")
    journal_mode: str = Field(description="Active SQLite journal mode (e.g., WAL).")
    schema_version: int = Field(description="Highest applied schema migration version.")
    table_count: int = Field(ge=0, description="Total user tables in database.")
    integrity_status: str = Field(description="Result of PRAGMA integrity_check.")


class Page[T](BaseModel):
    """Keyset or offset paginated collection of typed records."""

    items: list[T] = Field(description="List of records in the current page.")
    total_count: int = Field(ge=0, description="Total matching records count.")
    next_cursor: str | None = Field(
        default=None, description="Cursor for fetching next page, if any."
    )


class SettingRecord(BaseModel):
    """Auditable record for a scoped configuration setting."""

    scope: str
    key: str
    value: Any
    schema_version: int = 1
    updated_at_utc: str


class SettingsPage(BaseModel):
    """Paginated slice of setting records."""

    items: list[SettingRecord]
    next_key: str | None = None


class HostSessionRecord(BaseModel):
    """Stored login lifecycle metadata without a usable bearer token."""

    session_id: str
    token_hash: str = Field(repr=False)
    username: str
    peer_id: str
    created_at_utc: str
    expires_at_utc: str
    revoked_at_utc: str | None = None
    status: str
