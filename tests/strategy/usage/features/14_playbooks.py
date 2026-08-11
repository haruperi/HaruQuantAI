"""Standalone Strategy Playbooks feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_strategy_playbook,
    ensure_strategy_storage,
    list_strategy_playbooks,
    parse_strategy_playbook,
    persist_strategy_playbook,
)

_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _playbook() -> dict[str, object]:
    return build_strategy_playbook(
        playbook_id="play-1",
        strategy_profile_ref="trend@1.0.0",
        title="Trend breakout",
        summary="Closed-bar setup",
        setup_rules=("trend",),
        debrief_prompts=("Was entry valid?",),
    )


def _persist_demonstration() -> None:
    """Exercise production playbook persistence and listing when statefully enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_strategy_playbook(
        _playbook(), request_id=_REQUEST, correlation_id=_CORRELATION
    )
    _emit("FEAT-STR-14 persistence", persisted["record_hash"])
    _emit("FEAT-STR-14 playbook list", list_strategy_playbooks(request_id=_REQUEST))


def fr_str_066() -> None:
    _emit("FR-STR-066", _playbook())


def fr_str_067() -> None:
    _emit("FR-STR-067", parse_strategy_playbook(_playbook()))


def fr_str_068() -> None:
    _emit("FR-STR-068", _playbook()["setup_rules"])


def main() -> None:
    """Run every Strategy Playbooks requirement example."""
    for number in range(66, 69):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
