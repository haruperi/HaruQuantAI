"""Simulation scenario engine feature API."""

from app.services.simulator.scenarios.catalog import get_scenario_templates
from app.services.simulator.scenarios.contracts import (
    InjectedEvent,
    MissionDefinition,
    build_injected_event,
    build_mission_definition,
    build_seeded_fault_event,
)
from app.services.simulator.scenarios.providers import (
    build_scenario_evidence_provider,
    build_scenario_provider,
)
from app.services.simulator.scenarios.triggers import (
    evaluate_scenario_triggers,
    order_injected_events,
)

__all__ = [
    "InjectedEvent",
    "MissionDefinition",
    "build_injected_event",
    "build_mission_definition",
    "build_scenario_evidence_provider",
    "build_scenario_provider",
    "build_seeded_fault_event",
    "evaluate_scenario_triggers",
    "get_scenario_templates",
    "order_injected_events",
]
