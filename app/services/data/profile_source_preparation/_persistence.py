"""Persistence and source declaration store for Profile Source Preparation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import Uuid7
    from app.contracts.data.models import ProfileSourceDeclaration


class ProfileSourcePersistence:
    """In-memory validated profile source declaration store."""

    def __init__(self) -> None:
        self._sources: dict[Uuid7, ProfileSourceDeclaration] = {}

    def save_source(self, source: ProfileSourceDeclaration) -> None:
        """Store a validated profile source declaration."""
        self._sources[source.data_version_id] = source

    def get_source(self, data_version_id: Uuid7) -> ProfileSourceDeclaration | None:
        """Retrieve a profile source declaration by data version ID."""
        return self._sources.get(data_version_id)

    def get_all_sources(self) -> list[ProfileSourceDeclaration]:
        """Return all stored profile source declarations."""
        return list(self._sources.values())

    def clear(self) -> None:
        """Reset in-memory storage."""
        self._sources.clear()
