"""Domain persistence module for Persistence domain control-plane state.

Purpose:
    Owns SQLite DDL schemas, parameterized SQL operations, connection lifecycle,
    WAL mode, and transaction management under namespace `persistence.v1`.
    Covers tables for schema migrations, immutable artifact catalog/lineage,
    project databanks and memberships, databank column views, and retention
    audit.

Invariants:
    * WAL mode enabled with synchronous=NORMAL, foreign_keys=ON,
      busy_timeout=5000ms.
    * All mutations are transactional and parameterized; raw connections
      never escape.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.contracts.persistence import (
    ArtifactMetadata,
    ArtifactRecord,
    AutoSyncPolicy,
    ColumnConfig,
    DatabankMemberRecord,
    DatabankNotFoundError,
    DatabankRecord,
    DatabankViewConfig,
    DuplicateMemberError,
    MigrationRecord,
    RankingDirection,
    SampleType,
)
from app.kernel.logging import get_logger

logger = get_logger(__name__)

SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS persistence_schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS persistence_artifacts (
    artifact_id TEXT PRIMARY KEY,
    sha256_hash TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_persistence_artifacts_hash
ON persistence_artifacts (sha256_hash);

CREATE TABLE IF NOT EXISTS persistence_artifact_lineage (
    parent_artifact_id TEXT NOT NULL,
    child_artifact_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL DEFAULT 'derived_from',
    PRIMARY KEY (parent_artifact_id, child_artifact_id),
    FOREIGN KEY (parent_artifact_id)
        REFERENCES persistence_artifacts(artifact_id) ON DELETE RESTRICT,
    FOREIGN KEY (child_artifact_id)
        REFERENCES persistence_artifacts(artifact_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS persistence_databanks (
    project_name TEXT NOT NULL,
    databank_name TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1000,
    default_view TEXT NOT NULL DEFAULT 'Default',
    auto_sync_policy TEXT NOT NULL DEFAULT 'never',
    created_at_utc TEXT NOT NULL,
    PRIMARY KEY (project_name, databank_name)
);

CREATE TABLE IF NOT EXISTS persistence_databank_members (
    project_name TEXT NOT NULL,
    databank_name TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    fitness REAL NOT NULL DEFAULT 0.0,
    ranking_value REAL NOT NULL DEFAULT 0.0,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    annotations_json TEXT NOT NULL DEFAULT '{}',
    added_at_utc TEXT NOT NULL,
    PRIMARY KEY (project_name, databank_name, artifact_id),
    FOREIGN KEY (project_name, databank_name)
        REFERENCES persistence_databanks(project_name, databank_name)
        ON DELETE CASCADE,
    FOREIGN KEY (artifact_id)
        REFERENCES persistence_artifacts(artifact_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_databank_members_ranking
ON persistence_databank_members (project_name, databank_name, ranking_value DESC);

CREATE TABLE IF NOT EXISTS persistence_databank_views (
    view_name TEXT PRIMARY KEY,
    scope TEXT NOT NULL DEFAULT 'global',
    layout_json TEXT NOT NULL DEFAULT '{}',
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS persistence_retention_audit (
    operation_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    purged_at_utc TEXT NOT NULL,
    PRIMARY KEY (operation_id, artifact_id)
);
"""


def get_connection(database_path: Path, timeout: float = 5.0) -> sqlite3.Connection:
    """Create and configure a SQLite connection with WAL mode and PRAGMAs."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(
        database_path,
        timeout=timeout,
        autocommit=True,
    )
    try:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON;")
        con.execute("PRAGMA busy_timeout=5000;")
        if str(database_path) != ":memory:":
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("PRAGMA synchronous=NORMAL;")
        return con
    except Exception:
        con.close()
        raise


def initialize_persistence_schema(database_path: Path) -> None:
    """Initialize the persistence control-plane schema if not already present."""
    con = get_connection(database_path)
    try:
        con.executescript(SCHEMA_SQL)
    finally:
        con.close()


class PersistenceDatabaseManager:
    """Encapsulates SQL operations and transactions on the database."""

    def __init__(self, database_path: Path) -> None:
        """Initialize the database manager with a target database path."""
        self._database_path = database_path
        initialize_persistence_schema(database_path)

    @property
    def database_path(self) -> Path:
        """Return the target database path."""
        return self._database_path

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection]:
        """Managed transaction context with automatic commit or rollback."""
        con = get_connection(self._database_path)
        try:
            con.execute("BEGIN IMMEDIATE;")
            yield con
            con.execute("COMMIT;")
        except Exception:
            with suppress(sqlite3.Error):
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def execute_query(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Execute a read-only query and return row dictionaries."""
        con = get_connection(self._database_path)
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()

    def execute_mutation(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Execute a mutation SQL statement and commit immediately."""
        with self.transaction() as con:
            cur = con.cursor()
            cur.execute(sql, params)
            return cur.rowcount

    def execute_script(self, sql_script: str) -> None:
        """Execute multiple SQL statements in a script."""
        with self.transaction() as con:
            con.executescript(sql_script)

    def checkpoint(self) -> None:
        """Force a WAL checkpoint to truncate wal journal and commit pages."""
        con = get_connection(self._database_path)
        try:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            con.close()

    def hot_snapshot(self, destination_path: Path) -> None:
        """Create an atomic SQLite point-in-time snapshot using VACUUM INTO."""
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if destination_path.exists():
            destination_path.unlink()
        con = get_connection(self._database_path)
        try:
            con.execute("VACUUM INTO ?;", (str(destination_path),))
        finally:
            con.close()

    def verify_sqlite_integrity(self, database_path: Path) -> None:
        """Execute PRAGMA integrity_check on a database file."""
        con = get_connection(database_path, timeout=5.0)
        try:
            cur = con.cursor()
            cur.execute("PRAGMA integrity_check;")
            rows = cur.fetchall()
            if not rows or rows[0][0] != "ok":
                msg = f"Database integrity check failed: {rows}"
                raise sqlite3.DatabaseError(msg)
        finally:
            con.close()

    def restore_database(self, source_path: Path) -> None:
        """Restore active database from source snapshot file using SQLite backup API."""
        self.checkpoint()
        source_con = get_connection(source_path, timeout=5.0)
        target_con = get_connection(self._database_path, timeout=10.0)
        try:
            with target_con:
                source_con.backup(target_con)
        finally:
            source_con.close()
            target_con.close()
        self.checkpoint()

    # -----------------------------------------------------------------------
    # Migrations CRUD
    # -----------------------------------------------------------------------

    def get_applied_migrations(self) -> list[MigrationRecord]:
        """Fetch all applied migrations ordered by version ascending."""
        sql = (
            "SELECT version, name, checksum, applied_at_utc "
            "FROM persistence_schema_migrations "
            "ORDER BY version ASC;"
        )
        rows = self.execute_query(sql)
        return [
            MigrationRecord(
                version=int(r["version"]),
                name=str(r["name"]),
                checksum=str(r["checksum"]),
                applied_at_utc=datetime.fromisoformat(r["applied_at_utc"]),
            )
            for r in rows
        ]

    # -----------------------------------------------------------------------
    # Artifacts & Lineage CRUD
    # -----------------------------------------------------------------------

    def insert_artifact(
        self,
        artifact_id: str,
        sha256_hash: str,
        media_type: str,
        *,
        size_bytes: int,
        metadata: ArtifactMetadata,
        created_at_utc: datetime,
        parent_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        """Insert a new artifact and record lineage within a transaction.

        Idempotent: If an artifact with artifact_id already exists, return the existing
        record without rewriting lineage or raising an integrity error.
        """
        meta_dict = {
            "media_type": metadata.media_type,
            "description": metadata.description,
            "author": metadata.author,
            "tags": list(metadata.tags),
            "custom": dict(metadata.custom),
        }
        with self.transaction() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT artifact_id, sha256_hash, media_type, size_bytes, "
                "metadata_json, created_at_utc FROM persistence_artifacts "
                "WHERE artifact_id = ?;",
                (artifact_id,),
            )
            row = cur.fetchone()
            if row is not None:
                meta_json = json.loads(row[4])
                existing_meta = ArtifactMetadata(
                    media_type=meta_json.get("media_type", row[2]),
                    description=meta_json.get("description", ""),
                    author=meta_json.get("author", "system"),
                    tags=tuple(meta_json.get("tags", ())),
                    custom=meta_json.get("custom", {}),
                )
                cur.execute(
                    "SELECT parent_artifact_id FROM persistence_artifact_lineage "
                    "WHERE child_artifact_id = ?;",
                    (artifact_id,),
                )
                p_ids = tuple(r[0] for r in cur.fetchall())
                return ArtifactRecord(
                    artifact_id=row[0],
                    sha256_hash=row[1],
                    media_type=row[2],
                    size_bytes=int(row[3]),
                    created_at_utc=datetime.fromisoformat(row[5]),
                    metadata=existing_meta,
                    parent_ids=p_ids,
                )

            cur.execute(
                "INSERT INTO persistence_artifacts ("
                "artifact_id, sha256_hash, media_type, size_bytes, "
                "metadata_json, created_at_utc) VALUES (?, ?, ?, ?, ?, ?);",
                (
                    artifact_id,
                    sha256_hash,
                    media_type,
                    size_bytes,
                    json.dumps(meta_dict),
                    created_at_utc.isoformat(),
                ),
            )
            for parent_id in parent_ids:
                cur.execute(
                    "INSERT INTO persistence_artifact_lineage "
                    "(parent_artifact_id, child_artifact_id) VALUES (?, ?);",
                    (parent_id, artifact_id),
                )
        return ArtifactRecord(
            artifact_id=artifact_id,
            sha256_hash=sha256_hash,
            media_type=media_type,
            size_bytes=size_bytes,
            created_at_utc=created_at_utc,
            metadata=metadata,
            parent_ids=tuple(parent_ids),
        )

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        """Fetch artifact record by artifact_id."""
        sql = (
            "SELECT artifact_id, sha256_hash, media_type, size_bytes, "
            "metadata_json, created_at_utc FROM persistence_artifacts "
            "WHERE artifact_id = ?;"
        )
        rows = self.execute_query(sql, (artifact_id,))
        if not rows:
            return None
        r = rows[0]
        meta_json = json.loads(r["metadata_json"])
        meta = ArtifactMetadata(
            media_type=meta_json.get("media_type", r["media_type"]),
            description=meta_json.get("description", ""),
            author=meta_json.get("author", "system"),
            tags=tuple(meta_json.get("tags", ())),
            custom=meta_json.get("custom", {}),
        )
        lineage_sql = (
            "SELECT parent_artifact_id FROM persistence_artifact_lineage "
            "WHERE child_artifact_id = ?;"
        )
        lineage_rows = self.execute_query(lineage_sql, (artifact_id,))
        parent_ids = tuple(lr["parent_artifact_id"] for lr in lineage_rows)
        return ArtifactRecord(
            artifact_id=r["artifact_id"],
            sha256_hash=r["sha256_hash"],
            media_type=r["media_type"],
            size_bytes=int(r["size_bytes"]),
            created_at_utc=datetime.fromisoformat(r["created_at_utc"]),
            metadata=meta,
            parent_ids=parent_ids,
        )

    def get_artifact_parents(self, artifact_id: str) -> list[str]:
        """Fetch parent artifact IDs for a given child artifact."""
        sql = (
            "SELECT parent_artifact_id FROM persistence_artifact_lineage "
            "WHERE child_artifact_id = ?;"
        )
        rows = self.execute_query(sql, (artifact_id,))
        return [r["parent_artifact_id"] for r in rows]

    def get_artifact_children(self, artifact_id: str) -> list[str]:
        """Fetch child artifact IDs for a given parent artifact."""
        sql = (
            "SELECT child_artifact_id FROM persistence_artifact_lineage "
            "WHERE parent_artifact_id = ?;"
        )
        rows = self.execute_query(sql, (artifact_id,))
        return [r["child_artifact_id"] for r in rows]

    def delete_artifact_record(self, artifact_id: str) -> None:
        """Delete an artifact and its lineage within a transaction."""
        with self.transaction() as con:
            cur = con.cursor()
            cur.execute(
                "DELETE FROM persistence_artifact_lineage "
                "WHERE child_artifact_id = ? OR parent_artifact_id = ?;",
                (artifact_id, artifact_id),
            )
            cur.execute(
                "DELETE FROM persistence_artifacts WHERE artifact_id = ?;",
                (artifact_id,),
            )

    # -----------------------------------------------------------------------
    # Databanks CRUD
    # -----------------------------------------------------------------------

    def upsert_databank(
        self,
        project_name: str,
        databank_name: str,
        *,
        capacity: int,
        default_view: str,
        auto_sync_policy: AutoSyncPolicy,
        created_at_utc: datetime,
    ) -> DatabankRecord:
        """Create or update a project databank record."""
        sql = (
            "INSERT INTO persistence_databanks "
            "(project_name, databank_name, capacity, default_view, "
            "auto_sync_policy, created_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (project_name, databank_name) DO UPDATE SET "
            "capacity = excluded.capacity, "
            "default_view = excluded.default_view, "
            "auto_sync_policy = excluded.auto_sync_policy;"
        )
        self.execute_mutation(
            sql,
            (
                project_name,
                databank_name,
                capacity,
                default_view,
                auto_sync_policy.value,
                created_at_utc.isoformat(),
            ),
        )
        return DatabankRecord(
            project_name=project_name,
            databank_name=databank_name,
            capacity=capacity,
            default_view=default_view,
            auto_sync_policy=auto_sync_policy,
            member_count=self.count_databank_members(project_name, databank_name),
            created_at_utc=created_at_utc,
        )

    def get_databank(
        self, project_name: str, databank_name: str
    ) -> DatabankRecord | None:
        """Fetch databank configuration by project and databank name."""
        sql = (
            "SELECT project_name, databank_name, capacity, default_view, "
            "auto_sync_policy, created_at_utc FROM persistence_databanks "
            "WHERE project_name = ? AND databank_name = ?;"
        )
        rows = self.execute_query(sql, (project_name, databank_name))
        if not rows:
            return None
        r = rows[0]
        count = self.count_databank_members(project_name, databank_name)
        return DatabankRecord(
            project_name=r["project_name"],
            databank_name=r["databank_name"],
            capacity=int(r["capacity"]),
            default_view=r["default_view"],
            auto_sync_policy=AutoSyncPolicy(r["auto_sync_policy"]),
            member_count=count,
            created_at_utc=datetime.fromisoformat(r["created_at_utc"]),
        )

    def list_databanks(self, project_name: str) -> list[DatabankRecord]:
        """List all databanks for a project."""
        sql = (
            "SELECT project_name, databank_name, capacity, default_view, "
            "auto_sync_policy, created_at_utc FROM persistence_databanks "
            "WHERE project_name = ? ORDER BY databank_name ASC;"
        )
        rows = self.execute_query(sql, (project_name,))
        records: list[DatabankRecord] = []
        for r in rows:
            count = self.count_databank_members(project_name, r["databank_name"])
            records.append(
                DatabankRecord(
                    project_name=r["project_name"],
                    databank_name=r["databank_name"],
                    capacity=int(r["capacity"]),
                    default_view=r["default_view"],
                    auto_sync_policy=AutoSyncPolicy(r["auto_sync_policy"]),
                    member_count=count,
                    created_at_utc=datetime.fromisoformat(r["created_at_utc"]),
                )
            )
        return records

    def delete_databank(self, project_name: str, databank_name: str) -> bool:
        """Delete databank and all associated members."""
        with self.transaction() as con:
            cur = con.cursor()
            cur.execute(
                "DELETE FROM persistence_databank_members "
                "WHERE project_name = ? AND databank_name = ?;",
                (project_name, databank_name),
            )
            cur.execute(
                "DELETE FROM persistence_databanks "
                "WHERE project_name = ? AND databank_name = ?;",
                (project_name, databank_name),
            )
            return cur.rowcount > 0

    def clear_databank_members(self, project_name: str, databank_name: str) -> int:
        """Remove all members from a databank."""
        sql = (
            "DELETE FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ?;"
        )
        return self.execute_mutation(sql, (project_name, databank_name))

    def count_databank_members(self, project_name: str, databank_name: str) -> int:
        """Count total members currently in a databank."""
        rows = self.execute_query(
            "SELECT COUNT(*) as count FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ?;",
            (project_name, databank_name),
        )
        return int(rows[0]["count"]) if rows else 0

    def insert_member(
        self,
        project_name: str,
        databank_name: str,
        artifact_id: str,
        *,
        fitness: float,
        ranking_value: float,
        metrics: Mapping[str, float],
        annotations: Mapping[str, Any],
        added_at_utc: datetime,
    ) -> DatabankMemberRecord:
        """Insert a strategy member into a databank."""
        sql = (
            "INSERT INTO persistence_databank_members "
            "(project_name, databank_name, artifact_id, fitness, "
            "ranking_value, metrics_json, annotations_json, added_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
        )
        self.execute_mutation(
            sql,
            (
                project_name,
                databank_name,
                artifact_id,
                fitness,
                ranking_value,
                json.dumps(dict(metrics)),
                json.dumps(dict(annotations)),
                added_at_utc.isoformat(),
            ),
        )
        return DatabankMemberRecord(
            project_name=project_name,
            databank_name=databank_name,
            artifact_id=artifact_id,
            fitness=fitness,
            ranking_value=ranking_value,
            metrics=metrics,
            annotations=annotations,
            added_at_utc=added_at_utc,
        )

    def remove_member(
        self, project_name: str, databank_name: str, artifact_id: str
    ) -> bool:
        """Remove a member from a databank."""
        rows = self.execute_mutation(
            "DELETE FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ? AND artifact_id = ?;",
            (project_name, databank_name, artifact_id),
        )
        return rows > 0

    def move_member_between_databanks(
        self,
        source_project: str,
        source_databank: str,
        target_project: str,
        target_databank: str,
        artifact_id: str,
    ) -> DatabankMemberRecord:
        """Atomically move a member from source databank to target databank."""
        with self.transaction() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT 1 FROM persistence_databanks "
                "WHERE project_name = ? AND databank_name = ?;",
                (target_project, target_databank),
            )
            if cur.fetchone() is None:
                msg = f"Target databank {target_project}/{target_databank} not found"
                raise DatabankNotFoundError(msg)

            cur.execute(
                "SELECT fitness, ranking_value, metrics_json, annotations_json "
                "FROM persistence_databank_members "
                "WHERE project_name = ? AND databank_name = ? AND artifact_id = ?;",
                (source_project, source_databank, artifact_id),
            )
            source_row = cur.fetchone()
            if source_row is None:
                msg = (
                    f"Member {artifact_id} not found in source databank "
                    f"{source_project}/{source_databank}"
                )
                raise DatabankNotFoundError(msg)

            cur.execute(
                "SELECT 1 FROM persistence_databank_members "
                "WHERE project_name = ? AND databank_name = ? AND artifact_id = ?;",
                (target_project, target_databank, artifact_id),
            )
            if cur.fetchone() is not None:
                msg = (
                    f"Member {artifact_id} already exists in target databank "
                    f"{target_project}/{target_databank}"
                )
                raise DuplicateMemberError(msg)

            fitness = float(source_row[0])
            ranking_value = float(source_row[1])
            metrics_json = str(source_row[2])
            annotations_json = str(source_row[3])
            added_at_utc = datetime.now(UTC)

            cur.execute(
                "INSERT INTO persistence_databank_members "
                "(project_name, databank_name, artifact_id, fitness, "
                "ranking_value, metrics_json, annotations_json, added_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    target_project,
                    target_databank,
                    artifact_id,
                    fitness,
                    ranking_value,
                    metrics_json,
                    annotations_json,
                    added_at_utc.isoformat(),
                ),
            )

            cur.execute(
                "DELETE FROM persistence_databank_members "
                "WHERE project_name = ? AND databank_name = ? AND artifact_id = ?;",
                (source_project, source_databank, artifact_id),
            )

            return DatabankMemberRecord(
                project_name=target_project,
                databank_name=target_databank,
                artifact_id=artifact_id,
                fitness=fitness,
                ranking_value=ranking_value,
                metrics=json.loads(metrics_json),
                annotations=json.loads(annotations_json),
                added_at_utc=added_at_utc,
            )

    def get_databank_members(
        self,
        project_name: str,
        databank_name: str,
        limit: int | None = None,
    ) -> list[DatabankMemberRecord]:
        """Fetch databank members ordered by ranking value descending."""
        sql = (
            "SELECT project_name, databank_name, artifact_id, fitness, "
            "ranking_value, metrics_json, annotations_json, added_at_utc "
            "FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ? "
            "ORDER BY ranking_value DESC"
        )
        params: tuple[Any, ...] = (project_name, databank_name)
        if limit is not None and limit > 0:
            sql += " LIMIT ?"
            params = (project_name, databank_name, limit)
        rows = self.execute_query(sql, params)
        return [
            DatabankMemberRecord(
                project_name=r["project_name"],
                databank_name=r["databank_name"],
                artifact_id=r["artifact_id"],
                fitness=float(r["fitness"]),
                ranking_value=float(r["ranking_value"]),
                metrics=json.loads(r["metrics_json"]),
                annotations=json.loads(r["annotations_json"]),
                added_at_utc=datetime.fromisoformat(r["added_at_utc"]),
            )
            for r in rows
        ]

    def get_lowest_ranked_member(
        self, project_name: str, databank_name: str
    ) -> DatabankMemberRecord | None:
        """Fetch the member with the lowest ranking_value in a databank."""
        sql = (
            "SELECT project_name, databank_name, artifact_id, fitness, "
            "ranking_value, metrics_json, annotations_json, added_at_utc "
            "FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ? "
            "ORDER BY ranking_value ASC LIMIT 1;"
        )
        rows = self.execute_query(sql, (project_name, databank_name))
        if not rows:
            return None
        r = rows[0]
        return DatabankMemberRecord(
            project_name=r["project_name"],
            databank_name=r["databank_name"],
            artifact_id=r["artifact_id"],
            fitness=float(r["fitness"]),
            ranking_value=float(r["ranking_value"]),
            metrics=json.loads(r["metrics_json"]),
            annotations=json.loads(r["annotations_json"]),
            added_at_utc=datetime.fromisoformat(r["added_at_utc"]),
        )

    # -----------------------------------------------------------------------
    # Views CRUD
    # -----------------------------------------------------------------------

    def upsert_view(self, view_config: DatabankViewConfig) -> None:
        """Save or update a databank view configuration."""
        cols_dict = [
            {
                "name": c.name,
                "metric_key": c.metric_key,
                "sample_type": c.sample_type.value,
                "format_spec": c.format_spec,
                "is_visible": c.is_visible,
                "sort_priority": c.sort_priority,
                "sort_direction": c.sort_direction.value,
            }
            for c in view_config.columns
        ]
        layout = {
            "view_name": view_config.view_name,
            "scope": view_config.scope,
            "columns": cols_dict,
        }
        sql = (
            "INSERT INTO persistence_databank_views "
            "(view_name, scope, layout_json, updated_at_utc) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT (view_name) DO UPDATE SET "
            "scope = excluded.scope, "
            "layout_json = excluded.layout_json, "
            "updated_at_utc = excluded.updated_at_utc;"
        )
        self.execute_mutation(
            sql,
            (
                view_config.view_name,
                view_config.scope,
                json.dumps(layout),
                view_config.updated_at_utc.isoformat(),
            ),
        )

    def get_view(self, view_name: str) -> DatabankViewConfig | None:
        """Retrieve a databank view configuration by name."""
        rows = self.execute_query(
            "SELECT view_name, scope, layout_json, updated_at_utc "
            "FROM persistence_databank_views WHERE view_name = ?;",
            (view_name,),
        )
        if not rows:
            return None
        r = rows[0]
        layout = json.loads(r["layout_json"])
        columns = tuple(
            ColumnConfig(
                name=c["name"],
                metric_key=c["metric_key"],
                sample_type=SampleType(c.get("sample_type", "full_sample")),
                format_spec=c.get("format_spec", "{:.2f}"),
                is_visible=bool(c.get("is_visible", True)),
                sort_priority=c.get("sort_priority"),
                sort_direction=RankingDirection(c.get("sort_direction", "descending")),
            )
            for c in layout.get("columns", [])
        )
        return DatabankViewConfig(
            view_name=r["view_name"],
            scope=r["scope"],
            columns=columns,
            updated_at_utc=datetime.fromisoformat(r["updated_at_utc"]),
        )

    def list_views(self) -> list[DatabankViewConfig]:
        """List all saved databank views."""
        rows = self.execute_query(
            "SELECT view_name FROM persistence_databank_views ORDER BY view_name ASC;"
        )
        views: list[DatabankViewConfig] = []
        for r in rows:
            v = self.get_view(r["view_name"])
            if v is not None:
                views.append(v)
        return views

    # -----------------------------------------------------------------------
    # Retention Audit CRUD
    # -----------------------------------------------------------------------

    def record_purge_audit(
        self,
        operation_id: str,
        artifact_id: str,
        reason: str,
        purged_at_utc: datetime,
    ) -> None:
        """Record an audited purge entry for an artifact."""
        sql = (
            "INSERT INTO persistence_retention_audit "
            "(operation_id, artifact_id, reason, purged_at_utc) "
            "VALUES (?, ?, ?, ?);"
        )
        self.execute_mutation(
            sql, (operation_id, artifact_id, reason, purged_at_utc.isoformat())
        )

    def get_purge_audit(
        self, operation_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch audit records for retention purges."""
        if operation_id:
            sql = (
                "SELECT operation_id, artifact_id, reason, purged_at_utc "
                "FROM persistence_retention_audit WHERE operation_id = ? "
                "ORDER BY purged_at_utc DESC LIMIT ?;"
            )
            return self.execute_query(sql, (operation_id, limit))
        sql = (
            "SELECT operation_id, artifact_id, reason, purged_at_utc "
            "FROM persistence_retention_audit "
            "ORDER BY purged_at_utc DESC LIMIT ?;"
        )
        return self.execute_query(sql, (limit,))
