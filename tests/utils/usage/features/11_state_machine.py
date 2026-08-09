"""Standalone usage evidence for FEAT-UTIL-10."""

from datetime import UTC, datetime

from app.utils import (
    attempt_transition,
    build_transition_record,
    build_transition_table,
    is_terminal_state,
)


def main() -> None:
    """Run generic state transition evaluation."""
    table = build_transition_table(
        {"OPEN": ["CLOSED"], "CLOSED": []}, terminal_states=["CLOSED"]
    )
    result = attempt_transition(table, "OPEN", "CLOSED")
    assert is_terminal_state(table, "CLOSED")
    record = build_transition_record(
        entity_id="demo",
        source_state="OPEN",
        target_state="CLOSED",
        outcome="ACCEPTED",
        reason_code="USAGE.COMPLETE",
        actor_ref="usage",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        sequence=1,
    )
    assert record["target_state"] == "CLOSED"
    print("SUCCESS: FEAT-UTIL-10 state machine completed")
    print(f"Data -> transition={result}")


if __name__ == "__main__":
    main()
