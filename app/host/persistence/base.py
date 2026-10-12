"""Typed repository base class for host persistence subsystem.

Description:
    Provides generic, parameterized CRUD operations with optimistic concurrency
    revision tracking against the `host_entities` table.

Purpose:
    FEAT-HOST-PERSISTENCE: Scoped JSON entity CRUD and revisions.

Key Capabilities:
    - FR-HOST-PERSISTENCE-TYPED-REPOSITORY: Scoped JSON entity CRUD and revisions.
      Associated: `TypedRepository.get()`, `TypedRepository.save()`,
        `TypedRepository.delete()`, `TypedRepository.list()`
      Logging: DEBUG reads; INFO writes; WARNING revision conflicts.

Python API Usage:
    ```python
    from pydantic import BaseModel
    from app.host.persistence.base import TypedRepository
    from app.host.persistence.engine import DatabaseManager


    class MyModel(BaseModel):
        name: str


    db = DatabaseManager(":memory:")
    repo = TypedRepository(db, entity_type="custom", model_cls=MyModel)
    ```

CLI Usage:
    No direct CLI for typed repositories. Diagnostics inspects entities:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.host.logging import get_logger
from app.host.persistence.engine import (
    canonical_json,
    validate_identifier,
)
from app.host.persistence.errors import (
    CorruptDataError,
    RevisionConflictError,
)
from app.host.persistence.models import EntityRecord, Page

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class TypedRepository[T: BaseModel]:
    """Narrow, parameterized entity repository with monotonic revision concurrency."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        entity_type: str,
        model_cls: type[T],
        scope: str = "workspace",
    ) -> None:
        """Initialize TypedRepository for a given entity type and Pydantic model.

        Args:
            db: Central host DatabaseManager.
            entity_type: Categorical name of entity collection.
            model_cls: Pydantic model class for serialization/deserialization.
            scope: Default authorization or tenant scope.
        """
        validate_identifier(entity_type, "entity_type")
        validate_identifier(scope, "scope")
        self._db = db
        self.entity_type = entity_type
        self.model_cls = model_cls
        self.scope = scope

    def get(
        self,
        entity_id: str,
    ) -> T | None:
        """Retrieve and deserialize an entity by ID if present.

        Args:
            entity_id: Unique entity identifier.

        Returns:
            Deserialized Pydantic model instance, or None if absent.
        """
        logger.debug(
            "TypedRepository.get storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT payload FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()

        if row is None:
            return None

        try:
            raw_payload = json.loads(row["payload"])
            return self.model_cls.model_validate(raw_payload)
        except Exception as exc:
            msg = (
                f"Corrupt data encountered deserializing {self.entity_type}:{entity_id}"
            )
            logger.exception(msg, extra={"error": str(exc)})
            raise CorruptDataError(msg) from exc

    def get_record(
        self,
        entity_id: str,
    ) -> EntityRecord | None:
        """Retrieve full EntityRecord envelope including revision metadata.

        Args:
            entity_id: Unique entity identifier.

        Returns:
            EntityRecord record, or None if absent.
        """
        logger.debug(
            "TypedRepository.get_record storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        sql = (
            "SELECT entity_id, entity_type, scope, payload, revision, "
            "created_at_utc, updated_at_utc FROM host_entities "
            "WHERE entity_id = ? AND entity_type = ? AND scope = ?;"
        )
        params = (entity_id, self.entity_type, self.scope)

        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()

        if row is None:
            return None

        try:
            return EntityRecord(
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                scope=row["scope"],
                payload=json.loads(row["payload"]),
                revision=row["revision"],
                created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                updated_at_utc=datetime.fromisoformat(row["updated_at_utc"]),
            )
        except Exception as exc:
            msg = f"Corrupt envelope for entity {self.entity_type}:{entity_id}"
            raise CorruptDataError(msg) from exc

    def save(
        self,
        entity_id: str,
        model: T,
        *,
        expected_revision: int | None = None,
    ) -> EntityRecord:
        """Save or update entity, verifying optimistic concurrency revision.

        Args:
            entity_id: Unique entity identifier.
            model: Pydantic model payload to persist.
            expected_revision: Expected current revision for optimistic
                concurrency check.

        Returns:
            Updated EntityRecord envelope.

        Raises:
            RevisionConflictError: If expected_revision does not match persisted record.
        """
        logger.debug(
            "TypedRepository.save storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")
        payload_dict = model.model_dump(mode="json")
        payload_json = canonical_json(payload_dict)
        now_dt = datetime.now(UTC)
        now_str = now_dt.isoformat()

        def _execute(conn: sqlite3.Connection) -> EntityRecord:
            cur = conn.cursor()
            cur.execute(
                "SELECT revision, created_at_utc FROM host_entities "
                "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                (entity_id, self.entity_type, self.scope),
            )
            existing = cur.fetchone()

            if existing is not None:
                current_rev = int(existing["revision"])
                created_at = existing["created_at_utc"]
                if expected_revision is not None and expected_revision != current_rev:
                    msg = (
                        f"Revision conflict for {self.entity_type}:{entity_id}: "
                        f"expected {expected_revision}, but current is {current_rev}"
                    )
                    logger.warning(
                        msg,
                        extra={"fr_id": "FR-HOST-PERSISTENCE-REVISION-CONCURRENCY"},
                    )
                    raise RevisionConflictError(msg)

                new_rev = current_rev + 1
                cur.execute(
                    """
                    UPDATE host_entities
                    SET payload = ?, revision = ?, updated_at_utc = ?
                    WHERE entity_id = ? AND entity_type = ? AND scope = ?;
                    """,
                    (
                        payload_json,
                        new_rev,
                        now_str,
                        entity_id,
                        self.entity_type,
                        self.scope,
                    ),
                )
                logger.info(
                    "Entity updated",
                    extra={
                        "entity_id": entity_id,
                        "entity_type": self.entity_type,
                        "revision": new_rev,
                        "fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY",
                    },
                )
                return EntityRecord(
                    entity_id=entity_id,
                    entity_type=self.entity_type,
                    scope=self.scope,
                    payload=payload_dict,
                    revision=new_rev,
                    created_at_utc=datetime.fromisoformat(created_at),
                    updated_at_utc=now_dt,
                )

            # Insert new record
            if expected_revision is not None and expected_revision != 0:
                msg = (
                    f"Revision conflict on insert for {self.entity_type}:{entity_id}: "
                    f"expected {expected_revision}, record does not exist"
                )
                raise RevisionConflictError(msg)

            new_rev = 1
            cur.execute(
                """
                INSERT INTO host_entities (
                    entity_id, entity_type, scope, payload, revision,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    entity_id,
                    self.entity_type,
                    self.scope,
                    payload_json,
                    new_rev,
                    now_str,
                    now_str,
                ),
            )
            logger.info(
                "Entity created",
                extra={
                    "entity_id": entity_id,
                    "entity_type": self.entity_type,
                    "revision": new_rev,
                    "fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY",
                },
            )
            return EntityRecord(
                entity_id=entity_id,
                entity_type=self.entity_type,
                scope=self.scope,
                payload=payload_dict,
                revision=new_rev,
                created_at_utc=now_dt,
                updated_at_utc=now_dt,
            )

        with self._db.transaction() as conn:
            return _execute(conn)

    def delete(
        self,
        entity_id: str,
        *,
        expected_revision: int | None = None,
    ) -> bool:
        """Delete an entity by ID with optional expected revision check.

        Args:
            entity_id: Unique entity identifier.
            expected_revision: Optional revision concurrency assertion.

        Returns:
            True if entity was deleted; False if not found.
        """
        logger.debug(
            "TypedRepository.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        validate_identifier(entity_id, "entity_id")

        def _execute(conn: sqlite3.Connection) -> bool:
            cur = conn.cursor()
            if expected_revision is not None:
                cur.execute(
                    "SELECT revision FROM host_entities "
                    "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                    (entity_id, self.entity_type, self.scope),
                )
                row = cur.fetchone()
                if row is None:
                    return False
                curr_rev = int(row["revision"])
                if curr_rev != expected_revision:
                    msg = (
                        f"Revision conflict on delete for "
                        f"{self.entity_type}:{entity_id}: "
                        f"expected {expected_revision}, current is {curr_rev}"
                    )
                    raise RevisionConflictError(msg)

            cur.execute(
                "DELETE FROM host_entities "
                "WHERE entity_id = ? AND entity_type = ? AND scope = ?;",
                (entity_id, self.entity_type, self.scope),
            )
            return cur.rowcount > 0

        with self._db.transaction() as conn:
            return _execute(conn)

    def list(
        self,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> Page[T]:
        """List entities ordered by entity_id with keyset pagination.

        Args:
            cursor: Optional entity_id cursor representing pagination position.
            limit: Maximum items to retrieve per page (bounded 1..500).

        Returns:
            Page containing deserialized models and next cursor.
        """
        logger.debug(
            "TypedRepository.list storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-TYPED-REPOSITORY"},
        )
        clamped_limit = max(1, min(limit, 500))
        with self._db.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM host_entities "
                "WHERE entity_type = ? AND scope = ?;",
                (self.entity_type, self.scope),
            )
            total = int(cur.fetchone()[0])

            if cursor:
                cur.execute(
                    "SELECT entity_id, payload FROM host_entities "
                    "WHERE entity_type = ? AND scope = ? AND entity_id > ? "
                    "ORDER BY entity_id ASC LIMIT ?;",
                    (self.entity_type, self.scope, cursor, clamped_limit + 1),
                )
            else:
                cur.execute(
                    "SELECT entity_id, payload FROM host_entities "
                    "WHERE entity_type = ? AND scope = ? "
                    "ORDER BY entity_id ASC LIMIT ?;",
                    (self.entity_type, self.scope, clamped_limit + 1),
                )

            rows = cur.fetchall()

        has_more = len(rows) > clamped_limit
        result_rows = rows[:clamped_limit]
        items: list[T] = []

        for r in result_rows:
            raw_payload = json.loads(r["payload"])
            items.append(self.model_cls.model_validate(raw_payload))

        next_cursor = result_rows[-1]["entity_id"] if has_more and result_rows else None
        return Page(items=items, total_count=total, next_cursor=next_cursor)
