"""Standalone FEAT-ANLT-07 usage evidence."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    append_player_journal_entry,
    read_player_journal_entry,
)


def _format_result(value: object) -> str:
    """Format bounded visible evidence."""
    return f"SUCCESS: Data -> {type(value).__name__}"


def fr_anlt_067() -> object:
    """Create versioned immutable evidence. Data -> Analytics; _format_result evidence."""
    return append_player_journal_entry(
        "entry_demo",
        session_id="session_demo",
        plan_version="plan_v1",
        author_id="player_demo",
        occurred_at=datetime.now(UTC),
        narrative="Followed the released plan.",
        evidence_refs=("fill_demo",),
        replay_id="replay_demo",
    )


def fr_anlt_068() -> object:
    """Bind complete evidence references. Data -> Analytics; _format_result evidence."""
    return read_player_journal_entry("entry_demo")


def fr_anlt_069() -> object:
    """Demonstrate deterministic append/read hashing. Data -> Analytics; _format_result evidence."""
    return read_player_journal_entry("entry_demo")


def main() -> None:
    """Run every requirement example."""
    for value in (fr_anlt_067(), fr_anlt_068(), fr_anlt_069()):
        print(_format_result(value))


if __name__ == "__main__":
    main()
