"""Observation ingestion pipeline for control-plane monitoring.

Classes and functions:
    ObservationRecord: Class. Provides ObservationRecord behavior for execution workflows.
    ObservationIngestionService: Class. Provides ObservationIngestionService behavior for execution workflows.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.agentic.contracts.observation_event.model import ObservationEvent
from app.agentic.contracts.serialization import canonical_json_dumps


@dataclass(frozen=True)
class ObservationRecord:
    """Represent ObservationRecord behavior in execution service workflows."""

    observation_id: str
    workflow_id: str
    observation_type: str
    severity: str
    source: str
    payload_ref: str | None
    payload_json: str | None
    authority_state: str
    freshness_status: str
    occurred_at: str


class ObservationIngestionService:
    """Persist canonical observation events into the core observation table."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def ingest(self, observation: ObservationEvent) -> ObservationRecord:
        """Perform the ingest execution service operation."""
        payload = observation.payload
        inline_or_ref = payload.payload_ref_or_inline
        payload_ref = inline_or_ref.get("ref")
        payload_json = (
            None if payload_ref is not None else canonical_json_dumps(inline_or_ref)
        )
        authority_state = canonical_json_dumps(payload.authority_state)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO core_observations (
                    observation_id,
                    workflow_id,
                    observation_type,
                    severity,
                    source,
                    payload_ref,
                    payload_json,
                    authority_state,
                    freshness_status,
                    occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.observation_id,
                    observation.workflow_id,
                    payload.observation_type,
                    payload.severity,
                    payload.source,
                    payload_ref,
                    payload_json,
                    authority_state,
                    payload.freshness_status,
                    payload.observed_at.isoformat().replace("+00:00", "Z"),
                ),
            )
            row = connection.execute(
                "SELECT * FROM core_observations WHERE observation_id = ?",
                (payload.observation_id,),
            ).fetchone()

        if row is None:
            raise LookupError(
                f"observation not found after create: {payload.observation_id}"
            )
        return ObservationRecord(**dict(row))
