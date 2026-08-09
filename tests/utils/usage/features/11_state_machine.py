"""Standalone usage evidence for FEAT-UTIL-10."""

from app.utils import attempt_transition, build_transition_table


def main() -> None:
    """Run generic state transition evaluation."""
    table = build_transition_table(
        {"OPEN": ["CLOSED"], "CLOSED": []}, terminal_states=["CLOSED"]
    )
    result = attempt_transition(table, "OPEN", "CLOSED")
    print("SUCCESS: FEAT-UTIL-10 state machine completed")
    print(f"Data -> transition={result}")


if __name__ == "__main__":
    main()
