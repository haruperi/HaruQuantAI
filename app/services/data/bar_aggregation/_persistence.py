"""Persistence and lineage store for Bar Aggregation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import Timeframe, Uuid7
    from app.contracts.data.models import AggregationSpec


class BarAggregationPersistence:
    """In-memory lineage and timeframe definition persistence store."""

    def __init__(self) -> None:
        self._lineage: dict[Uuid7, tuple[Uuid7, str]] = {}
        self._custom_timeframes: dict[str, Timeframe] = {}

    def record_lineage(
        self,
        spec: AggregationSpec,
        derived_version_id: Uuid7,
        content_hash: str,
    ) -> None:
        """Record aggregation lineage link."""
        self._lineage[spec.spec_id] = (derived_version_id, content_hash)

    def get_lineage(self, spec_id: Uuid7) -> tuple[Uuid7, str] | None:
        """Retrieve lineage link by spec ID."""
        return self._lineage.get(spec_id)

    def register_timeframe(self, name: str, timeframe: Timeframe) -> None:
        """Store a custom defined timeframe."""
        self._custom_timeframes[name] = timeframe

    def get_timeframe(self, name: str) -> Timeframe | None:
        """Retrieve a custom defined timeframe."""
        return self._custom_timeframes.get(name)

    def clear(self) -> None:
        """Reset lineage and timeframe mappings."""
        self._lineage.clear()
        self._custom_timeframes.clear()
