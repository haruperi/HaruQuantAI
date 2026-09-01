"""Behavior tests for FEAT-DATA-NORMALIZE_TICKS."""

from typing import Any

import pytest

from app.contracts.data.models import NormalizeTicksRequest, Tick
from app.kernel.identity import generate_uuid7
from app.services.data.normalize_ticks.normalize_ticks import NormalizeTicksService


class _Store:
    def __init__(self) -> None:
        self.ticks: tuple[Tick, ...] = ()

    async def put_ticks(
        self,
        version_id: str,
        ticks: tuple[Tick, ...],
        **_: Any,
    ) -> object:
        self.ticks = ticks
        return {"version_id": version_id}


def _tick(timestamp: str, sequence: int) -> Tick:
    return Tick(
        timestamp=timestamp,
        bid="1.1",
        ask="1.2",
        source_sequence=sequence,
        flags=0,
    )


@pytest.mark.asyncio
async def test_normalize_ticks_orders_and_records_finding() -> None:
    store = _Store()
    service = NormalizeTicksService(store)  # type: ignore[arg-type]
    request = NormalizeTicksRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="NORMALIZE",
        ticks=(
            _tick("2026-01-01T00:00:01.000000Z", 1),
            _tick("2026-01-01T00:00:00.000000Z", 0),
        ),
    )

    result = await service.normalize_ticks(request)

    assert store.ticks[0].timestamp == "2026-01-01T00:00:00.000000Z"
    assert result.version_id is not None
    assert tuple(item.code for item in result.findings) == ("TICK_ORDER_NORMALIZED",)
