"""Standalone Strategy Profiles and Expectancy References feature evidence."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_expectancy_reference,
    build_strategy_profile,
    ensure_strategy_storage,
    evaluate_expectancy_reference,
    list_strategy_profiles,
    parse_expectancy_reference,
    parse_strategy_profile,
    persist_strategy_profile,
)

_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _profile() -> dict[str, object]:
    return build_strategy_profile(
        strategy_id="trend",
        strategy_version="1.0.0",
        permitted_instruments=("EURUSD",),
        permitted_sessions=("LONDON",),
        permitted_regimes=("TREND",),
        indicator_dependencies=("ema-20",),
        entry_rules=("breakout",),
        exit_rules=("target",),
        invalidation_rules=("close-below",),
        automation_permissions=("SUPERVISED",),
    )


def _persist_demonstration() -> None:
    """Exercise production profile persistence and listing when statefully enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_strategy_profile(
        _profile(), request_id=_REQUEST, correlation_id=_CORRELATION
    )
    _emit("FEAT-STR-13 persistence", persisted["record_hash"])
    _emit("FEAT-STR-13 profile list", list_strategy_profiles(request_id=_REQUEST))


def fr_str_063() -> None:
    _emit("FR-STR-063", _profile())


def fr_str_064() -> None:
    _emit("FR-STR-064", parse_strategy_profile(_profile()))


def fr_str_065() -> None:
    _emit("FR-STR-065", _profile()["permitted_regimes"])


def fr_str_076() -> None:
    _emit(
        "FR-STR-076",
        build_expectancy_reference(
            profile_id="exp-1", exact_version="1", evidence_ref="ev-1"
        ),
    )


def fr_str_077() -> None:
    reference = build_expectancy_reference(
        profile_id="exp-1", exact_version="1", evidence_ref="ev-1"
    )
    _emit(
        "FR-STR-077",
        evaluate_expectancy_reference(parse_expectancy_reference(reference)),
    )


def main() -> None:
    """Run every Profiles and Expectancy References requirement example."""
    for number in (63, 64, 65, 76, 77):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
