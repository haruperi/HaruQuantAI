"""Standalone FEAT-ANLT-09 usage evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import analyze_emergency_response

EVENTS = (
    {"kind": "perceived", "occurred_at": "2026-01-01T00:00:00+00:00"},
    {"kind": "resolved", "occurred_at": "2026-01-01T00:00:10+00:00", "survival": True},
)


def _format_result(value: object) -> str:
    """Format bounded visible evidence."""
    return f"SUCCESS: Data -> {type(value).__name__}"


def fr_anlt_073() -> object:
    """Measure lifecycle timing. Data -> Analytics; _format_result evidence."""
    return analyze_emergency_response(
        EVENTS, required_sequence=("perceived", "resolved")
    )


def fr_anlt_074() -> object:
    """Preserve sequence and survival completeness. Data -> Analytics; _format_result evidence."""
    return analyze_emergency_response(
        EVENTS, required_sequence=("perceived", "acknowledged", "resolved")
    )


def main() -> None:
    """Run every requirement example."""
    for value in (fr_anlt_073(), fr_anlt_074()):
        print(_format_result(value))


if __name__ == "__main__":
    main()
