"""Behavior tests for FEAT-DATA-ALIGN_SERIES."""

from typing import Any

import pytest

from app.contracts.data.internal import StoredSeriesSnapshot
from app.contracts.data.models import AlignmentPolicy, AlignSeriesRequest, Tick
from app.kernel.identity import generate_uuid7
from app.services.data.align_series.align_series import AlignSeriesService


class _Store:
    def __init__(self) -> None:
        self.source_id = generate_uuid7()
        self.copied: tuple[Tick, ...] = ()
        self.tick = Tick(
            timestamp="2026-01-01T00:00:00.000000Z",
            bid="1.1",
            ask="1.2",
            source_sequence=0,
            flags=0,
        )

    async def get_snapshot(self, version_id: str) -> StoredSeriesSnapshot | None:
        if version_id != self.source_id:
            return None
        return StoredSeriesSnapshot(
            version_id=self.source_id,
            kind="TICKS",
            content_hash="0" * 64,
            row_count=1,
        )

    async def read_ticks(self, version_id: str) -> tuple[Tick, ...] | None:
        return (self.tick,) if version_id == self.source_id else None

    async def put_ticks(
        self,
        version_id: str,
        ticks: tuple[Tick, ...],
        **_: Any,
    ) -> object:
        self.copied = ticks
        return {"version_id": version_id}

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"unexpected store call: {name}")


def _request(store: _Store, direction: str) -> AlignSeriesRequest:
    return AlignSeriesRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="ALIGN",
        source_version_id=store.source_id,
        policy=AlignmentPolicy(
            direction=direction,  # type: ignore[arg-type]
            max_age_seconds=60,
            missing_policy="FAIL",
            timezone="UTC",
        ),
    )


@pytest.mark.asyncio
async def test_exact_alignment_copies_source_without_timestamp_change() -> None:
    store = _Store()
    service = AlignSeriesService(store)  # type: ignore[arg-type]

    result = await service.align_series(_request(store, "EXACT"))

    assert result.outcome == "SUCCESS"
    assert result.aligned is not None
    assert store.copied == (store.tick,)


@pytest.mark.asyncio
async def test_last_known_fails_without_target_timeline() -> None:
    store = _Store()
    service = AlignSeriesService(store)  # type: ignore[arg-type]

    result = await service.align_series(_request(store, "LAST_KNOWN"))

    assert result.outcome == "FAILURE"
    assert result.code == "DATA_ALIGNMENT_INCOMPATIBLE"
