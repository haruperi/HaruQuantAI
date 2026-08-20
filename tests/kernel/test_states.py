"""Unit tests for component state transition engine.

Traces to: P5-T02, Gate G5
"""

from __future__ import annotations

import pytest
from app.kernel.errors import LifecycleError
from app.kernel.states import (
    _ALLOWED_TRANSITIONS,
    ComponentState,
    transition_component,
)


def test_self_transitions_are_always_permitted() -> None:
    """Verify that transitioning to the same state is always a valid no-op returning current state."""
    for state in ComponentState:
        assert transition_component(state, state) == state


def test_allowed_transitions_succeed() -> None:
    """Verify all defined allowed transitions succeed and return the target state."""
    for src, targets in _ALLOWED_TRANSITIONS.items():
        for dst in targets:
            assert transition_component(src, dst) == dst


def test_forbidden_transitions_raise_lifecycle_error() -> None:
    """Verify Cartesian product of all forbidden transitions raises LifecycleError with exact message."""
    for src in ComponentState:
        allowed = _ALLOWED_TRANSITIONS.get(src, frozenset())
        for dst in ComponentState:
            if src == dst or dst in allowed:
                continue
            with pytest.raises(
                LifecycleError, match=f"invalid component transition: {src} -> {dst}"
            ):
                transition_component(src, dst)


def test_quarantined_state_is_terminal() -> None:
    """Verify QUARANTINED state has zero outward transitions except to itself."""
    assert _ALLOWED_TRANSITIONS[ComponentState.QUARANTINED] == frozenset()
    for target in ComponentState:
        if target == ComponentState.QUARANTINED:
            assert transition_component(ComponentState.QUARANTINED, target) == target
        else:
            with pytest.raises(LifecycleError):
                transition_component(ComponentState.QUARANTINED, target)
