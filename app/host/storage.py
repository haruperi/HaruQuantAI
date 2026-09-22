"""Host storage owner: SQLite versioned records, migrations, and CAS."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import sqlite3
import threading
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypeVar, override

from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec


class StorageError(RuntimeError):
    """Base error for storage failures."""


class StorageConflictError(StorageError):
    """Raised when an optimistic concurrency check fails."""


class StorageClosedError(StorageError):
    """Raised when an operation is attempted on a closed store."""


class StorageMigrationError(StorageError):
    """Raised when a schema migration fails."""


@dataclass(frozen=True, slots=True)
class StorageRecord:
    """Immutable versioned storage record."""

    namespace: str
    key: str
    revision: int
    schema_version: int
    payload_bytes: bytes
    created_at_utc: str
    updated_at_utc: str

    def __post_init__(self) -> None:
        """Validate record fields."""
        if not self.namespace or not isinstance(self.namespace, str):
            raise ValueError("namespace must be a non-empty string")
        if not self.key or not isinstance(self.key, str):
            raise ValueError("key must be a non-empty string")
        if self.revision < 1:
            raise ValueError("revision must be >= 1")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if not isinstance(self.payload_bytes, bytes):
            raise TypeError("payload_bytes must be bytes")


@dataclass(frozen=True, slots=True)
class StorageMutation:
    """Requested record upsert with optional compare-and-swap revision."""

    namespace: str
    key: str
    schema_version: int
    payload_bytes: bytes
    expected_revision: int | None = None

    def __post_init__(self) -> None:
        """Validate mutation fields."""
        if not self.namespace or not isinstance(self.namespace, str):
            raise ValueError("namespace must be a non-empty string")
        if not self.key or not isinstance(self.key, str):
            raise ValueError("key must be a non-empty string")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if not isinstance(self.payload_bytes, bytes):
            raise TypeError("payload_bytes must be bytes")
        if self.expected_revision is not None and self.expected_revision < 0:
            raise ValueError("expected_revision must be >= 0 or None")


@dataclass(frozen=True, slots=True)
class StorageDelete:
    """Requested record deletion with optional compare-and-swap revision."""

    namespace: str
    key: str
    expected_revision: int | None = None

    def __post_init__(self) -> None:
        """Validate delete fields."""
        if not self.namespace or not isinstance(self.namespace, str):
            raise ValueError("namespace must be a non-empty string")
        if not self.key or not isinstance(self.key, str):
            raise ValueError("key must be a non-empty string")
        if self.expected_revision is not None and self.expected_revision < 1:
            raise ValueError("expected_revision must be >= 1 or None")


@dataclass(frozen=True, slots=True)
class StorageConflict:
    """Record conflict information on CAS failure."""

    namespace: str
    key: str
    expected_revision: int | None
    actual_revision: int | None


@dataclass(frozen=True, slots=True)
class StorageTransactionResult:
    """Result of an all-or-nothing storage transaction."""

    committed: bool
    records: tuple[StorageRecord, ...] = ()
    conflicts: tuple[StorageConflict, ...] = ()


@dataclass(frozen=True, slots=True)
class StoragePage:
    """Deterministic page of scanned records."""

    records: tuple[StorageRecord, ...]
    next_token: str | None = None
    total_count: int = 0


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration for SQLite storage provider."""

    database_path: Path | str
    busy_timeout_ms: int = 5000
    max_page_size: int = 100

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be > 0")
        if self.max_page_size <= 0:
            raise ValueError("max_page_size must be > 0")


class Storage(Protocol):
    """Public capability protocol for durable record persistence."""

    def get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record by namespace and key, or None if absent."""
        ...

    def commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit an all-or-nothing batch of mutations with CAS validation."""
        ...

    def scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Deterministically scan records in a namespace ordered by key ASC."""
        ...

    async def async_get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record on the owned writer thread (event-loop safe)."""
        ...

    async def async_commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations on the owned writer thread (event-loop safe)."""
        ...

    async def async_scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Deterministically scan records off the event loop."""
        ...

    def status(self) -> StorageStatus:
        """Return migration and readiness status."""
        ...

    def close(self) -> None:
        """Flush and safely close the storage engine."""
        ...


@dataclass(frozen=True, slots=True)
class StorageStatus:
    """Immutable migration/readiness status of the storage engine."""

    schema_version: int
    applied_migrations: tuple[int, ...]
    ready: bool


_T = TypeVar("_T")

HOST_STORAGE = Capability[Storage]("host.storage", 1)


def _utc_now_iso() -> str:
    """Return current UTC timestamp formatted as ISO-8601 string."""
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class _SqliteStorage(Storage):
    """Private SQLite implementation of Storage protocol."""

    def __init__(self, config: StorageConfig) -> None:
        """Initialize and migrate the SQLite database."""
        self._config = config
        db_path = Path(config.database_path)
        if db_path != Path(":memory:"):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(db_path)
        self._lock = threading.RLock()
        self._closed = False
        # One owned single-writer executor thread: async callers bridge
        # through it so the event loop never blocks on SQLite directly.
        self._writer = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="haruquantai-storage"
        )
        # Identify the single owned writer thread once; every operation,
        # synchronous or async, serializes through it.
        self._writer_ident = self._writer.submit(threading.get_ident).result()

        try:
            self._conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=float(config.busy_timeout_ms) / 1000.0,
                isolation_level=None,  # Explicit transaction control
            )
            self._conn.execute(f"PRAGMA busy_timeout = {config.busy_timeout_ms};")
            self._conn.execute("PRAGMA foreign_keys = ON;")
            if db_path != Path(":memory:"):
                self._conn.execute("PRAGMA journal_mode = WAL;")
            self._migrate()
        except sqlite3.DatabaseError as err:
            self._writer.shutdown(wait=True)
            raise StorageError(
                f"Storage failed to open or migrate {self._db_path!r}: {err}"
            ) from err

    def _migrate(self) -> None:
        """Apply idempotent forward-only migrations."""
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at_utc TEXT NOT NULL
                );
                """
            )
            cursor = self._conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version ASC;"
            )
            applied_rows = [row[0] for row in cursor.fetchall()]
            applied = set(applied_rows)

            max_known = 1
            newer = [v for v in applied_rows if v > max_known]
            if newer:
                raise StorageMigrationError(
                    f"Database schema version {newer[0]} is newer than "
                    f"supported version {max_known}; upgrade the host first"
                )

            migrations: list[tuple[int, str, Sequence[str]]] = [
                (
                    1,
                    "create_records_table",
                    (
                        """
                        CREATE TABLE IF NOT EXISTS records (
                            namespace TEXT NOT NULL,
                            key TEXT NOT NULL,
                            revision INTEGER NOT NULL,
                            schema_version INTEGER NOT NULL,
                            payload_bytes BLOB NOT NULL,
                            created_at_utc TEXT NOT NULL,
                            updated_at_utc TEXT NOT NULL,
                            PRIMARY KEY (namespace, key)
                        );
                        """,
                        """
                        CREATE INDEX IF NOT EXISTS idx_records_ns_key
                        ON records (namespace, key);
                        """,
                    ),
                )
            ]

            for version, name, statements in migrations:
                if version not in applied:
                    try:
                        self._conn.execute("BEGIN IMMEDIATE;")
                        for statement in statements:
                            self._conn.execute(statement)
                        self._conn.execute(
                            "INSERT INTO schema_migrations "
                            "(version, name, applied_at_utc) "
                            "VALUES (?, ?, ?);",
                            (version, name, _utc_now_iso()),
                        )
                        self._conn.execute("COMMIT;")
                    except Exception as err:
                        self._conn.execute("ROLLBACK;")
                        raise StorageMigrationError(
                            f"Migration {version} ({name}) failed: {err}"
                        ) from err

    @override
    def get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record by namespace and key on the writer thread."""
        return self._on_writer(lambda: self._get_record_impl(namespace, key))

    def _get_record_impl(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record by namespace and key."""
        with self._lock:
            if self._closed:
                raise StorageClosedError("Storage is closed")
            cursor = self._conn.execute(
                """
                SELECT namespace, key, revision, schema_version, payload_bytes,
                       created_at_utc, updated_at_utc
                FROM records
                WHERE namespace = ? AND key = ?;
                """,
                (namespace, key),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return StorageRecord(
                namespace=row[0],
                key=row[1],
                revision=row[2],
                schema_version=row[3],
                payload_bytes=row[4],
                created_at_utc=row[5],
                updated_at_utc=row[6],
            )

    def _check_conflict(
        self, op: StorageMutation | StorageDelete
    ) -> StorageConflict | None:
        """Check optimistic concurrency expectations for a single operation."""
        cursor = self._conn.execute(
            "SELECT revision FROM records WHERE namespace = ? AND key = ?;",
            (op.namespace, op.key),
        )
        row = cursor.fetchone()
        actual_revision: int | None = row[0] if row is not None else None

        if op.expected_revision is not None:
            # 0 indicates expecting no prior record
            if op.expected_revision == 0:
                if actual_revision is not None:
                    return StorageConflict(
                        namespace=op.namespace,
                        key=op.key,
                        expected_revision=0,
                        actual_revision=actual_revision,
                    )
            elif actual_revision != op.expected_revision:
                return StorageConflict(
                    namespace=op.namespace,
                    key=op.key,
                    expected_revision=op.expected_revision,
                    actual_revision=actual_revision,
                )
        elif isinstance(op, StorageDelete) and actual_revision is None:
            return StorageConflict(
                namespace=op.namespace,
                key=op.key,
                expected_revision=None,
                actual_revision=None,
            )
        return None

    def _apply_mutation(self, op: StorageMutation, now_iso: str) -> StorageRecord:
        """Apply an individual record insertion or update."""
        cursor = self._conn.execute(
            "SELECT revision, created_at_utc FROM records "
            "WHERE namespace = ? AND key = ?;",
            (op.namespace, op.key),
        )
        row = cursor.fetchone()
        if row is None:
            new_rev = 1
            created_at = now_iso
            self._conn.execute(
                """
                INSERT INTO records (
                    namespace, key, revision, schema_version,
                    payload_bytes, created_at_utc, updated_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    op.namespace,
                    op.key,
                    new_rev,
                    op.schema_version,
                    op.payload_bytes,
                    created_at,
                    now_iso,
                ),
            )
        else:
            new_rev = row[0] + 1
            created_at = row[1]
            self._conn.execute(
                """
                UPDATE records
                SET revision = ?, schema_version = ?,
                    payload_bytes = ?, updated_at_utc = ?
                WHERE namespace = ? AND key = ?;
                """,
                (
                    new_rev,
                    op.schema_version,
                    op.payload_bytes,
                    now_iso,
                    op.namespace,
                    op.key,
                ),
            )
        return StorageRecord(
            namespace=op.namespace,
            key=op.key,
            revision=new_rev,
            schema_version=op.schema_version,
            payload_bytes=op.payload_bytes,
            created_at_utc=created_at,
            updated_at_utc=now_iso,
        )

    @override
    def commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations on the owned writer thread (blocking)."""
        return self._on_writer(lambda: self._commit_transaction_impl(mutations))

    def _commit_transaction_impl(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations and deletes in an atomic transaction."""
        if not mutations:
            return StorageTransactionResult(committed=True)

        with self._lock:
            if self._closed:
                raise StorageClosedError("Storage is closed")

            self._conn.execute("BEGIN IMMEDIATE;")
            conflicts: list[StorageConflict] = []

            for op in mutations:
                conflict = self._check_conflict(op)
                if conflict is not None:
                    conflicts.append(conflict)

            if conflicts:
                self._conn.execute("ROLLBACK;")
                return StorageTransactionResult(
                    committed=False, conflicts=tuple(conflicts)
                )

            now_iso = _utc_now_iso()
            written_records: list[StorageRecord] = []

            for op in mutations:
                if isinstance(op, StorageDelete):
                    self._conn.execute(
                        "DELETE FROM records WHERE namespace = ? AND key = ?;",
                        (op.namespace, op.key),
                    )
                elif isinstance(op, StorageMutation):
                    written_records.append(self._apply_mutation(op, now_iso))

            self._conn.execute("COMMIT;")
            return StorageTransactionResult(
                committed=True, records=tuple(written_records)
            )

    @override
    def scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Scan records on the owned writer thread (blocking)."""
        return self._on_writer(
            lambda: self._scan_records_impl(
                namespace, prefix=prefix, limit=limit, after_key=after_key
            )
        )

    def _scan_records_impl(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Scan records in deterministic key order with pagination."""
        with self._lock:
            if self._closed:
                raise StorageClosedError("Storage is closed")

            bounded_limit = min(max(1, limit), self._config.max_page_size)

            conditions = ["namespace = ?"]
            params: list[Any] = [namespace]

            if prefix:
                conditions.append("key LIKE ?")
                params.append(f"{prefix}%")

            if after_key is not None:
                conditions.append("key > ?")
                params.append(after_key)

            where_clause = " AND ".join(conditions)

            # Query items with bounded_limit + 1 to detect has_more
            query = f"""
                SELECT namespace, key, revision, schema_version, payload_bytes,
                       created_at_utc, updated_at_utc
                FROM records
                WHERE {where_clause}
                ORDER BY key ASC
                LIMIT ?;
            """  # noqa: S608 - parameterized dynamic query with static column names
            params.append(bounded_limit + 1)
            cursor = self._conn.execute(query, params)
            rows = cursor.fetchall()

            has_more = len(rows) > bounded_limit
            slice_rows = rows[:bounded_limit]

            records = tuple(
                StorageRecord(
                    namespace=r[0],
                    key=r[1],
                    revision=r[2],
                    schema_version=r[3],
                    payload_bytes=r[4],
                    created_at_utc=r[5],
                    updated_at_utc=r[6],
                )
                for r in slice_rows
            )

            next_token = slice_rows[-1][1] if has_more and slice_rows else None

            # Total count in namespace (with prefix if given)
            count_conditions = ["namespace = ?"]
            count_params: list[Any] = [namespace]
            if prefix:
                count_conditions.append("key LIKE ?")
                count_params.append(f"{prefix}%")
            count_query = (
                f"SELECT COUNT(*) FROM records WHERE {' AND '.join(count_conditions)};"  # noqa: S608
            )
            count_cursor = self._conn.execute(count_query, count_params)
            total_count = count_cursor.fetchone()[0]

            return StoragePage(
                records=records,
                next_token=next_token,
                total_count=total_count,
            )

    @override
    def status(self) -> StorageStatus:
        """Return migration and readiness status from the writer thread."""
        return self._on_writer(self._status_impl)

    def _status_impl(self) -> StorageStatus:
        """Return migration and readiness status."""
        with self._lock:
            if self._closed:
                return StorageStatus(
                    schema_version=0, applied_migrations=(), ready=False
                )
            cursor = self._conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version ASC;"
            )
            applied = tuple(row[0] for row in cursor.fetchall())
            return StorageStatus(
                schema_version=applied[-1] if applied else 0,
                applied_migrations=applied,
                ready=True,
            )

    @override
    async def async_get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record on the owned writer thread."""
        return await self._await_on_writer(
            lambda: self._get_record_impl(namespace, key)
        )

    @override
    async def async_commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations on the owned writer thread."""
        return await self._await_on_writer(
            lambda: self._commit_transaction_impl(mutations)
        )

    @override
    async def async_scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Deterministically scan records on the owned writer thread."""
        return await self._await_on_writer(
            lambda: self._scan_records_impl(
                namespace, prefix=prefix, limit=limit, after_key=after_key
            )
        )

    def _on_writer(self, fn: Callable[[], _T]) -> _T:
        """Run a storage operation on the owned writer thread (blocking).

        Executes inline when already on the writer thread (e.g. nested or
        async-facade calls); otherwise submits and blocks on the result.
        """
        if self._closed:
            raise StorageClosedError("Storage is closed")
        if threading.get_ident() == self._writer_ident:
            return fn()
        return self._writer.submit(fn).result()

    async def _await_on_writer(self, fn: Callable[[], _T]) -> _T:
        """Run a storage operation on the owned writer thread (async)."""
        if self._closed:
            raise StorageClosedError("Storage is closed")
        if threading.get_ident() == self._writer_ident:
            return fn()
        return await asyncio.wrap_future(self._writer.submit(fn))

    @override
    def close(self) -> None:
        """Safely close the database connection and drain the writer thread."""
        with self._lock:
            if not self._closed:
                self._closed = True
                self._conn.close()
        self._writer.shutdown(wait=True)

    def __del__(self) -> None:
        """Close connection if garbage collected."""
        with contextlib.suppress(sqlite3.Error, OSError):
            self.close()


class _StorageFeature:
    spec = FeatureSpec(
        "host.storage",
        provides=frozenset({HOST_STORAGE}),
        description="SQLite-backed versioned records and CAS transactions",
    )

    def __init__(self, config: StorageConfig) -> None:
        self._service = _SqliteStorage(config)

    async def start(self, context: FeatureContext) -> None:
        context.on_close(self._service.close)
        context.provide(HOST_STORAGE, self._service)


def _storage_feature(config: StorageConfig) -> _StorageFeature:
    """Create the storage feature for the host composition root only."""
    return _StorageFeature(config)


__all__ = (
    "HOST_STORAGE",
    "Storage",
    "StorageClosedError",
    "StorageConfig",
    "StorageConflict",
    "StorageConflictError",
    "StorageDelete",
    "StorageError",
    "StorageMigrationError",
    "StorageMutation",
    "StoragePage",
    "StorageRecord",
    "StorageStatus",
    "StorageTransactionResult",
    "_storage_feature",
)
