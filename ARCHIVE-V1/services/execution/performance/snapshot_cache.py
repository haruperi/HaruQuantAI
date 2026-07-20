"""Hot snapshot caching with freshness metadata.

Classes and functions:
    SnapshotCacheEntry: Class. Provides SnapshotCacheEntry behavior for execution workflows.
    HotSnapshotCache: Class. Provides HotSnapshotCache behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from app.services.utils import Clock, FreshnessWindow, SystemClock
from app.services.utils.normalization import evaluate_freshness

SnapshotT = TypeVar("SnapshotT")


@dataclass(frozen=True)
class SnapshotCacheEntry(Generic[SnapshotT]):
    """Represent SnapshotCacheEntry behavior in execution service workflows."""

    key: str
    snapshot: SnapshotT
    observed_at: object
    max_age_seconds: int

    def freshness(self, *, clock: Clock | None = None) -> FreshnessWindow:
        """Perform the freshness execution service operation."""
        return evaluate_freshness(
            self.observed_at,
            max_age_seconds=self.max_age_seconds,
            clock=clock,
        )


class HotSnapshotCache(Generic[SnapshotT]):
    """Small in-memory stand-in for a Redis-backed hot snapshot cache."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._entries: dict[str, SnapshotCacheEntry[SnapshotT]] = {}

    def put(
        self, entry: SnapshotCacheEntry[SnapshotT]
    ) -> SnapshotCacheEntry[SnapshotT]:
        """Perform the put execution service operation."""
        self._entries[entry.key] = entry
        return entry

    def get(self, key: str) -> SnapshotCacheEntry[SnapshotT] | None:
        """Perform the get execution service operation."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.freshness(clock=self._clock).is_stale:
            self._entries.pop(key, None)
            return None
        return entry
