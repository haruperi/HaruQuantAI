"""Pure generic transition-table validation and evaluation."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence

from app.utils.errors.exceptions import ValidationError


def build_transition_table(
    edges: Mapping[str, Sequence[str]],
    *,
    terminal_states: Sequence[str],
    ranks: Mapping[str, int] | None = None,
) -> dict[str, object]:
    """Build a validated JSON-safe transition table.

    Args:
        edges: Declared state edges.
        terminal_states: Explicit terminal states.
        ranks: Optional complete state ranks.

    Returns:
        Detached transition table.

    Raises:
        ValidationError: If the table is inconsistent.
    """
    if not edges or any(not state for state in edges):
        raise ValidationError("TRANSITION_TABLE_INVALID")
    states = set(edges)
    terminals = set(terminal_states)
    for source, targets in edges.items():
        if source in terminals and targets:
            raise ValidationError("TERMINAL_EDGE_INVALID")
        if len(targets) != len(set(targets)) or any(
            target not in states for target in targets
        ):
            raise ValidationError("TRANSITION_EDGE_INVALID")
    start = next(iter(edges))
    reached = {start}
    pending = deque([start])
    while pending:
        for target in edges[pending.popleft()]:
            if target not in reached:
                reached.add(target)
                pending.append(target)
    if reached != states or not terminals <= states:
        raise ValidationError("TRANSITION_STATE_UNREACHABLE")
    if ranks is not None and set(ranks) != states:
        raise ValidationError("TRANSITION_RANK_INVALID")
    return {
        "edges": {state: list(targets) for state, targets in edges.items()},
        "terminal_states": sorted(terminals),
        "ranks": dict(ranks) if ranks is not None else None,
    }


def is_terminal_state(table: Mapping[str, object], state: str) -> bool:
    """Return whether a known state is terminal.

    Args:
        table: Validated transition table.
        state: State to inspect.

    Returns:
        Whether the state is terminal.

    Raises:
        ValidationError: If the table or state is unknown.
    """
    edges = table.get("edges")
    if not isinstance(edges, Mapping) or state not in edges:
        raise ValidationError("TRANSITION_STATE_UNKNOWN")
    terminals = table.get("terminal_states")
    if not isinstance(terminals, list):
        raise ValidationError("TRANSITION_TABLE_INVALID")
    return state in terminals


def attempt_transition(
    table: Mapping[str, object], source: str, target: str
) -> dict[str, object]:
    """Evaluate one transition without mutating caller state.

    Args:
        table: Validated transition table.
        source: Current state.
        target: Proposed state.

    Returns:
        TransitionResult v1 mapping.

    Raises:
        ValidationError: If either state is unknown.
    """
    edges = table.get("edges")
    if not isinstance(edges, Mapping) or source not in edges or target not in edges:
        raise ValidationError("TRANSITION_STATE_UNKNOWN")
    if is_terminal_state(table, source):
        outcome, reason = "REJECTED_TERMINAL", "SOURCE_TERMINAL"
    else:
        ranks = table.get("ranks")
        if isinstance(ranks, Mapping) and int(ranks[target]) < int(ranks[source]):
            outcome, reason = "REGRESSED", "TARGET_RANK_LOWER"
        elif target not in edges[source]:
            outcome, reason = "REJECTED_UNDECLARED_EDGE", "EDGE_UNDECLARED"
        else:
            outcome, reason = "ACCEPTED", "EDGE_DECLARED"
    return {
        "contract_version": "v1",
        "schema_id": "utils.transition_result.v1",
        "outcome": outcome,
        "source_state": source,
        "target_state": target,
        "reason_code": reason,
    }
