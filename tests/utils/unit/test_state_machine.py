"""Unit tests for generic transition primitives."""

from app.utils import attempt_transition, build_transition_table


def test_transition_outcomes_are_pure_and_fail_closed() -> None:
    table = build_transition_table(
        {"OPEN": ["CLOSED"], "CLOSED": []},
        terminal_states=["CLOSED"],
        ranks={"OPEN": 0, "CLOSED": 1},
    )
    assert attempt_transition(table, "OPEN", "CLOSED")["outcome"] == "ACCEPTED"
    assert attempt_transition(table, "CLOSED", "OPEN")["outcome"] == "REJECTED_TERMINAL"
