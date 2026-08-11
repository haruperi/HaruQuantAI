"""Standalone Setup Evaluation feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_setup_evaluation,
    ensure_strategy_storage,
    list_setup_evaluations,
    parse_setup_evaluation,
    persist_setup_evaluation,
)

_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _evaluation() -> dict[str, object]:
    return build_setup_evaluation(
        evaluation_id="eval-1",
        playbook_ref="play-1",
        outcome="MATCH",
        source_snapshot_refs=("snapshot-1",),
    )


def _persist_demonstration() -> None:
    """Exercise production setup-evaluation persistence and listing when enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_setup_evaluation(
        _evaluation(), request_id=_REQUEST, correlation_id=_CORRELATION
    )
    _emit("FEAT-STR-15 persistence", persisted["record_hash"])
    _emit(
        "FEAT-STR-15 setup evaluation list",
        list_setup_evaluations(request_id=_REQUEST),
    )


def fr_str_069() -> None:
    _emit("FR-STR-069", _evaluation())


def fr_str_070() -> None:
    _emit("FR-STR-070", parse_setup_evaluation(_evaluation()))


def fr_str_071() -> None:
    _emit(
        "FR-STR-071",
        build_setup_evaluation(
            evaluation_id="eval-2",
            playbook_ref="play-1",
            outcome="STALE",
            source_snapshot_refs=("snapshot-1",),
            reason_codes=("STALE",),
        ),
    )


def main() -> None:
    """Run every Setup Evaluation requirement example."""
    for number in range(69, 72):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
