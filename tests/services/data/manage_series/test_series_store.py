"""Behavior tests for FEAT-DATA-MANAGE_SERIES."""

import hashlib
import json
from pathlib import Path

import pytest

from app.contracts.data.models import Tick
from app.kernel.identity import generate_uuid7
from app.services.data.manage_series.config import ManageSeriesConfig
from app.services.data.manage_series.series_store import SeriesStoreService


def _tick(sequence: int = 0) -> Tick:
    return Tick(
        timestamp="2026-01-01T00:00:00.000000Z",
        bid="1.1",
        ask="1.2",
        source_sequence=sequence,
        flags=0,
    )


def _hash(tick: Tick) -> str:
    return hashlib.sha256(
        json.dumps(tick.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()


@pytest.mark.asyncio
async def test_round_trip_and_pin(tmp_path: Path) -> None:
    service = SeriesStoreService(
        ManageSeriesConfig(database_path=tmp_path / "data.sqlite3")
    )
    tick = _tick()
    version_id = generate_uuid7()

    stored = await service.put_ticks(version_id, (tick,), content_hash=_hash(tick))
    assert stored.row_count == 1
    assert await service.read_ticks(version_id) == (tick,)

    binding_id = generate_uuid7()
    await service.pin_versions(binding_id, (version_id,))
    pinned = await service.get_snapshot(version_id)
    assert pinned is not None and pinned.pinned is True
    assert await service.collect_unpinned(limit=10) == ()


@pytest.mark.asyncio
async def test_immutable_identity_conflict_fails(tmp_path: Path) -> None:
    service = SeriesStoreService(
        ManageSeriesConfig(database_path=tmp_path / "data.sqlite3")
    )
    version_id = generate_uuid7()
    first = _tick(0)
    second = _tick(1)

    await service.put_ticks(version_id, (first,), content_hash=_hash(first))
    with pytest.raises(ValueError, match="immutable series version conflict"):
        await service.put_ticks(version_id, (second,), content_hash=_hash(second))


@pytest.mark.asyncio
async def test_collect_removes_unpinned_version(tmp_path: Path) -> None:
    service = SeriesStoreService(
        ManageSeriesConfig(database_path=tmp_path / "data.sqlite3")
    )
    tick = _tick()
    version_id = generate_uuid7()
    await service.put_ticks(version_id, (tick,), content_hash=_hash(tick))

    assert await service.collect_unpinned(limit=1) == (version_id,)
    assert await service.get_snapshot(version_id) is None
