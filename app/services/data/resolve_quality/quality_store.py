"""Feature-owned persistence for data quality findings and decisions."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

from app.contracts.data.models import DataQualityDecision, DataQualityFinding

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_quality_findings (
    finding_id TEXT PRIMARY KEY,
    data_version_id TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_data_quality_findings_version
    ON data_quality_findings(data_version_id);
CREATE TABLE IF NOT EXISTS data_quality_decisions (
    decision_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL
);
"""


class QualityStore:
    """SQLite adapter owned exclusively by FEAT-DATA-RESOLVE_QUALITY."""

    def __init__(self, database_path: Path) -> None:
        """Initialize a lazy feature-local store.

        Args:
            database_path: Feature-owned SQLite path.
        """
        self._database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.executescript(_SCHEMA)
        return connection

    async def replace_findings(
        self,
        data_version_id: str,
        findings: tuple[DataQualityFinding, ...],
    ) -> None:
        """Replace deterministic findings for one immutable version.

        Args:
            data_version_id: Immutable source version identity.
            findings: Current deterministic finding set.
        """

        def write() -> None:
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM data_quality_findings WHERE data_version_id = ?",
                    (data_version_id,),
                )
                connection.executemany(
                    "INSERT INTO data_quality_findings "
                    "(finding_id, data_version_id, payload_json) VALUES (?, ?, ?)",
                    (
                        (
                            finding.finding_id,
                            data_version_id,
                            json.dumps(
                                finding.model_dump(mode="json"),
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        )
                        for finding in findings
                    ),
                )

        await asyncio.to_thread(write)

    async def record_decision(self, decision: DataQualityDecision) -> None:
        """Append one immutable quality decision.

        Args:
            decision: Explicit quality resolution decision.

        Raises:
            ValueError: If the same decision identity is reused for new content.
        """
        payload = json.dumps(
            decision.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )

        def write() -> None:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT payload_json FROM data_quality_decisions WHERE decision_id = ?",
                    (decision.decision_id,),
                ).fetchone()
                if existing is not None and existing[0] != payload:
                    raise ValueError("immutable quality decision conflict")
                if existing is None:
                    connection.execute(
                        "INSERT INTO data_quality_decisions (decision_id, payload_json) "
                        "VALUES (?, ?)",
                        (decision.decision_id, payload),
                    )

        await asyncio.to_thread(write)
