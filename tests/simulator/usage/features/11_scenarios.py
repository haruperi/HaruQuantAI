"""Standalone usage for FEAT-SIM-11 scenario engine."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_injected_event,
    build_mission_definition,
    build_scenario_evidence_provider,
    build_scenario_provider,
    build_seeded_fault_event,
    create_realism_stream,
    evaluate_scenario_triggers,
    get_scenario_templates,
    order_injected_events,
)


def _event() -> object:
    """Build one bounded emergency event."""
    now = datetime.now(UTC)
    return build_injected_event(
        event_id="gap-1",
        event_type="market_gap",
        priority=100,
        causative_at=now,
        effective_at=now,
        venue_at=now,
        perceived_at=now,
        suspends_normal_transitions=True,
        payload={},
    )


def _mission() -> object:
    """Build one bounded mission definition."""
    return build_mission_definition(
        mission_id="mission-gap",
        version="v1",
        market_data_ref="dataset-usage",
        difficulty=6,
        seed=42,
        competence_tags=("execution",),
        triggers=(
            {
                "trigger_id": "price-trigger",
                "type": "price",
                "key": "price",
                "threshold": "1.05",
                "comparator": "lte",
            },
        ),
        events=(_event(),),
    )


def fr_sim_111() -> None:
    """FR-SIM-111: Simulator shall define immutable `MissionDefinition v1` separately from Risk's advisory scenario contract, with explicit identity, data reference, difficulty, seed, triggers, events, and competence tags."""
    mission = _mission()
    print(f"SUCCESS: FR-SIM-111 mission built; Data -> {mission.mission_id}")


def fr_sim_112() -> None:
    """FR-SIM-112: Simulator shall evaluate time, price, volatility, liquidity, player-action, checklist, account-state, compound, and seeded probabilistic triggers deterministically."""
    triggered = evaluate_scenario_triggers(_mission(), {"price": "1.04"})
    print(f"SUCCESS: FR-SIM-112 triggers evaluated; Data -> {triggered}")


def fr_sim_113() -> None:
    """FR-SIM-113: Simulator shall expose validated emergency scenario templates for flash crashes, API failure, drawdown breach, margin survival, and recovery failure."""
    templates = get_scenario_templates()
    print(
        f"SUCCESS: FR-SIM-113 emergency catalog read; Data -> {templates['emergency']}"
    )


def fr_sim_114() -> None:
    """FR-SIM-114: Simulator shall expose abnormal-operation templates for bad ticks, feed disagreement, market halts and gaps, margin changes, rejection, cancel-fill races, clock drift, and process failure."""
    templates = get_scenario_templates()
    print(f"SUCCESS: FR-SIM-114 abnormal catalog read; Data -> {templates['abnormal']}")


def fr_sim_115() -> None:
    """FR-SIM-115: Simulator shall define immutable `InjectedEvent` values with causative, effective, venue, and perception timestamps that preserve causal order."""
    event = _event()
    print(f"SUCCESS: FR-SIM-115 event built; Data -> {event.event_id}")


def fr_sim_116() -> None:
    """FR-SIM-116: Simulator shall apply a total effective-time and priority order to injected events, suspend incompatible normal transitions, and fail closed on ambiguous priority."""
    ordered = order_injected_events((_event(),))
    print(f"SUCCESS: FR-SIM-116 events ordered; Data -> {ordered[0].event_id}")


def fr_sim_117() -> None:
    """FR-SIM-117: Simulator shall provide bounded scenario evidence, difficulty calibration, and holdout-mask adapters for the Research and Optimization consumer ports."""
    mission = _mission()
    provider = build_scenario_provider((mission,))
    evidence_provider = build_scenario_evidence_provider((mission,))
    evidence = evidence_provider("mission-gap")
    calibration = provider.scenario_difficulty_calibration(
        market_data_ref="dataset-usage", competence_target="execution"
    )
    print(
        f"SUCCESS: FR-SIM-117 providers built; Data -> evidence={evidence is not None}, status={calibration['status']}"
    )


def fr_sim_229() -> None:
    """FR-SIM-229: Scenario alone creates seeded infrastructure faults."""
    event = build_seeded_fault_event(
        stream=create_realism_stream({"seed": 42}, "fault"),
        fault_type="disconnect",
        probability=Decimal(1),
        occurred_at=datetime.now(UTC),
        artifact_checksum="a" * 64,
    )
    print(
        f"SUCCESS: FR-SIM-229 seeded fault; Data -> {event.event_type if event else 'none'}"
    )


def main() -> None:
    """Run every FEAT-SIM-11 requirement demonstration."""
    print("FEATURE: FEAT-SIM-11 — Scenario Engine")
    fr_sim_111()
    fr_sim_112()
    fr_sim_113()
    fr_sim_114()
    fr_sim_115()
    fr_sim_116()
    fr_sim_117()
    fr_sim_229()


if __name__ == "__main__":
    main()
