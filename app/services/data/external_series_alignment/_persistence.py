"""Persistence and storage management for External Series Alignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import Uuid7
    from app.contracts.data.models import (
        AlignedSeries,
        AlignmentPolicy,
    )


class SeriesAlignmentPersistence:
    """In-memory alignment policy and aligned series storage."""

    def __init__(self) -> None:
        self._policies: dict[str, AlignmentPolicy] = {}
        self._aligned_series: dict[Uuid7, AlignedSeries] = {}

    def save_policy(self, name: str, policy: AlignmentPolicy) -> None:
        """Store an alignment policy."""
        self._policies[name] = policy

    def get_policy(self, name: str) -> AlignmentPolicy | None:
        """Retrieve an alignment policy."""
        return self._policies.get(name)

    def save_aligned_series(self, series: AlignedSeries) -> None:
        """Store an aligned series reference."""
        self._aligned_series[series.aligned_version_id] = series

    def get_aligned_series(self, version_id: Uuid7) -> AlignedSeries | None:
        """Retrieve aligned series by version ID."""
        return self._aligned_series.get(version_id)

    def get_all_aligned_series(self) -> list[AlignedSeries]:
        """Return all stored aligned series."""
        return list(self._aligned_series.values())

    def clear(self) -> None:
        """Reset all in-memory alignment stores."""
        self._policies.clear()
        self._aligned_series.clear()
