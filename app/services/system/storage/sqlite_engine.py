"""SQLite persistent storage engine with namespaced key-value tables."""

import asyncio
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any, override

from app.contracts.system.storage import StorageEngine


class SqliteStorageEngine(StorageEngine):
    """SQLite-backed persistent key-value engine with namespace isolation.

    Satisfies:
        FR-SYS-STORE_PERSISTENT_DATA: Persists binary payloads in SQLite table.
        FR-SYS-RETRIEVE_PERSISTENT_DATA: Retrieves binary payloads by key and namespace.
        FR-SYS-PURGE_NAMESPACE_DATA: Deletes keys or entire namespace partitions.
    """

    def __init__(self, db_path: Path, namespace: str = "root") -> None:
        """Initialize engine with SQLite database file path.

        Args:
            db_path: Path to .db file on disk.
            namespace: Namespace partition identifier.
        """
        self._db_path = db_path
        self._namespace = namespace
        self._initialized = False
        self._init_lock: asyncio.Lock | None = None

    @property
    def db_path(self) -> Path:
        """Return path to SQLite database file."""
        return self._db_path

    @property
    def namespace(self) -> str:
        """Return active namespace."""
        return self._namespace

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection.

        Returns:
            Configured sqlite3.Connection.
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self._db_path),
            timeout=30.0,
            check_same_thread=False,
        )
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    def _init_db_sync(self) -> None:
        """Create table and indexes if not present."""
        conn = self._get_connection()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_kv_store (
                        namespace TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value BLOB NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
                        updated_at TEXT NOT NULL DEFAULT (DATETIME('now')),
                        PRIMARY KEY (namespace, key)
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_system_kv_ns
                    ON system_kv_store(namespace);
                    """
                )
        finally:
            conn.close()

    async def initialize(self) -> None:
        """Initialize SQLite database tables and indexes asynchronously."""
        if self._initialized:
            return
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        async with self._init_lock:
            if not self._initialized:
                await asyncio.to_thread(self._init_db_sync)
                self._initialized = True

    def _get_sync(self, key: str) -> bytes | None:
        """Synchronously query binary payload by key.

        Args:
            key: Target key identifier.

        Returns:
            Binary payload if found, None otherwise.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT value FROM system_kv_store WHERE namespace = ? AND key = ?",
                (self._namespace, key),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return bytes(row[0])
        finally:
            conn.close()

    def _set_sync(self, key: str, value: bytes) -> None:
        """Synchronously upsert binary payload.

        Args:
            key: Target key identifier.
            value: Binary payload to persist.
        """
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO system_kv_store (namespace, key, value, updated_at)
                    VALUES (?, ?, ?, DATETIME('now'))
                    ON CONFLICT(namespace, key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at
                    """,
                    (self._namespace, key, value),
                )
        finally:
            conn.close()

    def _delete_sync(self, key: str) -> bool:
        """Synchronously delete key.

        Args:
            key: Target key identifier.

        Returns:
            True if row was deleted, False otherwise.
        """
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM system_kv_store WHERE namespace = ? AND key = ?",
                    (self._namespace, key),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def _list_keys_sync(self, prefix: str) -> tuple[str, ...]:
        """Synchronously list keys in namespace.

        Args:
            prefix: Key prefix filter.

        Returns:
            Tuple of matching keys.
        """
        pattern = f"{prefix}%" if prefix else "%"
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT key FROM system_kv_store
                WHERE namespace = ? AND key LIKE ?
                ORDER BY key ASC
                """,
                (self._namespace, pattern),
            )
            rows: Sequence[tuple[Any, ...]] = cursor.fetchall()
            return tuple(str(r[0]) for r in rows)
        finally:
            conn.close()

    @override
    async def get(self, key: str) -> bytes | None:
        """Retrieve binary content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            Binary payload if found, None otherwise.
        """
        await self.initialize()
        return await asyncio.to_thread(self._get_sync, key)

    @override
    async def set(self, key: str, value: bytes) -> None:
        """Store binary content for a given key.

        Args:
            key: Unique key identifier.
            value: Binary payload to persist.
        """
        await self.initialize()
        await asyncio.to_thread(self._set_sync, key, value)

    @override
    async def delete(self, key: str) -> bool:
        """Delete stored content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            True if the key was deleted, False if not found.
        """
        await self.initialize()
        return await asyncio.to_thread(self._delete_sync, key)

    @override
    async def list_keys(self, prefix: str = "") -> tuple[str, ...]:
        """List all stored keys matching optional prefix.

        Args:
            prefix: Optional key prefix filter.

        Returns:
            Tuple of matching keys.
        """
        await self.initialize()
        return await asyncio.to_thread(self._list_keys_sync, prefix)

    @override
    def partition(self, namespace: str) -> StorageEngine:
        """Return an isolated storage engine partition under a sub-namespace.

        Args:
            namespace: Sub-namespace identifier.

        Returns:
            Isolated SqliteStorageEngine partition.
        """
        ns = (
            namespace if self._namespace == "root" else f"{self._namespace}.{namespace}"
        )
        return SqliteStorageEngine(self._db_path, namespace=ns)
