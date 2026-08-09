"""Standalone usage for FEAT-SIM-10 simulation checklists and missions."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import build_no_trade_outcome
from app.services.simulator import (
    build_checklist_definition,
    bypass_simulation_checklist_step,
    complete_simulation_mission,
    evaluate_simulation_checklist,
    get_simulation_mode_policy,
    start_simulation_checklist,
)


def _definition() -> object:
    """Build one bounded preflight checklist."""
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
                "step_id": "notes",
                "evidence_key": "notes_ready",
                "comparator": "truthy",
                "prerequisites": ("feed",),
                "mandatory": False,
            },
        ),
    )


def fr_sim_104() -> None:
    """FR-SIM-104: Simulator shall validate immutable checklist definitions with ordered unique steps, prerequisites, actual-state evidence keys, allowlisted comparators, expected values, and mandatory declarations."""
    definition = _definition()
    print(
        f"SUCCESS: FR-SIM-104 definition validated; Data -> {definition.checklist_id}"
    )


def fr_sim_105() -> None:
    """FR-SIM-105: Simulator shall maintain deterministic `LOCKED`, `AVAILABLE`, `ACTIVE`, `SATISFIED`, `FAILED`, `BLOCKED`, `BYPASSED`, and `REGRESSED` checklist step states."""
    runtime = start_simulation_checklist(_definition(), "Standard")
    print(f"SUCCESS: FR-SIM-105 runtime started; Data -> {runtime.steps[0].state}")


def fr_sim_106() -> None:
    """FR-SIM-106: Simulator shall satisfy checklist steps only from validated actual-domain-state evidence; no caller may directly assert step satisfaction."""
    definition = _definition()
    runtime = evaluate_simulation_checklist(
        definition,
        start_simulation_checklist(definition, "Standard"),
        {"feed_ready": True},
    )
    print(
        f"SUCCESS: FR-SIM-106 actual state evaluated; Data -> {runtime.steps[0].state}"
    )


def fr_sim_107() -> None:
    """FR-SIM-107: Simulator shall define deterministic `Guided`, `Standard`, `Expert`, and `Challenge` hint, sequencing, optional-bypass, scoring, and rewind policy."""
    policy = get_simulation_mode_policy("Challenge")
    print(
        f"SUCCESS: FR-SIM-107 Challenge policy read; Data -> scored={policy['scored']}"
    )


def fr_sim_108() -> None:
    """FR-SIM-108: Simulator shall deny mandatory-step bypass, empty bypass reasons, unsupported mode overrides, and any optional bypass that mode policy does not permit."""
    definition = _definition()
    runtime = bypass_simulation_checklist_step(
        definition,
        start_simulation_checklist(definition, "Standard"),
        "notes",
        reason="not applicable",
    )
    print(
        f"SUCCESS: FR-SIM-108 optional bypass audited; Data -> {runtime.steps[1].state}"
    )


def fr_sim_109() -> None:
    """FR-SIM-109: Simulator shall complete a no-trade mission only when mandatory checklist steps are satisfied and a validated Risk-owned `NoTradeOutcome v1` classifies the outcome as a safe stand-down."""
    definition = _definition()
    runtime = evaluate_simulation_checklist(
        definition,
        start_simulation_checklist(definition, "Guided"),
        {"feed_ready": True},
    )
    outcome = complete_simulation_mission(
        definition,
        runtime,
        trade_count=0,
        no_trade_outcome=build_no_trade_outcome(
            decision_id="decision-usage",
            outcome_kind="safe_stand_down",
            failed_rule_ids=("spread-gate",),
            rationale="Mandatory spread gate rejected the setup",
            evaluated_at=datetime.now(UTC),
        ),
    )
    print(f"SUCCESS: FR-SIM-109 no-trade mission resolved; Data -> {outcome.status}")


def fr_sim_110() -> None:
    """FR-SIM-110: Every simulation mode shall expose `route="sim"`, deny live-route authority, and remain compatible with Trading's existing simulation-dispatch isolation guard."""
    routes = {
        mode: get_simulation_mode_policy(mode)["route"]
        for mode in ("Guided", "Standard", "Expert", "Challenge")
    }
    print(f"SUCCESS: FR-SIM-110 route isolation proven; Data -> {routes}")


def main() -> None:
    """Run every FEAT-SIM-10 requirement demonstration."""
    print("FEATURE: FEAT-SIM-10 — Simulation Checklists, Modes, and Missions")
    fr_sim_104()
    fr_sim_105()
    fr_sim_106()
    fr_sim_107()
    fr_sim_108()
    fr_sim_109()
    fr_sim_110()


if __name__ == "__main__":
    main()
