"""Persistence and storage management for External Indicator Series."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import Uuid7
    from app.contracts.data.models import ImportIndicatorsSuccess


class ExternalIndicatorPersistence:
    """In-memory storage for imported indicator series versions."""

    def __init__(self) -> None:
        self._imported_series: dict[Uuid7, ImportIndicatorsSuccess] = {}

    def save_series(self, version_id: Uuid7, result: ImportIndicatorsSuccess) -> None:
        """Store an imported indicator series result."""
        self._imported_series[version_id] = result

    def get_series(self, version_id: Uuid7) -> ImportIndicatorsSuccess | None:
        """Retrieve an imported indicator series result."""
        return self._imported_series.get(version_id)

    def get_all_series(self) -> list[ImportIndicatorsSuccess]:
        """Return all stored indicator series results."""
        return list(self._imported_series.values())

    def clear(self) -> None:
        """Reset storage."""
        self._imported_series.clear()
