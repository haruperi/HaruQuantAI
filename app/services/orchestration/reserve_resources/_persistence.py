"""Feature-local persistence for resource reservations and ledger audit receipts."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.composition.logging import get_logger
from app.contracts.orchestration.resources import (
    FiniteResourceProfile,
    LeaseStatus,
    ResourceAdmissionRequest,
    ResourceLease,
)

if TYPE_CHECKING:
    from app.contracts.workspace.persistence import PersistenceCapability

_LOGGER = get_logger("orchestration.reserve_resources.persistence")


class ResourceReservationStore:
    """Persistence adapter for durable resource leases and idempotency."""

    def __init__(
        self,
        persistence_port: PersistenceCapability | None = None,
        database_path: str = ":memory:",
    ) -> None:
        """Initialize the resource reservation store.

        Args:
            persistence_port: Optional workspace persistence port.
            database_path: SQLite path for local/standalone operations.
        """
        self._persistence_port = persistence_port
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the reservation and lease tables if they do not exist."""
        with self._connection:
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS resource_leases (
                lease_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                work_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                parent_lease_id TEXT,
                root_lease_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                memory_bytes INTEGER NOT NULL,
                thread_count INTEGER NOT NULL,
                temp_disk_bytes INTEGER NOT NULL,
                vram_bytes INTEGER NOT NULL,
                compile_slots INTEGER NOT NULL,
                ready_descriptors INTEGER NOT NULL,
                prefetch_chunks INTEGER NOT NULL,
                buffer_bytes INTEGER NOT NULL,
                cache_bytes INTEGER NOT NULL
                )"""
            )
            self._connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_idempotency_key
                ON resource_leases (idempotency_key)"""
            )

    def record_lease(
        self,
        request: ResourceAdmissionRequest,
        lease: ResourceLease,
    ) -> None:
        """Durable persistence for an admitted resource lease.

        Args:
            request: The admission request.
            lease: The created resource lease.
        """
        _LOGGER.debug(
            "Persisting lease %s (idempotency_key=%s)",
            lease.lease_id,
            request.idempotency_key,
        )
        p = lease.admitted_profile
        with self._connection:
            self._connection.execute(
                """INSERT OR REPLACE INTO resource_leases (
                    lease_id, request_id, owner_id, work_id, idempotency_key,
                    parent_lease_id, root_lease_id, generation, status, created_at,
                    memory_bytes, thread_count, temp_disk_bytes, vram_bytes,
                    compile_slots, ready_descriptors, prefetch_chunks,
                    buffer_bytes, cache_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    lease.lease_id,
                    request.request_id,
                    request.owner_id,
                    request.work_id,
                    request.idempotency_key,
                    lease.parent_lease_id,
                    lease.root_lease_id,
                    lease.generation,
                    lease.status.value,
                    lease.created_at_utc.isoformat(),
                    p.memory_bytes,
                    p.thread_count,
                    p.temp_disk_bytes,
                    p.vram_bytes,
                    p.compile_slots,
                    p.ready_descriptors,
                    p.prefetch_chunks,
                    p.buffer_bytes,
                    p.cache_bytes,
                ),
            )

    def get_lease_by_idempotency(self, idempotency_key: str) -> ResourceLease | None:
        """Lookup an existing lease by idempotency key.

        Args:
            idempotency_key: The idempotency identity.

        Returns:
            Matching ResourceLease or None.
        """
        cursor = self._connection.execute(
            """SELECT lease_id, request_id, owner_id, work_id, parent_lease_id,
                      root_lease_id, generation, status, created_at,
                      memory_bytes, thread_count, temp_disk_bytes, vram_bytes,
                      compile_slots, ready_descriptors, prefetch_chunks,
                      buffer_bytes, cache_bytes
               FROM resource_leases WHERE idempotency_key = ?""",
            (idempotency_key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_lease(row)

    def get_lease(self, lease_id: str) -> ResourceLease | None:
        """Lookup an existing lease by lease ID.

        Args:
            lease_id: The lease identifier.

        Returns:
            Matching ResourceLease or None.
        """
        cursor = self._connection.execute(
            """SELECT lease_id, request_id, owner_id, work_id, parent_lease_id,
                      root_lease_id, generation, status, created_at,
                      memory_bytes, thread_count, temp_disk_bytes, vram_bytes,
                      compile_slots, ready_descriptors, prefetch_chunks,
                      buffer_bytes, cache_bytes
               FROM resource_leases WHERE lease_id = ?""",
            (lease_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_lease(row)

    def update_lease_status(self, lease_id: str, status: LeaseStatus) -> bool:
        """Update the status of an existing lease.

        Args:
            lease_id: The lease identifier.
            status: The new status.

        Returns:
            True if row was updated, False otherwise.
        """
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE resource_leases SET status = ? WHERE lease_id = ?",
                (status.value, lease_id),
            )
            return cursor.rowcount > 0

    def _row_to_lease(self, row: tuple[Any, ...]) -> ResourceLease:
        """Convert a database row tuple to ResourceLease.

        Args:
            row: Database row tuple.

        Returns:
            Constructed ResourceLease object.
        """
        (
            lease_id,
            request_id,
            owner_id,
            work_id,
            parent_lease_id,
            root_lease_id,
            generation,
            status_str,
            created_at_str,
            mem,
            threads,
            disk,
            vram,
            compile_slots,
            ready_desc,
            prefetch,
            buffer_bytes,
            cache_bytes,
        ) = row

        profile = FiniteResourceProfile(
            memory_bytes=mem,
            thread_count=threads,
            temp_disk_bytes=disk,
            vram_bytes=vram,
            compile_slots=compile_slots,
            ready_descriptors=ready_desc,
            prefetch_chunks=prefetch,
            buffer_bytes=buffer_bytes,
            cache_bytes=cache_bytes,
        )
        return ResourceLease(
            lease_id=lease_id,
            request_id=request_id,
            owner_id=owner_id,
            work_id=work_id,
            parent_lease_id=parent_lease_id,
            root_lease_id=root_lease_id,
            admitted_profile=profile,
            generation=generation,
            status=LeaseStatus(status_str),
            created_at_utc=datetime.fromisoformat(created_at_str).replace(tzinfo=UTC),
        )

    def close(self) -> None:
        """Close the underlying database connection."""
        try:
            self._connection.close()
        except Exception:
            _LOGGER.exception("Error closing resource reservation store")
