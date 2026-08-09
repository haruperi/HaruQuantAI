"""Deterministic actual-state-bound checklist runtime."""

# ruff: noqa: DOC201, PLR0911

from __future__ import annotations

from collections.abc import Mapping

from app.services.simulator.checklists.contracts import (
    ChecklistDefinition,
    ChecklistRuntime,
    ChecklistStepDefinition,
    ChecklistStepRuntime,
    SimulationMode,
)
from app.services.simulator.checklists.policies import get_simulation_mode_policy
from app.services.simulator.errors import SimulationError
from app.utils import get_logger

logger = get_logger(__name__)


def start_checklist(
    definition: ChecklistDefinition, mode: SimulationMode
) -> ChecklistRuntime:
    """Start a checklist with only dependency-free steps available.

    Args:
        definition: Validated checklist definition.
        mode: Simulation assistance mode.

    Returns:
        Initial immutable runtime.
    """
    get_simulation_mode_policy(mode)
    return ChecklistRuntime(
        checklist_id=definition.checklist_id,
        version=definition.version,
        mode=mode,
        steps=tuple(
            ChecklistStepRuntime(
                step_id=step.step_id,
                state="AVAILABLE" if not step.prerequisites else "LOCKED",
            )
            for step in definition.steps
        ),
    )


def _matches(step: ChecklistStepDefinition, actual: object) -> bool:
    """Evaluate one allowlisted evidence comparator."""
    if step.comparator == "truthy":
        return bool(actual)
    if step.comparator == "eq":
        return actual == step.expected
    if step.comparator == "ne":
        return actual != step.expected
    if isinstance(actual, bool) or not isinstance(actual, (int, str)):
        return False
    if isinstance(step.expected, bool):
        return False
    if isinstance(actual, int) and isinstance(step.expected, int):
        return (
            actual >= step.expected
            if step.comparator == "gte"
            else actual <= step.expected
        )
    if isinstance(actual, str) and isinstance(step.expected, str):
        return (
            actual >= step.expected
            if step.comparator == "gte"
            else actual <= step.expected
        )
    return False


def evaluate_checklist(
    definition: ChecklistDefinition,
    runtime: ChecklistRuntime,
    actual_state: Mapping[str, object],
) -> ChecklistRuntime:
    """Evaluate checklist predicates only against actual-state evidence.

    Args:
        definition: Definition matching the runtime identity.
        runtime: Current runtime.
        actual_state: Read-only actual-domain-state evidence.

    Returns:
        Updated immutable runtime.

    Raises:
        SimulationError: If identities or stored step state are inconsistent.
    """
    logger.info("Evaluating Simulation checklist %s", runtime.checklist_id)
    if (runtime.checklist_id, runtime.version) != (
        definition.checklist_id,
        definition.version,
    ):
        raise SimulationError("SIM_CHECKLIST_INVALID", "Checklist identity mismatch")
    current = {step.step_id: step for step in runtime.steps}
    next_steps: list[ChecklistStepRuntime] = []
    satisfied: set[str] = {
        step.step_id for step in runtime.steps if step.state == "SATISFIED"
    }
    for definition_step in definition.steps:
        prior = current.get(definition_step.step_id)
        if prior is None:
            raise SimulationError("SIM_CHECKLIST_INVALID", "Checklist step is missing")
        prerequisites_ready = set(definition_step.prerequisites) <= satisfied
        if prior.state in {"BYPASSED", "BLOCKED", "FAILED"}:
            next_step = prior
        elif not prerequisites_ready:
            next_step = prior.model_copy(update={"state": "LOCKED"})
        elif definition_step.evidence_key not in actual_state:
            state = "REGRESSED" if prior.state == "SATISFIED" else "ACTIVE"
            next_step = prior.model_copy(update={"state": state, "evidence": None})
        else:
            evidence = actual_state[definition_step.evidence_key]
            state = "SATISFIED" if _matches(definition_step, evidence) else "ACTIVE"
            if prior.state == "SATISFIED" and state != "SATISFIED":
                state = "REGRESSED"
            next_step = prior.model_copy(update={"state": state, "evidence": evidence})
        next_steps.append(next_step)
        if next_step.state == "SATISFIED":
            satisfied.add(next_step.step_id)
        else:
            satisfied.discard(next_step.step_id)
    return runtime.model_copy(update={"steps": tuple(next_steps)})


def bypass_checklist_step(
    definition: ChecklistDefinition,
    runtime: ChecklistRuntime,
    step_id: str,
    *,
    reason: str,
) -> ChecklistRuntime:
    """Bypass an optional step only when the selected mode permits it.

    Args:
        definition: Checklist definition.
        runtime: Current checklist runtime.
        step_id: Step to bypass.
        reason: Non-empty audited bypass reason.

    Returns:
        Updated runtime.

    Raises:
        SimulationError: If the step or policy disallows bypass.
    """
    policy = get_simulation_mode_policy(runtime.mode)
    definitions = {step.step_id: step for step in definition.steps}
    step = definitions.get(step_id)
    if (
        step is None
        or step.mandatory
        or not policy["bypass_optional"]
        or not reason.strip()
    ):
        raise SimulationError("SIM_CHECKLIST_BYPASS_DENIED", "Checklist bypass denied")
    return runtime.model_copy(
        update={
            "steps": tuple(
                item.model_copy(update={"state": "BYPASSED", "reason": reason.strip()})
                if item.step_id == step_id
                else item
                for item in runtime.steps
            )
        }
    )


__all__ = ["bypass_checklist_step", "evaluate_checklist", "start_checklist"]
