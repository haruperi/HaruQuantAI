"""Immutable Data series storage and run-binding pin management.

This module is the primary domain-logic module for ``FEAT-DATA-MANAGE_SERIES``.
It deliberately owns only Data-series payload persistence. Other Data features use
its declared capability rather than importing this implementation or reading its
SQLite tables directly.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from app.contracts.common.models import ContentHash, JsonObject, Timeframe, Uuid7
from app.contracts.data.internal import StoredSeriesKind, StoredSeriesSnapshot
from app.contracts.data.models import Bar, Tick
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.data.manage_series.config import ManageSeriesConfig

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_series_versions (
    version_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    timeframe_json TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS data_series_pins (
    binding_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    PRIMARY KEY (binding_id, version_id),
    FOREIGN KEY (version_id) REFERENCES data_series_versions(version_id)
);
"""


class SeriesStoreService:
    """SQLite-backed immutable series-store capability implementation."""

    def __init__(self, config: ManageSeriesConfig) -> None:
        """Initialize a lazy series store.

        Args:
            config: Trusted feature configuration.
        """
        self._database_path = config.database_path

    def _connect(self) -> sqlite3.Connection:
        """Open one bounded SQLite connection and ensure the feature schema.

        Returns:
            Configured SQLite connection.
        """
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA)
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(data_series_versions)")
        }
        if "timeframe_json" not in columns:
            connection.execute(
                "ALTER TABLE data_series_versions ADD COLUMN timeframe_json TEXT"
            )
        return connection

    @staticmethod
    def _serialize_models(values: Iterable[Bar | Tick]) -> str:
        """Serialize public wire models deterministically for storage.

        Args:
            values: Bar or tick records.

        Returns:
            Compact JSON array text.
        """
        payload = [value.model_dump(mode="json") for value in values]
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    async def _put(
        self,
        version_id: Uuid7,
        *,
        kind: StoredSeriesKind,
        content_hash: ContentHash,
        row_count: int,
        timeframe: Timeframe | None,
        payload_json: str,
    ) -> StoredSeriesSnapshot:
        """Persist one immutable payload or verify an identical replay.

        Args:
            version_id: Immutable version identity.
            kind: Stored payload kind.
            content_hash: Canonical payload digest.
            row_count: Number of logical records.
            timeframe: Bar cadence when the payload is bar-shaped.
            payload_json: Canonical JSON payload.

        Returns:
            Stored series metadata.

        Raises:
            ValueError: If the same version identity is reused for different content.
        """
        timeframe_json = (
            json.dumps(
                timeframe.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            if timeframe is not None
            else None
        )

        def write() -> StoredSeriesSnapshot:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT kind, content_hash, row_count, timeframe_json, payload_json "
                    "FROM data_series_versions WHERE version_id = ?",
                    (version_id,),
                ).fetchone()
                expected = (
                    kind,
                    content_hash,
                    row_count,
                    timeframe_json,
                    payload_json,
                )
                if existing is not None:
                    if existing != expected:
                        raise ValueError("immutable series version conflict")
                else:
                    connection.execute(
                        "INSERT INTO data_series_versions "
                        "(version_id, kind, content_hash, row_count, timeframe_json, "
                        "payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            version_id,
                            kind,
                            content_hash,
                            row_count,
                            timeframe_json,
                            payload_json,
                            format_utc_timestamp(utc_now()),
                        ),
                    )
                pinned = connection.execute(
                    "SELECT 1 FROM data_series_pins WHERE version_id = ? LIMIT 1",
                    (version_id,),
                ).fetchone() is not None
            return StoredSeriesSnapshot(
                version_id=version_id,
                kind=kind,
                content_hash=content_hash,
                row_count=row_count,
                timeframe=timeframe,
                pinned=pinned,
            )

        return await asyncio.to_thread(write)

    async def put_ticks(
        self,
        version_id: Uuid7,
        ticks: tuple[Tick, ...],
        *,
        content_hash: ContentHash,
    ) -> StoredSeriesSnapshot:
        """Persist one immutable normalized tick version.

        Args:
            version_id: Immutable version identity.
            ticks: Normalized tick payload.
            content_hash: Canonical payload digest.

        Returns:
            Stored series metadata.
        """
        return await self._put(
            version_id,
            kind="TICKS",
            content_hash=content_hash,
            row_count=len(ticks),
            timeframe=None,
            payload_json=self._serialize_models(ticks),
        )

    async def put_bars(
        self,
        version_id: Uuid7,
        bars: tuple[Bar, ...],
        *,
        content_hash: ContentHash,
        timeframe: Timeframe,
        kind: StoredSeriesKind = "BARS",
    ) -> StoredSeriesSnapshot:
        """Persist one immutable bar or scenario version.

        Args:
            version_id: Immutable version identity.
            bars: Bar payload.
            content_hash: Canonical payload digest.
            timeframe: Exact source cadence for closed-bar reasoning.
            kind: ``BARS`` or ``SCENARIO``.

        Returns:
            Stored series metadata.

        Raises:
            ValueError: If kind is incompatible with bars.
        """
        if kind not in {"BARS", "SCENARIO"}:
            raise ValueError("bar payload kind must be BARS or SCENARIO")
        return await self._put(
            version_id,
            kind=kind,
            content_hash=content_hash,
            row_count=len(bars),
            timeframe=timeframe,
            payload_json=self._serialize_models(bars),
        )

    async def put_opaque(
        self,
        version_id: Uuid7,
        payload: JsonObject,
        *,
        content_hash: ContentHash,
        kind: StoredSeriesKind = "OPAQUE",
    ) -> StoredSeriesSnapshot:
        """Persist immutable JSON evidence.

        Args:
            version_id: Immutable version identity.
            payload: JSON-safe evidence.
            content_hash: Canonical payload digest.
            kind: ``INDICATOR`` or ``OPAQUE``.

        Returns:
            Stored series metadata.

        Raises:
            ValueError: If the selected kind requires bar/tick storage.
        """
        if kind not in {"INDICATOR", "OPAQUE"}:
            raise ValueError("opaque payload kind must be INDICATOR or OPAQUE")
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return await self._put(
            version_id,
            kind=kind,
            content_hash=content_hash,
            row_count=1,
            timeframe=None,
            payload_json=payload_json,
        )

    async def _read_row(self, version_id: Uuid7) -> tuple[str, str] | None:
        """Read stored kind and payload JSON.

        Args:
            version_id: Immutable version identity.

        Returns:
            ``(kind, payload_json)`` or None.
        """

        def read() -> tuple[str, str] | None:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT kind, payload_json FROM data_series_versions "
                    "WHERE version_id = ?",
                    (version_id,),
                ).fetchone()
            return cast(tuple[str, str] | None, row)

        return await asyncio.to_thread(read)

    async def read_ticks(self, version_id: Uuid7) -> tuple[Tick, ...] | None:
        """Read one tick payload.

        Args:
            version_id: Immutable version identity.

        Returns:
            Parsed ticks, or None when missing/not tick-shaped.
        """
        row = await self._read_row(version_id)
        if row is None or row[0] != "TICKS":
            return None
        raw = cast(list[dict[str, Any]], json.loads(row[1]))
        return tuple(Tick.model_validate(item) for item in raw)

    async def read_bars(self, version_id: Uuid7) -> tuple[Bar, ...] | None:
        """Read one bar/scenario payload.

        Args:
            version_id: Immutable version identity.

        Returns:
            Parsed bars, or None when missing/not bar-shaped.
        """
        row = await self._read_row(version_id)
        if row is None or row[0] not in {"BARS", "SCENARIO"}:
            return None
        raw = cast(list[dict[str, Any]], json.loads(row[1]))
        return tuple(Bar.model_validate(item) for item in raw)

    async def read_opaque(self, version_id: Uuid7) -> JsonObject | None:
        """Read one opaque/indicator payload.

        Args:
            version_id: Immutable version identity.

        Returns:
            Parsed JSON evidence, or None when unavailable.
        """
        row = await self._read_row(version_id)
        if row is None or row[0] not in {"INDICATOR", "OPAQUE"}:
            return None
        return cast(JsonObject, json.loads(row[1]))

    async def get_snapshot(self, version_id: Uuid7) -> StoredSeriesSnapshot | None:
        """Read metadata for one stored version.

        Args:
            version_id: Immutable version identity.

        Returns:
            Stored metadata, or None.
        """

        def read() -> StoredSeriesSnapshot | None:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT kind, content_hash, row_count, timeframe_json "
                    "FROM data_series_versions WHERE version_id = ?",
                    (version_id,),
                ).fetchone()
                if row is None:
                    return None
                pinned = connection.execute(
                    "SELECT 1 FROM data_series_pins WHERE version_id = ? LIMIT 1",
                    (version_id,),
                ).fetchone() is not None
            timeframe = (
                Timeframe.model_validate(json.loads(row[3]))
                if row[3] is not None
                else None
            )
            return StoredSeriesSnapshot(
                version_id=version_id,
                kind=cast(StoredSeriesKind, row[0]),
                content_hash=cast(ContentHash, row[1]),
                row_count=int(row[2]),
                timeframe=timeframe,
                pinned=pinned,
            )

        return await asyncio.to_thread(read)

    async def pin_versions(
        self,
        binding_id: Uuid7,
        version_ids: tuple[Uuid7, ...],
    ) -> None:
        """Pin exact versions referenced by an immutable run binding.

        Args:
            binding_id: Run-data binding identity.
            version_ids: Version identities to retain.

        Raises:
            ValueError: If any referenced version does not exist.
        """

        def pin() -> None:
            with self._connect() as connection:
                for version_id in version_ids:
                    exists = connection.execute(
                        "SELECT 1 FROM data_series_versions WHERE version_id = ?",
                        (version_id,),
                    ).fetchone()
                    if exists is None:
                        raise ValueError(f"unknown series version: {version_id}")
                connection.executemany(
                    "INSERT OR IGNORE INTO data_series_pins (binding_id, version_id) "
                    "VALUES (?, ?)",
                    ((binding_id, version_id) for version_id in version_ids),
                )

        await asyncio.to_thread(pin)

    async def collect_unpinned(self, *, limit: int) -> tuple[Uuid7, ...]:
        """Delete a bounded oldest set of unpinned versions.

        Args:
            limit: Positive maximum versions to collect.

        Returns:
            Deleted version identities.

        Raises:
            ValueError: If limit is not positive.
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        def collect() -> tuple[Uuid7, ...]:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT v.version_id FROM data_series_versions AS v "
                    "WHERE NOT EXISTS (SELECT 1 FROM data_series_pins AS p "
                    "WHERE p.version_id = v.version_id) "
                    "ORDER BY v.created_at, v.version_id LIMIT ?",
                    (limit,),
                ).fetchall()
                version_ids = tuple(cast(Uuid7, row[0]) for row in rows)
                connection.executemany(
                    "DELETE FROM data_series_versions WHERE version_id = ?",
                    ((version_id,) for version_id in version_ids),
                )
            return version_ids

        return await asyncio.to_thread(collect)


async def _demo() -> None:
    """Run a bounded standalone immutable-store usage demonstration."""
    import hashlib
    import tempfile

    from app.kernel.identity import generate_uuid7

    with tempfile.TemporaryDirectory() as temporary_directory:
        service = SeriesStoreService(
            ManageSeriesConfig(
                database_path=Path(temporary_directory) / "data.sqlite3"
            )
        )
        tick = Tick(
            timestamp="2026-01-01T00:00:00.000000Z",
            bid="1.1",
            ask="1.2",
            source_sequence=0,
            flags=0,
        )
        digest = hashlib.sha256(
            json.dumps(tick.model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest()
        version_id = generate_uuid7()
        stored = await service.put_ticks(version_id, (tick,), content_hash=digest)
        print(stored.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
