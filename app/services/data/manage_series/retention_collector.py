"""Physical collection port owned by the immutable Data series feature."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import cast

from app.contracts.common.models import UtcTimestamp, Uuid7
from app.services.data.manage_series.config import ManageSeriesConfig
from app.services.data.manage_series.series_store import _SCHEMA


class SeriesRetentionCollector:
    """Collect only unpinned series rows older than an explicit cutoff."""

    def __init__(self, config: ManageSeriesConfig) -> None:
        """Initialize the collector against the series owner's database.

        Args:
            config: Trusted series-store configuration.
        """
        self._database_path = config.database_path

    async def collect_unpinned_before(
        self,
        *,
        created_before: UtcTimestamp,
        limit: int,
    ) -> tuple[Uuid7, ...]:
        """Delete a bounded oldest set of unpinned versions before a cutoff.

        Args:
            created_before: Inclusive canonical UTC creation-time cutoff.
            limit: Positive maximum number of versions to delete.

        Returns:
            Deleted immutable series-version identifiers.

        Raises:
            ValueError: If limit is not positive.
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        def collect() -> tuple[Uuid7, ...]:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self._database_path) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.executescript(_SCHEMA)
                rows = connection.execute(
                    "SELECT v.version_id FROM data_series_versions AS v "
                    "WHERE v.created_at <= ? AND NOT EXISTS ("
                    "SELECT 1 FROM data_series_pins AS p "
                    "WHERE p.version_id = v.version_id) "
                    "ORDER BY v.created_at, v.version_id LIMIT ?",
                    (created_before, limit),
                ).fetchall()
                version_ids = tuple(cast(Uuid7, row[0]) for row in rows)
                connection.executemany(
                    "DELETE FROM data_series_versions WHERE version_id = ?",
                    ((version_id,) for version_id in version_ids),
                )
            return version_ids

        return await asyncio.to_thread(collect)
