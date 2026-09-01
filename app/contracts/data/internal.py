"""Internal cross-feature contracts for Data-owned immutable series storage.

These contracts are intentionally not UI/API wire surfaces. They exist so focused
Data features collaborate through a declared capability instead of importing a
sibling repository or reading another feature's private tables.
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from app.contracts.common.models import (
    ContentHash,
    JsonObject,
    UtcTimestamp,
    Uuid7,
    WireModel,
)
from app.contracts.data.models import Bar, Tick
from app.kernel.capability import CapabilityKey

type StoredSeriesKind = Literal["BARS", "TICKS", "SCENARIO", "INDICATOR", "OPAQUE"]


class StoredSeriesSnapshot(WireModel):
    """Immutable metadata for one Data-domain stored series payload."""

    version_id: Uuid7
    kind: StoredSeriesKind
    content_hash: ContentHash
    row_count: int
    pinned: bool = False
    schema_version: Literal[1] = 1


@runtime_checkable
class DataSeriesStoreCapability(Protocol):
    """Feature-to-feature storage port for immutable Data series payloads."""

    async def put_ticks(
        self,
        version_id: Uuid7,
        ticks: tuple[Tick, ...],
        *,
        content_hash: ContentHash,
    ) -> StoredSeriesSnapshot:
        """Persist one immutable normalized tick version."""
        ...

    async def put_bars(
        self,
        version_id: Uuid7,
        bars: tuple[Bar, ...],
        *,
        content_hash: ContentHash,
        kind: StoredSeriesKind = "BARS",
    ) -> StoredSeriesSnapshot:
        """Persist one immutable bar/scenario version."""
        ...

    async def put_opaque(
        self,
        version_id: Uuid7,
        payload: JsonObject,
        *,
        content_hash: ContentHash,
        kind: StoredSeriesKind = "OPAQUE",
    ) -> StoredSeriesSnapshot:
        """Persist immutable JSON evidence that has no bar/tick representation."""
        ...

    async def read_ticks(self, version_id: Uuid7) -> tuple[Tick, ...] | None:
        """Read a tick payload when the version is tick-shaped."""
        ...

    async def read_bars(self, version_id: Uuid7) -> tuple[Bar, ...] | None:
        """Read a bar/scenario payload when the version is bar-shaped."""
        ...

    async def read_opaque(self, version_id: Uuid7) -> JsonObject | None:
        """Read an opaque JSON payload when present."""
        ...

    async def get_snapshot(self, version_id: Uuid7) -> StoredSeriesSnapshot | None:
        """Read immutable metadata for one stored version."""
        ...

    async def pin_versions(
        self,
        binding_id: Uuid7,
        version_ids: tuple[Uuid7, ...],
    ) -> None:
        """Pin versions that are referenced by an immutable run binding."""
        ...

    async def collect_unpinned(
        self,
        *,
        limit: int,
        older_than: UtcTimestamp | None = None,
    ) -> tuple[Uuid7, ...]:
        """Delete a bounded set of unpinned versions older than the cutoff."""
        ...


DATA_SERIES_STORE_CAPABILITY: CapabilityKey[DataSeriesStoreCapability] = CapabilityKey(
    name="data.series-store",
    major=1,
)
