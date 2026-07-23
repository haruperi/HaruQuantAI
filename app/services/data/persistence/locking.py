"""Persistent exclusive write leases for resolved filesystem paths."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Self

from app.services.data._settings import get_data_settings
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import execute_transaction
from app.utils import logger

_SQLITE_INTEGER_MAX = (1 << 63) - 1
_NANOSECONDS_PER_SECOND = 1_000_000_000
_CREATE_LOCK_TABLE = """
CREATE TABLE IF NOT EXISTS data_write_locks (
    resolved_path TEXT PRIMARY KEY,
    owner_request_id TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    lease_expires_at_ns TEXT NOT NULL CHECK (
        length(lease_expires_at_ns) = 19
        AND lease_expires_at_ns NOT GLOB '*[^0-9]*'
    ),
    previous_owner_request_id TEXT,
    recovered_at_ns TEXT,
    recovery_count INTEGER NOT NULL DEFAULT 0 CHECK (recovery_count >= 0),
    CHECK (
        (active = 1 AND lease_expires_at_ns > '0000000000000000000')
        OR (active = 0 AND lease_expires_at_ns = '0000000000000000000')
    ),
    CHECK (
        (previous_owner_request_id IS NULL AND recovered_at_ns IS NULL)
        OR (previous_owner_request_id IS NOT NULL AND recovered_at_ns IS NOT NULL)
    ),
    CHECK (
        recovered_at_ns IS NULL
        OR (
            length(recovered_at_ns) = 19
            AND recovered_at_ns NOT GLOB '*[^0-9]*'
        )
    )
) STRICT
""".strip()
_ACQUIRE_LOCK = """
INSERT INTO data_write_locks (
    resolved_path,
    owner_request_id,
    active,
    lease_expires_at_ns,
    previous_owner_request_id,
    recovered_at_ns,
    recovery_count
)
VALUES (?, ?, 1, ?, NULL, NULL, 0)
ON CONFLICT(resolved_path) DO UPDATE SET
    previous_owner_request_id = CASE
        WHEN data_write_locks.active = 1
        THEN data_write_locks.owner_request_id
        ELSE data_write_locks.previous_owner_request_id
    END,
    recovered_at_ns = CASE
        WHEN data_write_locks.active = 1
        THEN ?
        ELSE data_write_locks.recovered_at_ns
    END,
    recovery_count = data_write_locks.recovery_count + CASE
        WHEN data_write_locks.active = 1 THEN 1 ELSE 0
    END,
    owner_request_id = excluded.owner_request_id,
    active = 1,
    lease_expires_at_ns = excluded.lease_expires_at_ns
WHERE data_write_locks.active = 0
    OR data_write_locks.lease_expires_at_ns <= ?
RETURNING owner_request_id, lease_expires_at_ns, recovery_count
""".strip()
_RELEASE_LOCK = """
UPDATE data_write_locks
SET active = 0, lease_expires_at_ns = '0000000000000000000'
WHERE resolved_path = ? AND owner_request_id = ? AND active = 1
RETURNING owner_request_id
""".strip()


def _error(code: str, request_id: str | None, stage: str) -> DataError:
    """Build one redacted locking-boundary error."""
    logger.debug("Running DATA function: _error")
    return DataError(
        code,
        safe_details={"operation": "acquire_write_lock", "stage": stage},
        request_id=request_id,
    )


def _validate_request_id(request_id: str) -> str:
    """Validate the caller-owned trace identifier."""
    logger.debug("Running DATA function: _validate_request_id")
    if not request_id or request_id != request_id.strip():
        raise _error("INVALID_INPUT", None, "request_id")
    return request_id


def _resolve_path(path: Path, request_id: str) -> Path:
    """Resolve one path identity without creating or opening it."""
    logger.debug("Running DATA function: _resolve_path")
    if not isinstance(path, Path):
        raise _error("INVALID_INPUT", request_id, "path")
    try:
        return path.expanduser().resolve()
    except OSError:
        raise _error("INVALID_INPUT", request_id, "path") from None


def _parse_lease_nanoseconds(value: float | None, now_ns: int) -> int:
    """Parse one required positive lease within SQLite integer bounds."""
    logger.debug("Running DATA function: _parse_lease_nanoseconds")
    if now_ns < 0 or now_ns > _SQLITE_INTEGER_MAX:
        raise ValueError("system time exceeds persistent timestamp bounds")
    if value is None:
        raise ValueError("missing lease configuration")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("invalid lease configuration")
    lease_nanoseconds = int(value * _NANOSECONDS_PER_SECOND)
    if lease_nanoseconds <= 0 or lease_nanoseconds > _SQLITE_INTEGER_MAX - now_ns:
        raise ValueError("lease exceeds persistent timestamp bounds")
    return lease_nanoseconds


def _timestamp_text(value: int) -> str:
    """Encode one bounded Unix-nanosecond timestamp as ordered fixed-width text."""
    logger.debug("Running DATA function: _timestamp_text")
    return f"{value:019d}"


def _lease_expiry(request_id: str) -> tuple[int, int]:
    """Return the current and configured expiry times in Unix nanoseconds."""
    logger.debug("Running DATA function: _lease_expiry")
    now_ns = time.time_ns()
    try:
        lease_seconds = get_data_settings().write_lock_lease_seconds
        lease_nanoseconds = _parse_lease_nanoseconds(lease_seconds, now_ns)
    except OverflowError, ValueError:
        raise _error("DB_CONNECTION_ERROR", request_id, "configuration") from None
    return now_ns, now_ns + lease_nanoseconds


@dataclass(slots=True)
class WriteLock:
    """One acquired owner-bound lease released by its context-manager exit."""

    path: Path
    request_id: str
    expires_at_ns: int
    recovery_count: int
    _entered: bool = field(default=False, init=False, repr=False)
    _released: bool = field(default=False, init=False, repr=False)

    def __enter__(self) -> Self:
        """Enter this acquired lease exactly once."""
        logger.debug("Running DATA function: __enter__")
        if self._entered or self._released:
            raise _error("CONCURRENT_WRITE_LOCKED", self.request_id, "context")
        self._entered = True
        return self

    def __exit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        """Release this lease without deleting another owner's record."""
        logger.debug("Running DATA function: __exit__")
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(_RELEASE_LOCK,),
                    parameter_sets=((str(self.path), self.request_id),),
                    max_rows=1,
                ),
                request_id=self.request_id,
            )
        )
        if len(result.rows) != 1:
            raise _error("CONCURRENT_WRITE_LOCKED", self.request_id, "release")
        if result.rows[0].get("owner_request_id") != self.request_id:
            raise _error("DATABASE_ERROR", self.request_id, "result")
        self._released = True
        self._entered = False


def acquire_write_lock(path: Path, request_id: str) -> WriteLock:
    """Atomically acquire one exclusive bounded lease for a resolved path.

    The Data-owned lock table is the sole migration-bootstrap exception. It is
    created idempotently on this explicit call so the later migration runner can
    safely use the lock without import-time I/O or a schema dependency cycle.

    Args:
        path: Filesystem path whose resolved identity must have one writer.
        request_id: Non-empty caller-owned trace and lease-owner identifier.

    Returns:
        An acquired context manager that releases only its exact owner record.

    Raises:
        DataError: If input/configuration is invalid, persistence fails, or another
            unexpired owner holds the resolved path.
    """
    logger.debug("Running DATA function: acquire_write_lock")
    validated_request_id = _validate_request_id(request_id)
    resolved_path = _resolve_path(path, validated_request_id)
    now_ns, expires_at_ns = _lease_expiry(validated_request_id)
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(_CREATE_LOCK_TABLE, _ACQUIRE_LOCK),
                parameter_sets=(
                    (),
                    (
                        str(resolved_path),
                        validated_request_id,
                        _timestamp_text(expires_at_ns),
                        _timestamp_text(now_ns),
                        _timestamp_text(now_ns),
                    ),
                ),
                max_rows=1,
            ),
            request_id=validated_request_id,
        )
    )
    if len(result.rows) != 1:
        raise _error("CONCURRENT_WRITE_LOCKED", validated_request_id, "acquire")
    row = result.rows[0]
    persisted_owner = row.get("owner_request_id")
    persisted_expiry = row.get("lease_expires_at_ns")
    recovery_count = row.get("recovery_count")
    if (
        persisted_owner != validated_request_id
        or not isinstance(persisted_expiry, str)
        or not isinstance(recovery_count, int)
        or recovery_count < 0
    ):
        raise _error("DATABASE_ERROR", validated_request_id, "result")
    try:
        parsed_expiry = int(persisted_expiry)
    except ValueError:
        raise _error("DATABASE_ERROR", validated_request_id, "result") from None
    if parsed_expiry != expires_at_ns:
        raise _error("DATABASE_ERROR", validated_request_id, "result")
    return WriteLock(
        path=resolved_path,
        request_id=validated_request_id,
        expires_at_ns=parsed_expiry,
        recovery_count=recovery_count,
    )


__all__ = ["WriteLock", "acquire_write_lock"]
