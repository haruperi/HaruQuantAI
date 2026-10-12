"""Host session login lifecycle repository for host persistence subsystem.

Description:
    Provides transactional CRUD operations against `host_session`, tracking
    authentication tokens, peer metadata, expirations, and revocations.

Purpose:
    FEAT-HOST-PERSISTENCE: Host session login lifecycle persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-HOST-SESSIONS: Login lifecycle record CRUD.
      Associated: `HostSessionStore.initialize()`, `HostSessionStore.create()`,
        `HostSessionStore.list_records()`, `HostSessionStore.update_status()`
      Logging: INFO storage verification/writes and counts; DEBUG reads.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager
    from app.host.persistence.stores.host_sessions import HostSessionStore

    db = DatabaseManager(":memory:")
    store = HostSessionStore(db)
    store.initialize()
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.host.logging import get_logger
from app.host.persistence.engine import MAX_READ_LIMIT
from app.host.persistence.errors import ValidationError
from app.host.persistence.models import HostSessionRecord
from app.host.persistence.schema import ensure_host_session_schema

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class HostSessionStore:
    """CRUD for the existing singular host_session login lifecycle table."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._initialized = False

    @property
    def db_path(self) -> Path:
        """Return the storage target for service binding checks."""
        return self._db.database_path

    def initialize(self) -> None:
        """Create the identical singular schema if absent, then verify columns."""
        if self._initialized:
            return
        with self._db.transaction() as conn:
            ensure_host_session_schema(conn)
        self._initialized = True
        logger.info(
            "Host session storage verified",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS"},
        )

    def create(self, record: HostSessionRecord) -> None:
        """Insert caller-provided metadata atomically."""
        self.initialize()
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT INTO host_session (session_id,token_hash,username,peer_id,"
                "created_at_utc,expires_at_utc,revoked_at_utc,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                tuple(record.model_dump().values()),
            )
        logger.info(
            "Host session record inserted",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS"},
        )

    def list_records(
        self, *, peer_id: str, limit: int = 1000
    ) -> list[HostSessionRecord]:
        """Read a bounded set of records belonging to the requested issuer."""
        if not 1 <= limit <= MAX_READ_LIMIT:
            raise ValidationError("Invalid host session read limit")
        self.initialize()
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT * FROM host_session WHERE peer_id=? "
                "ORDER BY created_at_utc,session_id LIMIT ?",
                (peer_id, limit),
            ).fetchall()
        logger.debug(
            "Host session records read",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS", "count": len(rows)},
        )
        return [HostSessionRecord.model_validate(dict(row)) for row in rows]

    def update_status(
        self,
        *,
        peer_id: str,
        expected_status: str,
        status: str,
        revoked_at_utc: str | None,
        token_hash: str | None = None,
        username: str | None = None,
    ) -> int:
        """Conditionally update only the requested issuer and optional row filters."""
        self.initialize()
        sql = (
            "UPDATE host_session SET status=?,revoked_at_utc=? "
            "WHERE peer_id=? AND status=?"
        )
        values: list[str | None] = [status, revoked_at_utc, peer_id, expected_status]
        if token_hash is not None:
            sql += " AND token_hash=?"
            values.append(token_hash)
        if username is not None:
            sql += " AND username=?"
            values.append(username)
        with self._db.transaction() as conn:
            count = conn.execute(sql, values).rowcount
        logger.info(
            "Host session records updated",
            extra={"fr_id": "FR-HOST-PERSISTENCE-HOST-SESSIONS", "count": count},
        )
        return count
