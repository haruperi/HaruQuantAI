"""Host storage owner: SQLite versioned records, migrations, and CAS.

This file is the single owner of the ``host.storage@1`` capability:
generic ``(namespace, key)`` records carrying a revision, schema
version, payload bytes, and UTC stamps, with compare-and-swap updates,
all-or-nothing transactions, deterministic bounded pagination, and
forward-only migrations on SQLite. Per the one-file-owner rule, all
SQLite details for this capability live here and nowhere else.

It does not own artifact content layout (``host.artifacts``), job
lifecycle semantics (``host.jobs``), plugin schemas, or UI state; it
stores opaque payload bytes only.

Persistence safety:
- Tests use isolated temporary stores only; no hard-coded or shared
  production path is ever touched.
- Callers see typed records and results, never SQL statements,
  connections, cursors, or filesystem paths beyond the configured
  database path.
- ARCH-017: this is the only module permitted to import ``sqlite3``.
- ARCH-019: this module and ``app/host/artifacts.py`` are the only
  filesystem mutators in the host; here mutation is limited to
  creating the database file's parent directory.
- Every operation serializes onto one owned single-writer thread, and
  ``close()`` drains that writer before returning.
"""

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
    """Base error for storage failures.

    Wraps engine-level failures such as being unable to open or
    migrate a database. Compare-and-swap mismatches are reported
    through ``StorageTransactionResult.conflicts`` instead of this
    hierarchy.
    """


class StorageConflictError(StorageError):
    """CAS expectation was not satisfied by the stored revision.

    Part of the public error hierarchy for callers that prefer raising;
    the engine itself surfaces CAS failures on the transaction result
    so a whole batch can fail atomically without an exception.
    """


class StorageClosedError(StorageError):
    """Operation attempted on a closed store.

    Raised synchronously before submission once ``close()`` has run,
    including from the async facade methods.
    """


class StorageMigrationError(StorageError):
    """Schema migration failed or the database is too new to open.

    Raised when a migration statement fails (that migration rolls
    back) or when stored schema versions are newer than the newest
    version this code supports; both cases fail closed.
    """


@dataclass(frozen=True, slots=True)
class StorageRecord:
    """Immutable versioned storage record.

    Attributes:
        namespace: Non-empty namespace owning this key space.
        key: Non-empty key, unique within its namespace.
        revision: Monotonic revision starting at 1 on insert and
            incremented on every update.
        schema_version: Caller-declared payload schema version (>= 1).
        payload_bytes: Opaque application payload.
        created_at_utc: ISO-8601 UTC stamp of the first write.
        updated_at_utc: ISO-8601 UTC stamp of the latest write.
    """

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
    """Requested record upsert with optional compare-and-swap revision.

    Attributes:
        namespace: Target namespace (non-empty string).
        key: Target key (non-empty string).
        schema_version: Payload schema version to write (>= 1).
        payload_bytes: Opaque payload to store.
        expected_revision: Optional CAS guard. ``None`` applies
            unconditionally; a positive value must match the stored
            revision; ``0`` requires the record to be absent.
    """

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
    """Requested record deletion with optional compare-and-swap revision.

    Attributes:
        namespace: Target namespace (non-empty string).
        key: Target key (non-empty string).
        expected_revision: Optional CAS guard that must equal the
            stored revision (>= 1). ``None`` deletes unconditionally
            but conflicts when the record is already absent.
    """

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
    """Record conflict information on CAS failure.

    Attributes:
        namespace: Namespace of the conflicting record.
        key: Key of the conflicting record.
        expected_revision: Revision the caller required, where ``0``
            means "expected absent" and ``None`` means unconditional.
        actual_revision: Revision actually stored, or ``None`` when no
            record exists.
    """

    namespace: str
    key: str
    expected_revision: int | None
    actual_revision: int | None


@dataclass(frozen=True, slots=True)
class StorageTransactionResult:
    """Result of an all-or-nothing storage transaction.

    Attributes:
        committed: Whether every mutation was applied atomically.
        records: Resulting records for applied upserts, in order;
            deletes emit no records. Empty when not committed.
        conflicts: CAS mismatches that rolled the transaction back;
            empty when committed.
    """

    committed: bool
    records: tuple[StorageRecord, ...] = ()
    conflicts: tuple[StorageConflict, ...] = ()


@dataclass(frozen=True, slots=True)
class StoragePage:
    """Deterministic page of scanned records.

    Attributes:
        records: Records in ascending key order, at most the bounded
            page size.
        next_token: Key to pass as ``after_key`` for the next page, or
            ``None`` when the scan is exhausted.
        total_count: Total records in the namespace (honoring the
            prefix filter), independent of pagination.
    """

    records: tuple[StorageRecord, ...]
    next_token: str | None = None
    total_count: int = 0


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration for SQLite storage provider.

    Attributes:
        database_path: Database file path, or the string
            ``":memory:"`` for an in-memory database (no WAL journal).
        busy_timeout_ms: SQLite busy timeout in milliseconds, applied
            both at connect time and as the ``busy_timeout`` pragma.
        max_page_size: Upper bound clamping every requested scan page
            size.
    """

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
    """Public capability protocol for durable record persistence.

    Contract: generic ``(namespace, key)`` records with revision,
    schema version, payload bytes, and UTC stamps; compare-and-swap
    via ``expected_revision`` (``0`` expects absence); all-or-nothing
    transactions returning immutable results; deterministic
    key-ordered bounded pagination; and fail-closed behavior on
    corrupt databases and unsupported newer schema versions.

    Concurrency: implementations own exactly one single-writer thread.
    Both the synchronous methods and the async facade serialize onto
    it (executing inline only when already on that thread), and
    ``close()`` drains the writer before returning.
    """

    def get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record by namespace and key, or None if absent.

        Runs on the owned writer thread.

        Args:
            namespace: Namespace to read from.
            key: Exact key to read.

        Returns:
            The stored record, or ``None`` when no such record exists.

        Raises:
            StorageClosedError: If the store is closed.
        """
        ...

    def commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit an all-or-nothing batch of mutations with CAS checks.

        Runs on the owned writer thread; either every mutation applies
        in one transaction or none do.

        Args:
            mutations: Upserts and deletes to apply in order.

        Returns:
            The immutable transaction outcome; ``committed`` is false
            exactly when CAS conflicts were found, in which case the
            batch is rolled back and the conflicts are reported on the
            result.
        """
        ...

    def scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Deterministically scan records in a namespace by key ASC.

        Runs on the owned writer thread.

        Args:
            namespace: Namespace to scan.
            prefix: Optional key prefix filter.
            limit: Requested page size, clamped to at least 1 and at
                most ``StorageConfig.max_page_size``.
            after_key: Exclusive lower key bound for pagination; pass
                the previous page's ``next_token``.

        Returns:
            One page of records in ascending key order, with the total
            count for the namespace and prefix.

        Raises:
            StorageClosedError: If the store is closed.
        """
        ...

    async def async_get_record(self, namespace: str, key: str) -> StorageRecord | None:
        """Retrieve a record on the owned writer thread (event-loop safe).

        The read is submitted to the single owned writer thread so the
        event loop never blocks on SQLite; it executes inline only
        when already on that thread.

        Args:
            namespace: Namespace to read from.
            key: Exact key to read.

        Returns:
            The stored record, or ``None`` when no such record exists.

        Raises:
            StorageClosedError: If the store is closed before
                submission.
        """
        ...

    async def async_commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations on the owned writer thread (event-loop safe).

        Semantics match ``commit_transaction``; the work is submitted
        to the owned writer thread so the event loop never blocks on
        SQLite.

        Args:
            mutations: Upserts and deletes to apply in order.

        Returns:
            The immutable transaction outcome; conflicts roll the
            whole batch back without raising.

        Raises:
            StorageClosedError: If the store is closed before
                submission.
        """
        ...

    async def async_scan_records(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        limit: int = 50,
        after_key: str | None = None,
    ) -> StoragePage:
        """Deterministically scan records off the event loop.

        Semantics match ``scan_records``; the scan runs on the owned
        writer thread.

        Args:
            namespace: Namespace to scan.
            prefix: Optional key prefix filter.
            limit: Requested page size, clamped to configuration
                bounds.
            after_key: Exclusive lower key bound for pagination.

        Returns:
            One page of records in ascending key order with the total
            count for the namespace and prefix.

        Raises:
            StorageClosedError: If the store is closed before
                submission.
        """
        ...

    def status(self) -> StorageStatus:
        """Return migration and readiness status.

        Runs on the owned writer thread.

        Returns:
            The applied migration versions and readiness flag; a
            closed store reports version 0, no migrations, and
            ``ready=False``.
        """
        ...

    def close(self) -> None:
        """Flush and safely close the storage engine.

        Marks the store closed so subsequent operations (sync or
        async) raise ``StorageClosedError`` before submission, then
        drains the owned writer thread.
        """
        ...


@dataclass(frozen=True, slots=True)
class StorageStatus:
    """Immutable migration/readiness status of the storage engine.

    Attributes:
        schema_version: Highest applied migration version, or 0 when
            none are applied or the engine is closed.
        applied_migrations: Applied migration versions, ascending.
        ready: Whether the engine is open and serving operations.
    """

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
    """Private SQLite implementation of Storage protocol.

    Concurrency model: one dedicated executor thread owns the
    connection, and every operation (sync or async) serializes onto it
    under an RLock. File databases open with WAL journaling,
    ``foreign_keys = ON``, a ``busy_timeout`` pragma, and explicit
    ``BEGIN IMMEDIATE`` transactions. Corrupt databases and
    newer-than-supported schema versions fail closed at open.
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize and migrate the SQLite database.

        Creates the parent directory for file-backed databases, starts
        the single-writer executor, configures pragmas, and applies
        migrations. In-memory databases skip WAL journaling.

        Args:
            config: Path, timeout, and page-size configuration.

        Raises:
            StorageError: If opening or migrating fails; the writer
                thread is shut down before raising.
        """
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
        """Apply idempotent forward-only migrations.

        Each unapplied migration runs inside ``BEGIN IMMEDIATE`` and
        appends its version to the ``schema_migrations`` history table
        on success; a failed statement rolls that migration back. A
        database recording versions newer than the newest supported
        version fails closed instead of opening.
        """
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
        """Retrieve a record by namespace and key on the writer thread.

        Args:
            namespace: Namespace to read from.
            key: Exact key to read.

        Returns:
            The stored record, or ``None`` when absent.

        Raises:
            StorageClosedError: If the store is closed.
        """
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
        """Check optimistic concurrency expectations for one operation.

        ``expected_revision`` 0 expects absence; a delete with no
        expectation conflicts when the record is already gone.
        """
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
        """Apply an individual record insertion or update.

        Inserts at revision 1 with a fresh creation stamp; updates
        increment the stored revision and preserve the original
        creation stamp.
        """
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
        """Commit mutations on the owned writer thread (blocking).

        Args:
            mutations: Upserts and deletes to apply in order.

        Returns:
            The immutable transaction outcome.

        Raises:
            StorageClosedError: If the store is closed.
        """
        return self._on_writer(lambda: self._commit_transaction_impl(mutations))

    def _commit_transaction_impl(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations and deletes in an atomic transaction.

        Checks every CAS expectation inside ``BEGIN IMMEDIATE``; any
        mismatch rolls the whole batch back and reports the conflicts.
        On success all writes commit together under a single
        ``updated_at_utc`` stamp.

        Args:
            mutations: Upserts and deletes to apply in order.

        Returns:
            The immutable transaction outcome.

        Raises:
            StorageClosedError: If the store is closed.
        """
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
        """Scan records on the owned writer thread (blocking).

        Args:
            namespace: Namespace to scan.
            prefix: Optional key prefix filter.
            limit: Requested page size, clamped to configuration
                bounds.
            after_key: Exclusive lower key bound for pagination.

        Returns:
            One page of records in ascending key order with the total
            count for the namespace and prefix.

        Raises:
            StorageClosedError: If the store is closed.
        """
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
        """Scan records in deterministic key order with pagination.

        Fetches one row beyond the bounded limit to detect a next
        page, uses the last returned key as the ``next_token``, and
        computes the namespace/prefix total separately from paging.
        """
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
        """Return migration and readiness status from the writer thread.

        Returns:
            Applied migrations and readiness; a closed store reports
            version 0 with ``ready=False``.
        """
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
        """Retrieve a record on the owned writer thread.

        Raises ``StorageClosedError`` synchronously when already
        closed; otherwise the read executes inline on the writer
        thread or is awaited there without blocking the event loop.
        """
        return await self._await_on_writer(
            lambda: self._get_record_impl(namespace, key)
        )

    @override
    async def async_commit_transaction(
        self, mutations: Sequence[StorageMutation | StorageDelete]
    ) -> StorageTransactionResult:
        """Commit mutations on the owned writer thread.

        All-or-nothing CAS semantics as ``commit_transaction``, with
        submission to the writer thread so the caller's event loop
        stays responsive.
        """
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
        """Deterministically scan records on the owned writer thread.

        Key-ordered bounded pagination as ``scan_records``, executed
        off the caller's event loop.
        """
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
        """Run a storage operation on the owned writer thread (async).

        Mirrors ``_on_writer`` for coroutines: executes inline when
        already on the writer thread, otherwise wraps the submitted
        work as an awaitable future.
        """
        if self._closed:
            raise StorageClosedError("Storage is closed")
        if threading.get_ident() == self._writer_ident:
            return fn()
        return await asyncio.wrap_future(self._writer.submit(fn))

    @override
    def close(self) -> None:
        """Safely close the connection and drain the writer thread.

        Idempotent: the first call closes the connection and blocks
        until queued writer work finishes; later calls are no-ops.
        Operations attempted afterwards raise ``StorageClosedError``.
        """
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
    """Feature wiring the SQLite storage service into the host runtime."""

    spec = FeatureSpec(
        "host.storage",
        provides=frozenset({HOST_STORAGE}),
        description="SQLite-backed versioned records and CAS transactions",
    )

    def __init__(self, config: StorageConfig) -> None:
        """Construct the feature and its private storage service."""
        self._service = _SqliteStorage(config)

    async def start(self, context: FeatureContext) -> None:
        """Provide HOST_STORAGE and register close-on-shutdown."""
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
