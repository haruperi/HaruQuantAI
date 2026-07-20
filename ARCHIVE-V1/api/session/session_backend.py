"""Session metadata and lease backend abstractions.

Purpose:
    Session metadata and lease backend abstractions.

Classes:
    SessionMetadata: Public class defined by this module.
    SessionRuntimeStore: Public class defined by this module.
    SQLiteSessionRuntimeStore: Public class defined by this module.

Functions:
    _parse_optional_datetime: Internal helper function defined by this module.

Notes:
    External-facing exports are collected in the owning package __init__.py.
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol


@dataclass(frozen=True)
class SessionMetadata:
    """Persistent simulator session identity and ownership metadata."""

    session_id: int
    user_id: int
    status: str
    config: dict[str, Any]
    current_bar_index: int
    total_bars: int | None
    runtime_owner: str | None
    lease_expires_at: datetime | None
    last_heartbeat_at: datetime | None
    raw: dict[str, Any]

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> SessionMetadata:
        """Public function for session_backend.from_record."""
        return cls(
            session_id=int(record["session_id"]),
            user_id=int(record["user_id"]),
            status=str(record.get("status") or ""),
            config=dict(record.get("config") or {}),
            current_bar_index=int(record.get("current_bar_index") or 0),
            total_bars=(
                int(record["total_bars"])
                if record.get("total_bars") is not None
                else None
            ),
            runtime_owner=(
                str(record.get("runtime_owner"))
                if record.get("runtime_owner")
                else None
            ),
            lease_expires_at=_parse_optional_datetime(record.get("lease_expires_at")),
            last_heartbeat_at=_parse_optional_datetime(record.get("last_heartbeat_at")),
            raw=dict(record),
        )

    def as_record(self) -> dict[str, Any]:
        """Public function for session_backend.as_record."""
        return dict(self.raw)


def _parse_optional_datetime(value: Any) -> datetime | None:
    """Internal function for session_backend._parse_optional_datetime."""
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


class SessionRuntimeStore(Protocol):
    """Backend abstraction for session metadata and active-runtime leases."""

    def get_metadata(self, session_id: int) -> SessionMetadata | None:
        """Return metadata for a simulator session."""
        ...

    def create_metadata(self, metadata: SessionMetadata) -> None:
        """Create metadata for a simulator session."""
        ...

    def update_metadata(self, session_id: int, patch: dict[str, Any]) -> None:
        """Patch metadata for a simulator session."""
        ...

    def acquire_lease(
        self,
        session_id: int,
        worker_id: str,
        ttl_seconds: int,
    ) -> bool:
        """Acquire a runtime lease for a simulator session."""
        ...

    def renew_lease(
        self,
        session_id: int,
        worker_id: str,
        ttl_seconds: int,
    ) -> bool:
        """Renew an existing runtime lease for a simulator session."""
        ...

    def release_lease(self, session_id: int, worker_id: str) -> None:
        """Release a runtime lease for a simulator session."""
        ...

    def clear_expired_leases(self) -> int:
        """Clear expired runtime leases and return the affected row count."""
        ...


class SQLiteSessionRuntimeStore:
    """SQLite-backed metadata and lease manager for simulator sessions."""

    def __init__(self, db_manager: Any) -> None:
        """Internal function for session_backend.__init__."""
        self._db_manager = db_manager

    def get_metadata(self, session_id: int) -> SessionMetadata | None:
        """Public function for session_backend.get_metadata."""
        record = self._db_manager.get_simulation_session(int(session_id))
        if not record:
            return None
        return SessionMetadata.from_record(record)

    def create_metadata(self, metadata: SessionMetadata) -> None:
        """Public function for session_backend.create_metadata."""
        patch = {
            "status": metadata.status,
            "current_bar_index": metadata.current_bar_index,
            "total_bars": metadata.total_bars,
            "config": metadata.config,
            "runtime_owner": metadata.runtime_owner,
            "lease_expires_at": metadata.lease_expires_at,
            "last_heartbeat_at": metadata.last_heartbeat_at,
        }
        self.update_metadata(metadata.session_id, patch)

    def update_metadata(self, session_id: int, patch: dict[str, Any]) -> None:
        """Public function for session_backend.update_metadata."""
        if not patch:
            return
        self._db_manager.update_simulation_session(int(session_id), **patch)

    def acquire_lease(
        self,
        session_id: int,
        worker_id: str,
        ttl_seconds: int,
    ) -> bool:
        """Public function for session_backend.acquire_lease."""
        return self._upsert_lease(
            session_id=session_id,
            worker_id=worker_id,
            ttl_seconds=ttl_seconds,
            allow_current_owner=True,
        )

    def renew_lease(
        self,
        session_id: int,
        worker_id: str,
        ttl_seconds: int,
    ) -> bool:
        """Public function for session_backend.renew_lease."""
        return self._upsert_lease(
            session_id=session_id,
            worker_id=worker_id,
            ttl_seconds=ttl_seconds,
            allow_current_owner=True,
        )

    def release_lease(self, session_id: int, worker_id: str) -> None:
        """Public function for session_backend.release_lease."""
        conn = sqlite3.connect(self._db_manager.db_path, timeout=5.0)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                """
                UPDATE simulation_sessions
                SET runtime_owner = NULL,
                    lease_expires_at = NULL,
                    last_heartbeat_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND (runtime_owner IS NULL OR runtime_owner = ?)
                """,
                (int(session_id), str(worker_id)),
            )
            conn.commit()
        finally:
            conn.close()

    def clear_expired_leases(self) -> int:
        """Public function for session_backend.clear_expired_leases."""
        now_text = self._format_timestamp(datetime.now(UTC))
        conn = sqlite3.connect(self._db_manager.db_path, timeout=5.0)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                """
                UPDATE simulation_sessions
                SET runtime_owner = NULL,
                    lease_expires_at = NULL,
                    last_heartbeat_at = NULL,
                    status = CASE
                        WHEN status = 'running' THEN 'paused'
                        ELSE status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE lease_expires_at IS NOT NULL
                  AND lease_expires_at <= ?
                """,
                (now_text,),
            )
            conn.commit()
            return int(cursor.rowcount or 0)
        finally:
            conn.close()

    def _upsert_lease(
        self,
        *,
        session_id: int,
        worker_id: str,
        ttl_seconds: int,
        allow_current_owner: bool,
    ) -> bool:
        """Internal function for session_backend._upsert_lease."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=max(int(ttl_seconds), 1))
        now_text = self._format_timestamp(now)
        expires_text = self._format_timestamp(expires_at)
        params = [
            str(worker_id),
            expires_text,
            now_text,
            int(session_id),
            str(worker_id),
            now_text,
        ]
        owner_clause = "OR runtime_owner = ?" if allow_current_owner else ""
        conn = sqlite3.connect(self._db_manager.db_path, timeout=5.0)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                f"""
                UPDATE simulation_sessions
                SET runtime_owner = ?,
                    lease_expires_at = ?,
                    last_heartbeat_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND (
                        runtime_owner IS NULL
                        {owner_clause}
                        OR lease_expires_at IS NULL
                        OR lease_expires_at <= ?
                  )
                """,
                params,
            )
            conn.commit()
            return int(cursor.rowcount or 0) == 1
        finally:
            conn.close()

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        """Internal function for session_backend._format_timestamp."""
        normalized = value.astimezone(UTC).replace(tzinfo=None)
        return normalized.isoformat()
