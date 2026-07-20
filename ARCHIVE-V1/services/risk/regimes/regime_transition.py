"""Transition helpers for regime state changes."""

from __future__ import annotations

from .models import RegimeState, RegimeTransition


def build_regime_transition(
    previous: RegimeState | None,
    current: RegimeState,
) -> RegimeTransition:
    """Build simple transition metadata from previous to current regime."""
    previous_name = None if previous is None else previous.name
    return RegimeTransition(
        changed=previous_name != current.name,
        previous_name=previous_name,
        current_name=current.name,
    )
