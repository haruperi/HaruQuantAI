"""Unit tests for the Analytics process-scoring feature (FEAT-ANLT-06)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
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

_NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)


def _weights() -> dict[str, float]:
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


def _scores() -> dict[str, float]:
    return dict.fromkeys(_weights(), 0.8)


def _profile() -> object:
    return unwrap(create_process_scoring_profile("profile-v1", _weights()))


def _score(
    *, critical_failures: tuple[object, ...] = (), no_trade: bool = False
) -> object:
    return unwrap(
        build_session_score(
            _profile(),
            _scores(),
            session_id="session-a",
            scored_at=_NOW,
            critical_failures=critical_failures,
            no_trade=no_trade,
        )
    )


def test_profile_creation_is_deterministic() -> None:
    assert unwrap(create_process_scoring_profile("p1", _weights())) == unwrap(
        create_process_scoring_profile("p1", _weights())
    )


def test_profile_rejects_missing_dimension() -> None:
    weights = _weights()
    del weights["risk"]
    response = create_process_scoring_profile("p1", weights)
    assert response.status == "error"
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"


def test_profile_rejects_non_normalized_weights() -> None:
    weights = _weights()
    weights["risk"] = 0.5
    response = create_process_scoring_profile("p1", weights)
    assert response.status == "error"


def test_profile_rejects_invalid_policy_and_cap() -> None:
    response = create_process_scoring_profile(
        "p1", _weights(), critical_failure_policy="ignore"
    )
    assert response.status == "error"
    response = create_process_scoring_profile(
        "p1", _weights(), critical_failure_cap=2.0
    )
    assert response.status == "error"


def test_profile_requires_trimmed_version() -> None:
    response = create_process_scoring_profile(" ", _weights())
    assert response.status == "error"


def test_critical_failure_record_requires_known_kind_and_severity() -> None:
    assert create_critical_failure_record("other", "critical", "gap").status == "error"
    assert create_critical_failure_record("replay", "fatal", "gap").status == "error"


def test_critical_failure_record_requires_detail() -> None:
    response = create_critical_failure_record("safety", "error", "  ")
    assert response.status == "error"


def test_complete_score_weighted_total() -> None:
    score = _score()
    assert score.score_status == "complete"
    assert score.weighted_total == pytest.approx(0.8)
    assert score.leaderboard_eligible is True
    assert score.non_binding is True


def test_no_trade_session_scores_competence() -> None:
    score = _score(no_trade=True)
    assert score.no_trade is True
    assert score.score_status == "complete"
    assert score.weighted_total == pytest.approx(0.8)


def test_critical_failure_invalidates_score() -> None:
    failure = unwrap(create_critical_failure_record("replay", "critical", "replay gap"))
    score = _score(critical_failures=(failure,))
    assert score.score_status == "invalidated"
    assert score.weighted_total is None
    assert score.leaderboard_eligible is False


def test_critical_failure_cap_policy_bounds_total() -> None:
    profile = unwrap(
        create_process_scoring_profile(
            "p1", _weights(), critical_failure_policy="cap", critical_failure_cap=0.25
        )
    )
    failure = unwrap(
        create_critical_failure_record("integrity", "critical", "checksum mismatch")
    )
    score = unwrap(
        build_session_score(
            profile,
            _scores(),
            session_id="session-c",
            scored_at=_NOW,
            critical_failures=(failure,),
        )
    )
    assert score.score_status == "complete"
    assert score.weighted_total == pytest.approx(0.25)


def test_non_critical_failure_does_not_override() -> None:
    failure = unwrap(
        create_critical_failure_record("safety", "warning", "minor deviation")
    )
    score = _score(critical_failures=(failure,))
    assert score.score_status == "complete"
    assert score.weighted_total == pytest.approx(0.8)


def test_reproducibility_hash_is_deterministic() -> None:
    assert _score().reproducibility_hash == _score().reproducibility_hash
    assert len(_score().reproducibility_hash) == 64


def test_missing_dimension_fails_closed() -> None:
    scores = _scores()
    del scores["execution"]
    response = build_session_score(
        _profile(), scores, session_id="session-d", scored_at=_NOW
    )
    assert response.status == "error"


def test_non_utc_scored_at_rejected() -> None:
    response = build_session_score(
        _profile(),
        _scores(),
        session_id="session-e",
        scored_at=datetime.fromisoformat("2026-07-01T12:00:00"),
    )
    assert response.status == "error"


def test_eligible_scores_rank_above_invalidated() -> None:
    eligible = _score()
    failure = unwrap(create_critical_failure_record("replay", "critical", "replay gap"))
    invalidated = _score(critical_failures=(failure,))
    ranks = unwrap(compute_leaderboard_ranking([invalidated, eligible]))
    assert [row.session_id for row in ranks] == [
        eligible.session_id,
        invalidated.session_id,
    ]
    assert ranks[0].rank == 1
    assert ranks[1].eligible is False


def test_profit_is_secondary_to_process_score() -> None:
    low_score = _score()
    high_score = unwrap(
        build_session_score(
            _profile(),
            dict.fromkeys(_weights(), 0.95),
            session_id="session-high",
            scored_at=_NOW,
        )
    )
    ranks = unwrap(
        compute_leaderboard_ranking(
            [low_score, high_score],
            profits={"session-high": "5", "session-a": "999"},
        )
    )
    assert ranks[0].session_id == high_score.session_id


def test_limit_caps_ranked_rows() -> None:
    ranks = unwrap(compute_leaderboard_ranking([_score() for _ in range(3)], limit=2))
    assert len(ranks) == 2
    assert [row.rank for row in ranks] == [1, 2]


def test_invalid_profit_fails_closed() -> None:
    response = compute_leaderboard_ranking(
        [_score()], profits={"session-a": "not-a-number"}
    )
    assert response.status == "error"


def test_invalid_limit_fails_closed() -> None:
    response = compute_leaderboard_ranking([_score()], limit=0)
    assert response.status == "error"


def test_process_score_mapping_round_trip() -> None:
    original = _score()
    mapping = unwrap(build_process_score_mapping(original))
    assert mapping["contract_version"] == "v1"
    assert mapping["schema_id"] == "analytics.process_score.v1"
    parsed = unwrap(parse_process_score_mapping(mapping))
    assert parsed.reproducibility_hash == original.reproducibility_hash
    assert parsed.weighted_total == original.weighted_total


def test_process_score_mapping_rejects_unknown_version() -> None:
    mapping = dict(unwrap(build_process_score_mapping(_score())))
    mapping["contract_version"] = "v2"
    assert parse_process_score_mapping(mapping).status == "error"


def test_process_score_mapping_rejects_invalid_timestamp() -> None:
    mapping = dict(unwrap(build_process_score_mapping(_score())))
    mapping["scored_at"] = "not-a-timestamp"
    assert parse_process_score_mapping(mapping).status == "error"


def test_profile_mapping_round_trip() -> None:
    profile = unwrap(create_process_scoring_profile("p1", _weights()))
    mapping = unwrap(build_scoring_profile_mapping(profile))
    assert mapping["schema_id"] == "analytics.scoring_profile.v1"
    assert unwrap(parse_scoring_profile_mapping(mapping)) == profile


def test_profile_mapping_rejects_unknown_version() -> None:
    mapping = dict(unwrap(build_scoring_profile_mapping(_profile())))
    mapping["contract_version"] = "v9"
    assert parse_scoring_profile_mapping(mapping).status == "error"
