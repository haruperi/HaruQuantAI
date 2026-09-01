"""Simulator-owned scenario evidence and calibration providers."""

# ruff: noqa: TC001

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from hashlib import sha256

from app.kernel.serialization import canonical_json
from app.services.simulator.scenarios.contracts import MissionDefinition


class _ScenarioProvider:
    """Private provider satisfying Research and Optimization consumer ports."""

    def __init__(self, definitions: Sequence[MissionDefinition]) -> None:
        self._definitions = {item.mission_id: item for item in definitions}

    def scenario_evidence(self, scenario_id: str) -> Mapping[str, object] | None:
        """Return bounded evidence for one known scenario."""
        definition = self._definitions.get(scenario_id)
        if definition is None:
            return None
        payload = definition.model_dump(mode="json")
        return {
            "scenario_id": definition.mission_id,
            "version": definition.version,
            "difficulty": definition.difficulty,
            "definition_hash": sha256(canonical_json(payload).encode()).hexdigest(),
        }

    def scenario_difficulty_calibration(
        self, *, market_data_ref: str, competence_target: str
    ) -> Mapping[str, object]:
        """Return deterministic difficulty evidence for matching definitions."""
        matches = [
            item
            for item in self._definitions.values()
            if item.market_data_ref == market_data_ref
            and (not item.competence_tags or competence_target in item.competence_tags)
        ]
        return {
            "status": "CALIBRATED" if matches else "NOT_CALIBRATED",
            "scenario_ids": tuple(sorted(item.mission_id for item in matches)),
            "difficulty_levels": tuple(sorted({item.difficulty for item in matches})),
            "competence_target": competence_target,
        }

    def scenario_holdout_mask(
        self, *, market_data_ref: str, validation_window: tuple[str, str]
    ) -> Mapping[str, object]:
        """Return stable scenario identities held out for one data reference."""
        candidates = sorted(
            item.mission_id
            for item in self._definitions.values()
            if item.market_data_ref == market_data_ref
        )
        material = canonical_json(
            {"market_data_ref": market_data_ref, "validation_window": validation_window}
        )
        held_out = tuple(
            identity
            for identity in candidates
            if int(sha256(f"{material}|{identity}".encode()).hexdigest()[-1], 16) % 2
        )
        return {
            "status": "HOLDOUT_LOCKED" if held_out else "SCENARIO_HOLDOUT_UNAVAILABLE",
            "decision": "ready_for_validation" if held_out else "validation_needed",
            "held_out_scenario_ids": held_out,
            "validation_window": validation_window,
        }


def build_scenario_provider(
    definitions: Sequence[MissionDefinition],
) -> object:
    """Build one opaque Simulator scenario provider.

    Args:
        definitions: Validated mission definitions.

    Returns:
        Opaque provider satisfying declared consumer protocols.

    Raises:
        ValueError: If definitions are empty or duplicate identities exist.
    """
    if not definitions or len({item.mission_id for item in definitions}) != len(
        definitions
    ):
        raise ValueError("scenario provider requires unique definitions")
    return _ScenarioProvider(definitions)


def build_scenario_evidence_provider(
    definitions: Sequence[MissionDefinition],
) -> Callable[[str], Mapping[str, object] | None]:
    """Build the callable Research scenario-evidence provider.

    Args:
        definitions: Validated mission definitions.

    Returns:
        Callable returning bounded scenario evidence.
    """
    provider = _ScenarioProvider(definitions)
    return provider.scenario_evidence


__all__ = ["build_scenario_evidence_provider", "build_scenario_provider"]
