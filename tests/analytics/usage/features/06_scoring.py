"""Executable Analytics process-scoring usage example.

Demonstrates FEAT-ANLT-06 building deterministic process-first session scores,
critical-failure override, reproducibility hashes, comparative leaderboard
ranking, no-trade scoring, and the versioned JSON-safe contract transport.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    build_process_score_mapping,
    build_scoring_profile_mapping,
    build_session_score,
    compute_leaderboard_ranking,
    create_critical_failure_record,
    create_process_scoring_profile,
    parse_process_score_mapping,
    parse_scoring_profile_mapping,
)
from tests.analytics.usage._support import unwrap


def _format_result(obj: object) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


NOW = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)

_DIMENSIONS = (
    "preparation",
    "risk",
    "execution",
    "plan_adherence",
    "portfolio_management",
    "emergency",
    "discipline",
    "post_review",
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _weights() -> dict[str, float]:
    """Build the default normalized scoring weights."""
    return {
        "preparation": 0.2,
        "risk": 0.2,
        "execution": 0.1,
        "plan_adherence": 0.15,
        "portfolio_management": 0.1,
        "emergency": 0.1,
        "discipline": 0.1,
        "post_review": 0.05,
    }


def _scores(*, base: float = 0.75) -> dict[str, float]:
    """Build one canonical dimension-score set."""
    return dict.fromkeys(_DIMENSIONS, base)


def fr_anlt_061() -> None:
    """FR-ANLT-061: Create a versioned profile and transport it as v1 JSON."""
    _header("Profile Versioning - Create and Transport a Scoring Profile (FR-ANLT-061)")
    profile_response = create_process_scoring_profile("profile-v1", _weights())
    profile = unwrap(profile_response)
    print(_format_result(profile_response))
    mapping = unwrap(build_scoring_profile_mapping(profile))
    round_tripped = unwrap(parse_scoring_profile_mapping(mapping))
    print(
        f"Data -> profile_version={profile.profile_version}, "
        f"contract_version={mapping['contract_version']}, "
        f"round_trip_equal={round_tripped == profile}"
    )


def fr_anlt_062() -> None:
    """FR-ANLT-062: Create a bounded critical-failure observation record."""
    _header("Critical Failure Record - Create a Bounded Observation (FR-ANLT-062)")
    failure_response = create_critical_failure_record(
        "replay", "critical", "replay gap detected"
    )
    failure = unwrap(failure_response)
    print(_format_result(failure_response))
    print(
        f"Data -> kind={failure.kind}, severity={failure.severity}, detail={failure.detail}"
    )


def fr_anlt_063() -> None:
    """FR-ANLT-063: Score a session deterministically, including no-trade."""
    _header("Deterministic Session Scoring - Complete and No-Trade (FR-ANLT-063)")
    profile = unwrap(create_process_scoring_profile("profile-v1", _weights()))
    score_response = build_session_score(
        profile,
        _scores(),
        session_id="session-active",
        scored_at=NOW,
    )
    score = unwrap(score_response)
    print(_format_result(score_response))
    print(
        f"Data -> status={score.score_status}, weighted_total={score.weighted_total:.4f}, "
        f"leaderboard_eligible={score.leaderboard_eligible}"
    )
    stand_down = unwrap(
        build_session_score(
            profile,
            _scores(base=0.9),
            session_id="session-stand-down",
            scored_at=NOW,
            no_trade=True,
        )
    )
    print(
        f"Data -> no_trade={stand_down.no_trade}, status={stand_down.score_status}, "
        f"weighted_total={stand_down.weighted_total:.4f}"
    )


def fr_anlt_064() -> None:
    """FR-ANLT-064: Rank sessions comparatively with profit only secondary."""
    _header(
        "Comparative Ranking - Process Score Primary, Profit Secondary (FR-ANLT-064)"
    )
    profile = unwrap(create_process_scoring_profile("profile-v1", _weights()))
    low = unwrap(
        build_session_score(
            profile,
            _scores(base=0.5),
            session_id="session-low",
            scored_at=NOW,
        )
    )
    high = unwrap(
        build_session_score(
            profile,
            _scores(base=0.9),
            session_id="session-high",
            scored_at=NOW,
        )
    )
    ranks_response = compute_leaderboard_ranking(
        [low, high],
        profits={"session-low": "1000", "session-high": "10"},
    )
    ranks = unwrap(ranks_response)
    print(_format_result(ranks_response))
    for row in ranks:
        print(
            f"Data -> rank={row.rank}, session={row.session_id}, "
            f"process_score={row.process_score:.4f}, profit={row.profit}"
        )


def fr_anlt_065() -> None:
    """FR-ANLT-065: Transport one session score as a validated v1 mapping."""
    _header("Contract Transport - Build and Parse a Process Score (FR-ANLT-065)")
    profile = unwrap(create_process_scoring_profile("profile-v1", _weights()))
    score = unwrap(
        build_session_score(
            profile,
            _scores(),
            session_id="session-active",
            scored_at=NOW,
        )
    )
    mapping_response = build_process_score_mapping(score)
    mapping = unwrap(mapping_response)
    parsed = unwrap(parse_process_score_mapping(mapping))
    print(_format_result(mapping_response))
    print(
        f"Data -> schema_id={mapping['schema_id']}, round_trip_hash_equal="
        f"{parsed.reproducibility_hash == score.reproducibility_hash}"
    )


def fr_anlt_066() -> None:
    """FR-ANLT-066: Critical failures override scores regardless of P&L."""
    _header("Critical-Failure Override - Invalidate and Reproduce (FR-ANLT-066)")
    profile = unwrap(create_process_scoring_profile("profile-v1", _weights()))
    failure = unwrap(
        create_critical_failure_record("integrity", "critical", "checksum mismatch")
    )
    overridden_response = build_session_score(
        profile,
        _scores(),
        session_id="session-overridden",
        scored_at=NOW,
        critical_failures=(failure,),
    )
    overridden = unwrap(overridden_response)
    rebuilt = unwrap(
        build_session_score(
            profile,
            _scores(),
            session_id="session-overridden",
            scored_at=NOW,
            critical_failures=(failure,),
        )
    )
    print(_format_result(overridden_response))
    print(
        f"Data -> status={overridden.score_status}, weighted_total={overridden.weighted_total}, "
        f"reproducible={overridden.reproducibility_hash == rebuilt.reproducibility_hash}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    print(
        "\nFEATURE: FEAT-ANLT-06 — scoring/ — Process Scoring\n"
        "Purpose: Deterministic process-first scoring with critical-failure "
        "override, reproducibility, comparative ranking, and no-trade scoring.\n"
        "Module flow:\n"
        "-> Stage 1: Versioned profile creation and profile transport\n"
        "-> Stage 2: Critical-failure record creation\n"
        "-> Stage 3: Deterministic session scoring (complete and no-trade)\n"
        "-> Stage 4: Comparative leaderboard ranking\n"
        "-> Stage 5: Process-score v1 contract transport\n"
        "-> Stage 6: Critical-failure override and reproducibility"
    )
    fr_anlt_061()
    fr_anlt_062()
    fr_anlt_063()
    fr_anlt_064()
    fr_anlt_065()
    fr_anlt_066()


if __name__ == "__main__":
    main()
