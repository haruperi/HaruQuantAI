"""Persistence and scenario tracking for Synthetic Scenario Series."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import ContentHash, Uuid7
    from app.contracts.data.models import SyntheticModelSpec


class SyntheticScenarioPersistence:
    """In-memory model specification and generated scenario metadata store."""

    def __init__(self) -> None:
        self._specs: dict[Uuid7, SyntheticModelSpec] = {}
        self._scenarios: dict[Uuid7, tuple[ContentHash, str]] = {}

    def save_spec(self, spec: SyntheticModelSpec) -> None:
        """Store a synthetic model specification."""
        self._specs[spec.spec_id] = spec

    def get_spec(self, spec_id: Uuid7) -> SyntheticModelSpec | None:
        """Retrieve a model specification by ID."""
        return self._specs.get(spec_id)

    def get_all_specs(self) -> list[SyntheticModelSpec]:
        """Return all stored specifications."""
        return list(self._specs.values())

    def save_scenario(
        self, scenario_version_id: Uuid7, content_hash: ContentHash, classification: str
    ) -> None:
        """Record generated scenario version metadata."""
        self._scenarios[scenario_version_id] = (content_hash, classification)

    def get_scenario(
        self, scenario_version_id: Uuid7
    ) -> tuple[ContentHash, str] | None:
        """Retrieve generated scenario metadata."""
        return self._scenarios.get(scenario_version_id)

    def clear(self) -> None:
        """Reset all in-memory stores."""
        self._specs.clear()
        self._scenarios.clear()
