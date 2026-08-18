"""Approved reasoned stress-scenario catalogue and construction workflow."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any, TypedDict

from app.services.research.contracts.errors import ValidationError
from app.services.research.stress_evidence.contracts import (
    build_stress_scenario_evidence,
)
from app.services.research.stress_evidence.derivation import (
    build_reasoned_stress_shock,
)
from app.utils import canonical_json, derive_stable_id


class _ScenarioDefinition(TypedDict):
    """Internal immutable scenario definition shape."""

    name: str
    assumption_ref: str
    rationale: str
    shocks: tuple[tuple[str, float], ...]


_SCENARIOS: Mapping[str, _ScenarioDefinition] = MappingProxyType(
    {
        "broad_market_dislocation": {
            "name": "Broad market dislocation",
            "assumption_ref": "HQA-STRESS-ASSUMPTION-001-v1",
            "rationale": (
                "Tests simultaneous repricing, weaker liquidity, wider transaction "
                "costs, and correlation convergence."
            ),
            "shocks": (
                ("price", 30.0),
                ("spread", 100.0),
                ("liquidity", 40.0),
                ("correlation", 0.30),
            ),
        },
        "severe_fx_repricing": {
            "name": "Severe FX repricing",
            "assumption_ref": "HQA-STRESS-ASSUMPTION-002-v1",
            "rationale": (
                "Tests rapid currency revaluation with discontinuous opening prices "
                "and impaired execution."
            ),
            "shocks": (("fx", 15.0), ("gap", 5.0), ("spread", 50.0)),
        },
        "liquidity_withdrawal": {
            "name": "Liquidity withdrawal",
            "assumption_ref": "HQA-STRESS-ASSUMPTION-003-v1",
            "rationale": (
                "Tests reduced executable depth, sharply increased trading cost, "
                "and collateral pressure."
            ),
            "shocks": (("liquidity", 60.0), ("spread", 150.0), ("margin", 50.0)),
        },
        "venue_connectivity_disruption": {
            "name": "Venue and connectivity disruption",
            "assumption_ref": "HQA-STRESS-ASSUMPTION-004-v1",
            "rationale": (
                "Tests loss of connectivity followed by a bounded trading halt and "
                "adverse repricing when access returns."
            ),
            "shocks": (("connectivity", 120.0), ("halt", 300.0), ("gap", 8.0)),
        },
        "extreme_combined_tail": {
            "name": "Extreme combined tail",
            "assumption_ref": "HQA-STRESS-ASSUMPTION-005-v1",
            "rationale": (
                "Tests an explicitly severe multi-factor tail with the 50 percent "
                "price assumption aligned to the 2025 EBA equity-price stress."
            ),
            "shocks": (
                ("price", 50.0),
                ("spread", 250.0),
                ("liquidity", 75.0),
                ("fx", 20.0),
                ("correlation", 0.50),
                ("margin", 100.0),
            ),
        },
    }
)


def get_stress_scenario_catalog() -> tuple[dict[str, Any], ...]:
    """Return detached approved reasoned scenario definitions.

    Returns:
        Immutable-order JSON-safe scenario summaries.
    """
    return tuple(
        {
            "scenario_key": key,
            "name": definition["name"],
            "assumption_ref": definition["assumption_ref"],
            "rationale": definition["rationale"],
            "shocks": [
                {"shock_type": shock_type, "magnitude": magnitude}
                for shock_type, magnitude in definition["shocks"]
            ],
        }
        for key, definition in _SCENARIOS.items()
    )


def build_registered_stress_scenario(
    *, scenario_key: str, hypothesis: str, generated_at_utc: datetime
) -> dict[str, Any]:
    """Build canonical evidence from one approved reasoned scenario.

    Args:
        scenario_key: Approved catalogue key.
        hypothesis: Explicit stress objective.
        generated_at_utc: Evidence-generation instant.

    Returns:
        Validated stress-scenario evidence.

    Raises:
        ValidationError: If the key is unknown or evidence is invalid.
    """
    definition = _SCENARIOS.get(scenario_key)
    if definition is None:
        raise ValidationError("RES_STRESS_SCENARIO_INVALID", "SCENARIO_NOT_REGISTERED")
    assumption_ref = str(definition["assumption_ref"])
    rationale = str(definition["rationale"])
    shocks = tuple(
        build_reasoned_stress_shock(
            shock_type=str(shock_type),
            magnitude=float(magnitude),
            assumption_ref=assumption_ref,
            rationale=rationale,
        )
        for shock_type, magnitude in definition["shocks"]
    )
    scenario_id = derive_stable_id(
        "id", canonical_json({"scenario_key": scenario_key, "hypothesis": hypothesis})
    )
    return build_stress_scenario_evidence(
        scenario_id=scenario_id,
        hypothesis=hypothesis,
        shocks=shocks,
        generated_at_utc=generated_at_utc,
    )


__all__ = ("build_registered_stress_scenario", "get_stress_scenario_catalog")
