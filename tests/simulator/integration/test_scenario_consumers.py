"""Cross-domain evidence for Simulator scenario and realism providers."""

from datetime import UTC, datetime

from app.services.optimization import (
    evaluate_scenario_holdout,
    resolve_fill_model_calibration,
    resolve_scenario_difficulty_calibration,
)
from app.services.research import build_scenario_evidence_port
from app.services.simulator import (
    build_fill_model_provider,
    build_injected_event,
    build_mission_definition,
    build_scenario_evidence_provider,
    build_scenario_provider,
)


def _mission() -> object:
    """Build one mission used by every consumer port."""
    now = datetime.now(UTC)
    event = build_injected_event(
        event_id="event-1",
        event_type="market_gap",
        priority=10,
        causative_at=now,
        effective_at=now,
        venue_at=now,
        perceived_at=now,
        payload={},
    )
    return build_mission_definition(
        mission_id="mission-1",
        version="v1",
        market_data_ref="dataset-1",
        difficulty=6,
        seed=5,
        competence_tags=("execution",),
        triggers=(
            {
                "trigger_id": "action",
                "type": "player_action",
                "action": "submit",
            },
        ),
        events=(event,),
    )


def test_scenario_provider_satisfies_optimization_and_research_ports() -> None:
    """Use only domain-root APIs to satisfy all declared scenario consumers."""
    mission = _mission()
    provider = build_scenario_provider((mission,))
    calibration = resolve_scenario_difficulty_calibration(
        market_data_ref="dataset-1",
        competence_target="execution",
        provider=provider,
    )
    assert calibration["status"] == "CALIBRATED"
    holdout = evaluate_scenario_holdout(
        market_data_ref="dataset-1",
        validation_window=("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
        provider=provider,
    )
    assert holdout["status"] in {"HOLDOUT_LOCKED", "SCENARIO_HOLDOUT_UNAVAILABLE"}
    consumer = build_scenario_evidence_port(
        build_scenario_evidence_provider((mission,))
    )
    assert consumer("mission-1") == "AVAILABLE"


def test_realism_provider_satisfies_optimization_fill_port() -> None:
    """Pass explicit fill evidence through Optimization without inference."""
    provider = build_fill_model_provider(
        {"EURUSD": {"market_data_ref": "dataset-1", "latency_ms": 5}}
    )
    evidence = resolve_fill_model_calibration(
        market_data_ref="dataset-1", instrument="EURUSD", provider=provider
    )
    assert evidence["status"] == "CALIBRATED"
