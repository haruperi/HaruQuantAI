"""SQLite persistence implementation for QuantDataManager Source."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.data.quantdata_manager_source.config import (
        QuantDataManagerConfig,
    )

QUANTDATA_LINEAGE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS quantdata_lineage (
    lineage_id TEXT PRIMARY KEY,
    spec_id TEXT NOT NULL,
    source_root TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_mtime TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    decoder_version TEXT NOT NULL,
    series_id TEXT NOT NULL,
    series_version_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

QUANTDATA_SPECS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS quantdata_specs (
    spec_id TEXT PRIMARY KEY,
    allowed_root TEXT NOT NULL,
    decoder_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class QuantDataPersistence:
    """SQLite lineage and spec persistence for QuantDataManager sources."""

    def __init__(self, config: QuantDataManagerConfig) -> None:
        self._config = config
        self._mem_uri: str | None = None
        self._mem_conn: sqlite3.Connection | None = None
        if self._config.database_path is None:
            self._mem_uri = f"file:mem_quant_{id(self)}?mode=memory&cache=shared"
            self._mem_conn = sqlite3.connect(self._mem_uri, uri=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite database connection."""
        if self._config.database_path is not None:
            conn = sqlite3.connect(str(self._config.database_path))
        else:
            conn = sqlite3.connect(self._mem_uri or ":memory:", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize SQLite tables for lineage and imported manifests."""
        with self.get_connection() as conn:
            conn.execute(QUANTDATA_LINEAGE_TABLE_SQL)
            conn.execute(QUANTDATA_SPECS_TABLE_SQL)
            conn.commit()

    def record_lineage(
        self,
        lineage_id: str,
        spec_id: str,
        source_root: str,
        relative_path: str,
        file_size: int,
        file_mtime: str,
        content_hash: str,
        decoder_version: str,
        series_id: str,
        series_version_id: str,
    ) -> None:
        """Record an artifact import lineage entry."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quantdata_lineage (
                    lineage_id, spec_id, source_root, relative_path, file_size,
                    file_mtime, content_hash, decoder_version, series_id,
                    series_version_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lineage_id,
                    spec_id,
                    source_root,
                    relative_path,
                    file_size,
                    file_mtime,
                    content_hash,
                    decoder_version,
                    series_id,
                    series_version_id,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    def record_spec(
        self,
        spec_id: str,
        allowed_root: str,
        decoder_version: str,
    ) -> None:
        """Record an import specification registration."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quantdata_specs (
                    spec_id, allowed_root, decoder_version, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    spec_id,
                    allowed_root,
                    decoder_version,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    @staticmethod
    def read_legacy_sqlite(db_path: Path) -> list[dict[str, Any]]:
        """Read rows from a legacy QuantDataManager SQLite export."""
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM DATA LIMIT 5000")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def close(self) -> None:
        """Close any open in-memory connection handles."""
        if self._mem_conn is not None:
            self._mem_conn.close()
            self._mem_conn = None
