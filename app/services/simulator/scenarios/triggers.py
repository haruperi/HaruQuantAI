"""Deterministic evaluation and ordering for scenario triggers and events."""

# ruff: noqa: DOC201, PLR0911, TC001

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from app.services.simulator.errors import SimulationError
from app.services.simulator.scenarios.contracts import InjectedEvent, MissionDefinition


def _decimal(value: object) -> Decimal | None:
    """Return a finite Decimal or ``None`` for invalid evidence."""
    try:
        parsed = Decimal(str(value))
    except InvalidOperation, TypeError, ValueError:
        return None
    return parsed if parsed.is_finite() else None


def _simple_trigger(trigger: Mapping[str, object], state: Mapping[str, object]) -> bool:
    """Evaluate one non-compound trigger against bounded state."""
    trigger_type = trigger["type"]
    if trigger_type == "time":
        current = state.get("timestamp")
        threshold = trigger.get("at")
        return (
            isinstance(current, datetime)
            and isinstance(threshold, datetime)
            and current >= threshold
        )
    if trigger_type in {"price", "volatility", "liquidity", "account_state"}:
        key = str(trigger.get("key", trigger_type))
        actual = _decimal(state.get(key))
        expected = _decimal(trigger.get("threshold"))
        if actual is None or expected is None:
            return False
        comparator = trigger.get("comparator", "gte")
        return actual >= expected if comparator == "gte" else actual <= expected
    if trigger_type == "player_action":
        return state.get("player_action") == trigger.get("action")
    if trigger_type == "checklist":
        checklist = state.get("checklist")
        return isinstance(checklist, Mapping) and checklist.get(
            trigger.get("step_id")
        ) == trigger.get("state")
    if trigger_type == "probability":
        probability = _decimal(trigger.get("probability"))
        if probability is None or not Decimal(0) <= probability <= Decimal(1):
            return False
        material = (
            f"{trigger['trigger_id']}|{state.get('sequence', 0)}|{state.get('seed', 0)}"
        )
        draw = Decimal(int(sha256(material.encode()).hexdigest()[:16], 16)) / Decimal(
            16**16
        )
        return draw < probability
    return False


def _trigger_matches(
    trigger: Mapping[str, object], state: Mapping[str, object]
) -> bool:
    """Evaluate one trigger, including recursive compound predicates."""
    if trigger["type"] != "compound":
        return _simple_trigger(trigger, state)
    children = trigger.get("children")
    if (
        not isinstance(children, Sequence)
        or isinstance(children, (str, bytes))
        or not children
    ):
        return False
    typed_children = [child for child in children if isinstance(child, Mapping)]
    if len(typed_children) != len(children):
        return False
    results = [_trigger_matches(child, state) for child in typed_children]
    return all(results) if trigger.get("operator") == "all" else any(results)


def evaluate_scenario_triggers(
    definition: MissionDefinition, state: Mapping[str, object]
) -> tuple[str, ...]:
    """Return triggered identities in definition order.

    Args:
        definition: Validated mission definition.
        state: Actual simulation state and explicit deterministic sequence.

    Returns:
        Ordered triggered identities.
    """
    seeded_state = dict(state)
    seeded_state["seed"] = definition.seed
    return tuple(
        str(trigger["trigger_id"])
        for trigger in definition.triggers
        if _trigger_matches(trigger, seeded_state)
    )


def order_injected_events(events: Sequence[InjectedEvent]) -> tuple[InjectedEvent, ...]:
    """Order events by effective time and priority, failing on ambiguity.

    Args:
        events: Candidate injected events.

    Returns:
        Totally ordered immutable events.

    Raises:
        SimulationError: If incompatible events have indistinguishable priority.
    """
    identities: set[tuple[datetime, int]] = set()
    for event in events:
        key = (event.effective_at, event.priority)
        if key in identities:
            raise SimulationError(
                "SIM_EVENT_PRIORITY_AMBIGUOUS",
                "Injected events have ambiguous effective priority",
            )
        identities.add(key)
    ordered = sorted(
        events, key=lambda item: (item.effective_at, -item.priority, item.event_id)
    )
    suspending = [event for event in ordered if event.suspends_normal_transitions]
    normal = [event for event in ordered if not event.suspends_normal_transitions]
    return tuple(suspending or normal)


__all__ = ["evaluate_scenario_triggers", "order_injected_events"]
