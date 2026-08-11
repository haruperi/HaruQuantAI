"""Standalone Strategy Lifecycle Governance feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    ensure_strategy_storage,
    govern_strategy_lifecycle,
    list_lifecycle,
    persist_lifecycle_decision,
)

_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _decision() -> dict[str, object]:
    return govern_strategy_lifecycle(
        strategy_id="trend",
        strategy_version="1.0.0",
        current_status="TESTING",
        target_status="APPROVED",
        reason="tests passed",
    )


def _persist_demonstration() -> None:
    """Exercise production lifecycle persistence and listing when enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_lifecycle_decision(
        _decision(), request_id=_REQUEST, correlation_id=_CORRELATION
    )
    _emit("FEAT-STR-19 persistence", persisted["decision"])
    _emit("FEAT-STR-19 lifecycle list", list_lifecycle(request_id=_REQUEST))


def fr_str_080() -> None:
    _emit(
        "FR-STR-080",
        govern_strategy_lifecycle(
            strategy_id="trend",
            strategy_version="1.0.0",
            current_status="DRAFT",
            target_status="TESTING",
            reason="begin tests",
        ),
    )


def fr_str_081() -> None:
    _emit("FR-STR-081", _decision())


def fr_str_082() -> None:
    _emit(
        "FR-STR-082",
        govern_strategy_lifecycle(
            strategy_id="trend",
            strategy_version="1.0.0",
            current_status="APPROVED",
            target_status="RETIRED",
            reason="retire",
        ),
    )


def main() -> None:
    """Run every Strategy Lifecycle Governance requirement example."""
    for number in range(80, 83):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
