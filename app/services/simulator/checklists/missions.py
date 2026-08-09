"""Mission completion from checklist and Risk-owned no-trade evidence."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.simulator.checklists.contracts import (
    ChecklistDefinition,
    ChecklistRuntime,
    MissionOutcome,
)


def complete_simulation_mission(
    definition: ChecklistDefinition,
    runtime: ChecklistRuntime,
    *,
    trade_count: int,
    no_trade_outcome: Mapping[str, object] | None = None,
) -> MissionOutcome:
    """Resolve mission completion without requiring a trade.

    Args:
        definition: Mission checklist definition.
        runtime: Current checklist runtime.
        trade_count: Validated number of simulated trades.
        no_trade_outcome: Optional Risk-owned parsed no-trade outcome mapping.

    Returns:
        Deterministic mission outcome.

    Raises:
        ValueError: If the trade count is negative.
    """
    if trade_count < 0:
        raise ValueError("trade_count must be non-negative")
    states = {step.step_id: step.state for step in runtime.steps}
    mandatory = [step.step_id for step in definition.steps if step.mandatory]
    satisfied = sum(states.get(step_id) == "SATISFIED" for step_id in mandatory)
    if satisfied != len(mandatory):
        return MissionOutcome(
            status="INCOMPLETE",
            reason="mandatory_checklist_incomplete",
            safe_stand_down=False,
            satisfied_steps=satisfied,
            required_steps=len(mandatory),
        )
    safe_stand_down = bool(
        no_trade_outcome
        and no_trade_outcome.get("schema_id") == "risk.no_trade_outcome.v1"
        and no_trade_outcome.get("outcome_kind") == "safe_stand_down"
    )
    if trade_count == 0 and not safe_stand_down:
        return MissionOutcome(
            status="FAILED",
            reason="no_trade_without_safe_stand_down_evidence",
            safe_stand_down=False,
            satisfied_steps=satisfied,
            required_steps=len(mandatory),
        )
    return MissionOutcome(
        status="PASSED",
        reason="safe_stand_down" if safe_stand_down else "mission_completed",
        safe_stand_down=safe_stand_down,
        satisfied_steps=satisfied,
        required_steps=len(mandatory),
    )


__all__ = ["complete_simulation_mission"]
