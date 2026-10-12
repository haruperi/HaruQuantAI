"""Domain exception hierarchy for host persistence subsystem.

Description:
    Declares structured domain exceptions raised across persistence operations,
    including validation failures, schema incompatibilities, lock contention,
    optimistic concurrency revision mismatches, and data corruption.

Purpose:
    FEAT-HOST-PERSISTENCE: Authoritative database domain exceptions.

Key Capabilities:
    - FR-HOST-PERSISTENCE-EXCEPTIONS: Storage and transaction error taxonomy.
      Associated: `PersistenceError`, `ValidationError`, `IncompatibleSchemaError`,
        `StorageBusyError`, `RevisionConflictError`, `LeaseExpiredError`,
        `CorruptDataError`
      Logging: Exceptions are raised to caller or logged at boundary.

Python API Usage:
    ```python
    from app.host.persistence.errors import PersistenceError, ValidationError

    try:
        raise ValidationError("Invalid entity identifier")
    except PersistenceError as exc:
        pass
    ```

CLI Usage:
    No direct CLI for exception hierarchy. Diagnostics inspects errors:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

__all__ = [
    "CorruptDataError",
    "IncompatibleSchemaError",
    "LeaseExpiredError",
    "PersistenceError",
    "RevisionConflictError",
    "StorageBusyError",
    "ValidationError",
]


class PersistenceError(Exception):
    """Base exception for all database and persistence failures."""


class ValidationError(PersistenceError):
    """Raised when an identifier, depth, or payload violates constraints."""


class IncompatibleSchemaError(PersistenceError):
    """Raised when database schema definition is corrupt, altered, or unsupported."""


class StorageBusyError(PersistenceError):
    """Raised when SQLite locks or transactions time out under concurrent load."""


class RevisionConflictError(PersistenceError):
    """Raised when an optimistic concurrency revision mismatch occurs."""


class LeaseExpiredError(PersistenceError):
    """Raised when attempting to renew or operate on an expired/stolen lease."""


class CorruptDataError(PersistenceError):
    """Raised when persisted record content fails deserialization or validation."""
