"""Unit evidence for FEAT-SIM-10 checklists, modes, and missions."""

from datetime import UTC, datetime

import pytest
from app.services.risk import build_no_trade_outcome
from app.services.simulator import (
    build_checklist_definition,
    bypass_simulation_checklist_step,
    complete_simulation_mission,
    evaluate_simulation_checklist,
    get_simulation_mode_policy,
    start_simulation_checklist,
)
from app.services.simulator.errors import SimulationError


def _definition() -> object:
    """Build the two-step test checklist."""
    return build_checklist_definition(
        checklist_id="preflight",
        version="v1",
        steps=(
            {
                "step_id": "feed",
                "evidence_key": "feed_ready",
                "comparator": "eq",
                "expected": True,
            },
            {
                "step_id": "optional_note",
                "evidence_key": "note_written",
                "comparator": "truthy",
                "prerequisites": ("feed",),
                "mandatory": False,
            },
        ),
    )


def test_actual_state_unlocks_and_regresses_steps() -> None:
    """Bind satisfaction only to supplied actual-state evidence."""
    definition = _definition()
    runtime = start_simulation_checklist(definition, "Standard")
    evaluated = evaluate_simulation_checklist(
        definition, runtime, {"feed_ready": True, "note_written": True}
    )
    assert [step.state for step in evaluated.steps] == ["SATISFIED", "SATISFIED"]
    regressed = evaluate_simulation_checklist(
        definition, evaluated, {"feed_ready": False, "note_written": True}
    )
    assert regressed.steps[0].state == "REGRESSED"
    assert regressed.steps[1].state == "LOCKED"


def test_mode_policy_is_simulation_only_and_bypass_is_fail_closed() -> None:
    """Allow only Standard/Expert optional bypass and never a live route."""
    definition = _definition()
    standard = start_simulation_checklist(definition, "Standard")
    bypassed = bypass_simulation_checklist_step(
        definition, standard, "optional_note", reason="not applicable"
    )
    assert bypassed.steps[1].state == "BYPASSED"
    assert get_simulation_mode_policy("Challenge")["live_route_allowed"] is False
    with pytest.raises(SimulationError, match="bypass denied"):
        bypass_simulation_checklist_step(
            definition,
            start_simulation_checklist(definition, "Challenge"),
            "optional_note",
            reason="skip",
        )


def test_safe_stand_down_completes_a_no_trade_mission() -> None:
    """Accept Risk-owned safe-stand-down evidence as mission success."""
    definition = _definition()
    runtime = evaluate_simulation_checklist(
        definition,
        start_simulation_checklist(definition, "Guided"),
        {"feed_ready": True},
    )
    evidence = build_no_trade_outcome(
        decision_id="decision-1",
        outcome_kind="safe_stand_down",
        failed_rule_ids=("mandatory-spread",),
        rationale="Spread gate correctly rejected the setup",
        evaluated_at=datetime.now(UTC),
    )
    outcome = complete_simulation_mission(
        definition, runtime, trade_count=0, no_trade_outcome=evidence
    )
    assert outcome.status == "PASSED"
    assert outcome.safe_stand_down is True


def test_checklist_runtime_comparators_and_error_paths() -> None:
    """Test ne, gte, lte comparators and identity mismatch errors."""
    def_comp = build_checklist_definition(
        checklist_id="comp-test",
        version="v1",
        steps=(
            {
                "step_id": "ne-step",
                "evidence_key": "val_ne",
                "comparator": "ne",
                "expected": 10,
            },
            {
                "step_id": "gte-step",
                "evidence_key": "val_gte",
                "comparator": "gte",
                "expected": 5,
            },
            {
                "step_id": "lte-step",
                "evidence_key": "val_lte",
                "comparator": "lte",
                "expected": 5,
            },
        ),
    )
    runtime = start_simulation_checklist(def_comp, "Standard")
    evaluated = evaluate_simulation_checklist(
        def_comp, runtime, {"val_ne": 20, "val_gte": 10, "val_lte": 3}
    )
    assert [step.state for step in evaluated.steps] == [
        "SATISFIED",
        "SATISFIED",
        "SATISFIED",
    ]

    # Test identity mismatch
    wrong_def = build_checklist_definition(
        checklist_id="wrong-id",
        version="v1",
        steps=({"step_id": "other-step", "evidence_key": "k", "comparator": "truthy"},),
    )
    with pytest.raises(SimulationError, match="mismatch"):
        evaluate_simulation_checklist(wrong_def, runtime, {})


def test_mission_completion_failed_outcome() -> None:
    """Test mission completion when mandatory step is not satisfied."""
    definition = _definition()
    runtime = start_simulation_checklist(definition, "Standard")
    outcome = complete_simulation_mission(definition, runtime, trade_count=0)
    assert outcome.status == "INCOMPLETE"
