"""Persistence and batch tracking for Tick Normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.data.models import Tick


class TickNormalizationPersistence:
    """In-memory store for normalized tick batches."""

    def __init__(self) -> None:
        self._batches: dict[str, tuple[Tick, ...]] = {}

    def save_batch(self, batch_id: str, ticks: tuple[Tick, ...]) -> None:
        """Store a normalized tick batch."""
        self._batches[batch_id] = ticks

    def get_batch(self, batch_id: str) -> tuple[Tick, ...] | None:
        """Retrieve a normalized tick batch by ID."""
        return self._batches.get(batch_id)

    def get_all_batches(self) -> list[tuple[Tick, ...]]:
        """Return all stored tick batches."""
        return list(self._batches.values())

    def clear(self) -> None:
        """Reset batch storage."""
        self._batches.clear()
