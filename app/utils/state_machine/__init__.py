"""Function-only exports for generic state-machine primitives."""

from app.utils.state_machine.audit import build_transition_record
from app.utils.state_machine.transitions import (
    attempt_transition,
    build_transition_table,
    is_terminal_state,
)

__all__ = [
    "attempt_transition",
    "build_transition_record",
    "build_transition_table",
    "is_terminal_state",
]
