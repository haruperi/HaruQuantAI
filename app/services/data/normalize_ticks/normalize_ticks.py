"""Deterministic tick normalization for ``FEAT-DATA-NORMALIZE_TICKS``.

The feature preserves every genuine tick field, orders observations by their public
``(timestamp, source_sequence)`` key, records when incoming order needed repair, and
publishes the normalized immutable batch through the declared Data series-store port.
It does not infer missing prices, volume, provider identity, or future observations.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import TYPE_CHECKING

from app.contracts.common.models import ValidationIssue
from app.contracts.data.models import (
    NormalizeTicksRequest,
    NormalizeTicksSuccess,
    Tick,
)
from app.kernel.identity import generate_uuid7

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability


def normalize_tick_batch(
    ticks: tuple[Tick, ...],
) -> tuple[tuple[Tick, ...], tuple[ValidationIssue, ...], str]:
    """Normalize one validated tick batch without performing persistence.

    Args:
        ticks: Validated raw tick records.

    Returns:
        Ordered ticks, explicit normalization findings, and canonical SHA-256 hash.
    """
    ordered = tuple(sorted(ticks, key=lambda tick: (tick.timestamp, tick.source_sequence)))
    findings: list[ValidationIssue] = []
    if ordered != ticks:
        findings.append(
            ValidationIssue(
                path=("ticks",),
                code="TICK_ORDER_NORMALIZED",
                message="Input ticks were reordered by timestamp and source sequence.",
                context={"record_count": len(ticks)},
            )
        )
    seen: set[tuple[str, int]] = set()
    duplicate_keys = 0
    for tick in ordered:
        key = (tick.timestamp, tick.source_sequence)
        if key in seen:
            duplicate_keys += 1
        seen.add(key)
    if duplicate_keys:
        findings.append(
            ValidationIssue(
                path=("ticks",),
                code="DUPLICATE_TICK_KEY",
                message="Duplicate timestamp/source-sequence keys remain explicit.",
                context={"duplicate_count": duplicate_keys},
            )
        )
    encoded = json.dumps(
        [tick.model_dump(mode="json") for tick in ordered],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return ordered, tuple(findings), hashlib.sha256(encoded).hexdigest()


class NormalizeTicksService:
    """Capability implementation for deterministic normalized tick publication."""

    def __init__(self, store: DataSeriesStoreCapability) -> None:
        """Initialize with the declared immutable series-store dependency.

        Args:
            store: Data series-store capability resolved by the lifecycle adapter.
        """
        self._store = store

    async def normalize_ticks(
        self,
        request: NormalizeTicksRequest,
    ) -> NormalizeTicksSuccess:
        """Normalize and persist one immutable tick batch.

        Args:
            request: Validated normalize-ticks request.

        Returns:
            Successful result with immutable version identity and findings.
        """
        ordered, findings, content_hash = normalize_tick_batch(request.ticks)
        version_id = generate_uuid7()
        await self._store.put_ticks(
            version_id,
            ordered,
            content_hash=content_hash,
        )
        return NormalizeTicksSuccess(
            request_id=request.request_id,
            version_id=version_id,
            findings=findings,
        )


async def _demo() -> None:
    """Demonstrate deterministic ordering without external resources."""
    from typing import Any

    class _MemoryStore:
        async def put_ticks(self, version_id: str, ticks: tuple[Tick, ...], **_: Any) -> Any:
            return {"version_id": version_id, "rows": len(ticks)}

    service = NormalizeTicksService(_MemoryStore())  # type: ignore[arg-type]
    request = NormalizeTicksRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="NORMALIZE",
        ticks=(
            Tick(
                timestamp="2026-01-01T00:00:01.000000Z",
                bid="1.1",
                ask="1.2",
                source_sequence=1,
                flags=0,
            ),
            Tick(
                timestamp="2026-01-01T00:00:00.000000Z",
                bid="1.0",
                ask="1.1",
                source_sequence=0,
                flags=0,
            ),
        ),
    )
    print((await service.normalize_ticks(request)).model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
