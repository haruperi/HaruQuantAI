"""Persistence and storage management for Economic News Evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.data.models import (
        MarketNewsObservation,
        MarketNewsRevision,
    )


class EconomicNewsPersistenceStore:
    """In-memory observation and revision persistence store."""

    def __init__(self) -> None:
        self._observations: dict[str, MarketNewsObservation] = {}
        self._source_index: dict[tuple[str, str], str] = {}
        self._revisions: dict[str, list[MarketNewsRevision]] = {}
        self._rate_limits: dict[str, list[float]] = {}
        self._checkpoints: dict[str, str] = {}

    def add_observation(self, obs: MarketNewsObservation) -> None:
        """Store an economic news observation and index by source key."""
        self._observations[obs.observation_id] = obs
        self._source_index[(obs.source_id, obs.provider_item_id)] = obs.observation_id

    def get_observation(self, observation_id: str) -> MarketNewsObservation | None:
        """Retrieve an observation by its ID."""
        return self._observations.get(observation_id)

    def get_all_observations(self) -> list[MarketNewsObservation]:
        """Return all stored observations."""
        return list(self._observations.values())

    def get_by_source_key(
        self,
        source_id: str,
        item_id: str,
    ) -> MarketNewsObservation | None:
        """Retrieve an observation by its source and provider item ID."""
        obs_id = self._source_index.get((source_id, item_id))
        return self._observations.get(obs_id) if obs_id else None

    def add_revision(self, revision: MarketNewsRevision) -> None:
        """Store an observation revision."""
        revs = self._revisions.setdefault(revision.observation_id, [])
        revs.append(revision)

    def get_revisions(self, observation_id: str) -> list[MarketNewsRevision]:
        """Retrieve all revisions for an observation."""
        return list(self._revisions.get(observation_id, []))

    def record_rate_limit(self, source_id: str, ts: float) -> None:
        """Record an API request timestamp for rate limit tracking."""
        self._rate_limits.setdefault(source_id, []).append(ts)

    def get_rate_limits(self, source_id: str) -> list[float]:
        """Retrieve rate limit timestamps for a source."""
        return self._rate_limits.get(source_id, [])

    def set_checkpoint(self, source_id: str, checkpoint: str) -> None:
        """Record sync checkpoint for a source."""
        self._checkpoints[source_id] = checkpoint

    def get_checkpoint(self, source_id: str) -> str | None:
        """Get sync checkpoint for a source."""
        return self._checkpoints.get(source_id)

    def clear(self) -> None:
        """Reset all in-memory structures."""
        self._observations.clear()
        self._source_index.clear()
        self._revisions.clear()
        self._rate_limits.clear()
        self._checkpoints.clear()
