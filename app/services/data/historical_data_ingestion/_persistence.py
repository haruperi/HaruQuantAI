"""SQLite persistence implementation for Historical Data Ingestion."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from app.contracts.common.models import Uuid7
    from app.contracts.data.models import (
        DataImportReceipt,
        DataSeriesVersion,
        RegisteredDataConnection,
    )
    from app.services.data.historical_data_ingestion.config import (
        HistoricalDataIngestionConfig,
    )

DATA_CONNECTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS data_connections (
    connection_id TEXT PRIMARY KEY,
    connection_type TEXT NOT NULL,
    declared_capabilities TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

DATA_IMPORT_RECEIPTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS data_import_receipts (
    receipt_id TEXT PRIMARY KEY,
    series_version_id TEXT NOT NULL,
    input_rows INTEGER NOT NULL,
    accepted_rows INTEGER NOT NULL,
    rejected_rows INTEGER NOT NULL,
    duplicate_rows INTEGER NOT NULL,
    transformed_rows INTEGER NOT NULL,
    published_rows INTEGER NOT NULL,
    findings_json TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

DATA_SERIES_VERSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS data_series_versions (
    series_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    instrument_id TEXT NOT NULL,
    instrument_version_id TEXT NOT NULL,
    timeframe TEXT,
    tick_type TEXT,
    timezone TEXT NOT NULL,
    precision_json TEXT NOT NULL,
    coverage_json TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    source_artifact_id TEXT NOT NULL,
    canonical_artifact_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (series_id, version)
);
"""

STAGED_ARTIFACTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS staged_artifacts (
    artifact_id TEXT PRIMARY KEY,
    raw_data BLOB NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class HistoricalDataPersistence:
    """Manages SQLite storage for historical data connections and artifacts."""

    def __init__(self, config: HistoricalDataIngestionConfig) -> None:
        self._config = config
        self._mem_uri: str | None = None
        self._mem_conn: sqlite3.Connection | None = None
        self._staged_sources: dict[str, bytes] = {}
        if self._config.database_path is None:
            self._mem_uri = f"file:mem_hist_{id(self)}?mode=memory&cache=shared"
            self._mem_conn = sqlite3.connect(self._mem_uri, uri=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection."""
        if self._config.database_path is not None:
            conn = sqlite3.connect(str(self._config.database_path))
        else:
            conn = sqlite3.connect(self._mem_uri or ":memory:", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        """Initialize schema if auto_migrate is enabled."""
        if not self._config.auto_migrate:
            return
        with self.get_connection() as conn:
            conn.execute(DATA_CONNECTIONS_TABLE_SQL)
            conn.execute(DATA_IMPORT_RECEIPTS_TABLE_SQL)
            conn.execute(DATA_SERIES_VERSIONS_TABLE_SQL)
            conn.execute(STAGED_ARTIFACTS_TABLE_SQL)

    def stage_source_data(self, artifact_id: Uuid7, data: bytes | str) -> None:
        """Stage raw artifact data for import."""
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else data
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        self._staged_sources[artifact_id] = raw_bytes
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO staged_artifacts (
                    artifact_id, raw_data, content_hash, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    raw_bytes,
                    content_hash,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def get_staged_source(self, artifact_id: str) -> bytes | None:
        """Return raw bytes for a staged source artifact."""
        if artifact_id in self._staged_sources:
            return self._staged_sources[artifact_id]
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT raw_data FROM staged_artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
            if row:
                return cast("bytes", row["raw_data"])
        return None

    def save_connection(self, conn_model: RegisteredDataConnection) -> None:
        """Persist a registered data connection."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_connections (
                    connection_id, connection_type, declared_capabilities,
                    raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conn_model.connection_id,
                    conn_model.connection_type,
                    ",".join(conn_model.declared_capabilities),
                    conn_model.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def save_receipt_and_version(
        self, receipt: DataImportReceipt, version: DataSeriesVersion
    ) -> None:
        """Atomically persist receipt and series version records."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_import_receipts (
                    receipt_id, series_version_id, input_rows, accepted_rows,
                    rejected_rows, duplicate_rows, transformed_rows,
                    published_rows, findings_json, raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.series_version_id,
                    receipt.input_rows,
                    receipt.accepted_rows,
                    receipt.rejected_rows,
                    receipt.duplicate_rows,
                    receipt.transformed_rows,
                    receipt.published_rows,
                    "[]",
                    receipt.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO data_series_versions (
                    series_id, version, instrument_id, instrument_version_id,
                    timeframe, tick_type, timezone, precision_json,
                    coverage_json, row_count, source_artifact_id,
                    canonical_artifact_id, content_hash, raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.series_id,
                    version.version,
                    version.instrument_id,
                    version.instrument_version_id,
                    version.timeframe,
                    version.tick_type,
                    version.timezone,
                    version.precision.model_dump_json(),
                    version.coverage.model_dump_json(),
                    version.row_count,
                    version.source_artifact_id,
                    version.canonical_artifact_id,
                    version.content_hash,
                    version.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def fetch_series_version_and_artifact(
        self, series_version_id: str
    ) -> tuple[str, bytes] | None:
        """Fetch raw_json and canonical artifact data for a series version."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT raw_json, canonical_artifact_id "
                "FROM data_series_versions "
                "WHERE series_id = ? OR canonical_artifact_id = ?",
                (series_version_id, series_version_id),
            ).fetchone()
            if not row:
                return None
            artifact_row = conn.execute(
                "SELECT raw_data FROM staged_artifacts WHERE artifact_id = ?",
                (row["canonical_artifact_id"],),
            ).fetchone()
            data = cast("bytes", artifact_row["raw_data"]) if artifact_row else b"[]"
            return str(row["raw_json"]), data

    def close(self) -> None:
        """Close any open in-memory connection handles."""
        if self._mem_conn is not None:
            self._mem_conn.close()
            self._mem_conn = None
