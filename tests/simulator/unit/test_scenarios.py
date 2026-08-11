"""Unit evidence for FEAT-SIM-11 scenario behavior."""

from datetime import UTC, datetime

import pytest
from app.services.simulator import (
    build_injected_event,
    build_mission_definition,
    build_scenario_evidence_provider,
    build_scenario_provider,
    evaluate_scenario_triggers,
    get_scenario_templates,
    order_injected_events,
)
from app.services.simulator.errors import SimulationError


def _mission() -> object:
    """Build one deterministic trigger mission."""
    now = datetime.now(UTC)
    event = build_injected_event(
        event_id="event-1",
        event_type="flash_crash",
        priority=100,
        causative_at=now,
        effective_at=now,
        venue_at=now,
        perceived_at=now,
        suspends_normal_transitions=True,
        payload={},
    )
    return build_mission_definition(
        mission_id="flash-1",
        version="v1",
        market_data_ref="dataset-1",
        difficulty=8,
        seed=42,
        competence_tags=("risk",),
        triggers=(
            {
                "trigger_id": "price-break",
                "type": "price",
                "key": "price",
                "threshold": "1.05",
                "comparator": "lte",
            },
        ),
        events=(event,),
    )


def test_trigger_catalog_and_evidence_are_deterministic() -> None:
    """Evaluate triggers and expose bounded provider evidence."""
    mission = _mission()
    assert evaluate_scenario_triggers(mission, {"price": "1.04"}) == ("price-break",)
    assert "flash_crash" in get_scenario_templates()["emergency"]
    evidence = build_scenario_evidence_provider((mission,))("flash-1")
    assert evidence is not None
    assert evidence["difficulty"] == 8
    provider = build_scenario_provider((mission,))
    calibrated = provider.scenario_difficulty_calibration(
        market_data_ref="dataset-1", competence_target="risk"
    )
    assert calibrated["status"] == "CALIBRATED"


def test_ambiguous_event_priority_fails_closed() -> None:
    """Reject indistinguishable effective event priorities."""
    now = datetime.now(UTC)
    fields = {
        "event_type": "failure",
        "priority": 10,
        "causative_at": now,
        "effective_at": now,
        "venue_at": now,
        "perceived_at": now,
        "payload": {},
    }
    first = build_injected_event(event_id="a", **fields)
    second = build_injected_event(event_id="b", **fields)
    with pytest.raises(SimulationError, match="ambiguous"):
        order_injected_events((first, second))


def test_scenario_trigger_predicate_branches() -> None:
    """Test time, player_action, checklist, probability, and compound triggers."""
    now = datetime.now(UTC)

    time_mission = build_mission_definition(
        mission_id="m-time",
        version="v1",
        market_data_ref="d-1",
        difficulty=1,
        seed=123,
        competence_tags=("risk",),
        triggers=(
            {"trigger_id": "t-time", "type": "time", "at": now},
            {"trigger_id": "t-player", "type": "player_action", "action": "pause"},
            {
                "trigger_id": "t-chk",
                "type": "checklist",
                "step_id": "s1",
                "state": "DONE",
            },
            {"trigger_id": "t-prob", "type": "probability", "probability": "1.0"},
            {
                "trigger_id": "t-comp-all",
                "type": "compound",
                "operator": "all",
                "children": [
                    {"trigger_id": "c1", "type": "player_action", "action": "pause"},
                    {
                        "trigger_id": "c2",
                        "type": "checklist",
                        "step_id": "s1",
                        "state": "DONE",
                    },
                ],
            },
            {
                "trigger_id": "t-comp-any",
                "type": "compound",
                "operator": "any",
                "children": [
                    {"trigger_id": "c3", "type": "player_action", "action": "stop"},
                    {
                        "trigger_id": "c4",
                        "type": "checklist",
                        "step_id": "s1",
                        "state": "DONE",
                    },
                ],
            },
        ),
        events=(
            build_injected_event(
                event_id="e1",
                event_type="test",
                priority=1,
                causative_at=now,
                effective_at=now,
                venue_at=now,
                perceived_at=now,
                payload={},
            ),
        ),
    )

    state = {
        "timestamp": now,
        "player_action": "pause",
        "checklist": {"s1": "DONE"},
        "sequence": 1,
    }
    triggered = evaluate_scenario_triggers(time_mission, state)
    assert "t-time" in triggered
    assert "t-player" in triggered
    assert "t-chk" in triggered
    assert "t-prob" in triggered
    assert "t-comp-all" in triggered
    assert "t-comp-any" in triggered


def test_order_injected_events_suspending_transitions() -> None:
    """Order injected events with suspending normal transitions flag."""
    now = datetime.now(UTC)
    normal = build_injected_event(
        event_id="e-norm",
        event_type="test",
        priority=10,
        causative_at=now,
        effective_at=now,
        venue_at=now,
        perceived_at=now,
        suspends_normal_transitions=False,
        payload={},
    )
    suspending = build_injected_event(
        event_id="e-susp",
        event_type="test",
        priority=5,
        causative_at=now,
        effective_at=now,
        venue_at=now,
        perceived_at=now,
        suspends_normal_transitions=True,
        payload={},
    )
    ordered = order_injected_events((normal, suspending))
    assert len(ordered) == 1
    assert ordered[0].event_id == "e-susp"
