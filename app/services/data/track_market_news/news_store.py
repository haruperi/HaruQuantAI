"""Feature-owned persistence for market-news observations and revisions."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from app.contracts.data.models import MarketNewsObservation, MarketNewsRevision

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_market_news_observations (
    observation_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    provider_item_id TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    event_at TEXT NOT NULL,
    category TEXT NOT NULL,
    impact TEXT NOT NULL,
    language TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE (source_id, provider_item_id, first_seen_at)
);
CREATE INDEX IF NOT EXISTS idx_data_market_news_event_at
    ON data_market_news_observations(event_at);
CREATE TABLE IF NOT EXISTS data_market_news_revisions (
    revision_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    visible_from TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE (observation_id, revision),
    FOREIGN KEY (observation_id) REFERENCES data_market_news_observations(observation_id)
);
"""


class MarketNewsStore:
    """SQLite adapter owned exclusively by FEAT-DATA-TRACK_MARKET_NEWS."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA)
        return connection

    async def record_observation(self, observation: MarketNewsObservation) -> None:
        """Persist one immutable observation or verify exact idempotent replay."""
        payload = json.dumps(
            observation.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        event_at = (
            observation.scheduled_at
            or observation.published_at
            or observation.first_seen_at
        )

        def write() -> None:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT payload_json FROM data_market_news_observations "
                    "WHERE observation_id = ?",
                    (observation.observation_id,),
                ).fetchone()
                if existing is not None:
                    if existing[0] != payload:
                        raise ValueError("immutable market-news observation conflict")
                    return
                try:
                    connection.execute(
                        "INSERT INTO data_market_news_observations "
                        "(observation_id, source_id, provider_item_id, first_seen_at, "
                        "retrieved_at, event_at, category, impact, language, payload_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            observation.observation_id,
                            observation.source_id,
                            observation.provider_item_id,
                            observation.first_seen_at,
                            observation.retrieved_at,
                            event_at,
                            observation.category,
                            observation.impact,
                            observation.language,
                            payload,
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise ValueError("market-news observation identity conflict") from error

        await asyncio.to_thread(write)

    async def record_revision(self, revision: MarketNewsRevision) -> bool:
        """Persist one immutable visible-from revision.

        Returns:
            False when the referenced observation is unknown.
        """
        payload = json.dumps(
            revision.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )

        def write() -> bool:
            with self._connect() as connection:
                parent = connection.execute(
                    "SELECT 1 FROM data_market_news_observations WHERE observation_id = ?",
                    (revision.observation_id,),
                ).fetchone()
                if parent is None:
                    return False
                existing = connection.execute(
                    "SELECT revision_id, payload_json FROM data_market_news_revisions "
                    "WHERE revision_id = ? OR (observation_id = ? AND revision = ?)",
                    (revision.revision_id, revision.observation_id, revision.revision),
                ).fetchone()
                if existing is not None:
                    if existing != (revision.revision_id, payload):
                        raise ValueError("immutable market-news revision conflict")
                    return True
                connection.execute(
                    "INSERT INTO data_market_news_revisions "
                    "(revision_id, observation_id, revision, visible_from, kind, payload_json) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        revision.revision_id,
                        revision.observation_id,
                        revision.revision,
                        revision.visible_from,
                        revision.kind,
                        payload,
                    ),
                )
            return True

        return await asyncio.to_thread(write)

    async def query(
        self,
        *,
        as_of: str,
        from_at: str,
        to_at: str,
        source_id: str | None,
        category: str | None,
        language: str | None,
        impact: tuple[str, ...],
    ) -> tuple[MarketNewsObservation, ...]:
        """Read only observations visible by ``as_of`` within the event window."""

        def read() -> tuple[MarketNewsObservation, ...]:
            clauses = [
                "first_seen_at <= ?",
                "event_at >= ?",
                "event_at < ?",
            ]
            parameters: list[object] = [as_of, from_at, to_at]
            if source_id is not None:
                clauses.append("source_id = ?")
                parameters.append(source_id)
            if category is not None:
                clauses.append("category = ?")
                parameters.append(category)
            if language is not None:
                clauses.append("language = ?")
                parameters.append(language)
            if impact:
                placeholders = ",".join("?" for _ in impact)
                clauses.append(f"impact IN ({placeholders})")
                parameters.extend(impact)
            sql = (
                "SELECT observation_id, payload_json FROM data_market_news_observations "
                "WHERE " + " AND ".join(clauses) + " ORDER BY event_at, observation_id"
            )
            with self._connect() as connection:
                rows = connection.execute(sql, tuple(parameters)).fetchall()
                result: list[MarketNewsObservation] = []
                for observation_id, payload_json in rows:
                    latest = connection.execute(
                        "SELECT kind FROM data_market_news_revisions "
                        "WHERE observation_id = ? AND visible_from <= ? "
                        "ORDER BY revision DESC LIMIT 1",
                        (observation_id, as_of),
                    ).fetchone()
                    if latest is not None and latest[0] == "CANCELLATION":
                        continue
                    raw = cast(dict[str, Any], json.loads(payload_json))
                    result.append(MarketNewsObservation.model_validate(raw))
            return tuple(result)

        return await asyncio.to_thread(read)
