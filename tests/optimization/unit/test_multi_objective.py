"""Tests for multi-objective candidate evaluation (TC-IMP-OPT-07)."""

import pytest
from app.services.optimization import (
    build_multi_objective_mapping,
    evaluate_multi_objective_candidate,
    get_multi_objective_contract_version,
    get_multi_objective_schema_id,
    parse_multi_objective_mapping,
)

_HASH = "a" * 64
_WEIGHTS: dict[str, float] = {
    "preparation": 0.2,
    "risk": 0.2,
    "execution": 0.2,
    "plan_adherence": 0.1,
    "discipline": 0.1,
    "post_review": 0.2,
}


def _process_score(**overrides: object) -> dict[str, object]:
    """Build a minimal analytics.process_score.v1 mapping."""
    payload: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "analytics.process_score.v1",
        "session_id": "session-1",
        "profile_version": "profile-1",
        "dimension_scores": {
            "preparation": 0.8,
            "risk": 0.9,
            "execution": 0.7,
            "plan_adherence": 0.6,
            "portfolio_management": 0.5,
            "emergency": 1.0,
            "discipline": 0.8,
            "post_review": 0.7,
        },
        "weighted_total": 0.78,
        "score_status": "complete",
        "critical_failures": [],
        "no_trade": False,
        "leaderboard_eligible": True,
        "reproducibility_hash": "b" * 64,
        "scored_at": "2026-08-08T12:00:00+00:00",
        "non_binding": True,
    }
    payload.update(overrides)
    return payload


def test_evaluate_returns_composite_mapping() -> None:
    """Evaluation produces a valid multi-objective composite mapping."""
    result = evaluate_multi_objective_candidate(
        candidate_hash=_HASH,
        core_objective="sharpe_ratio",
        core_objective_value=0.8,
        dimension_weights=_WEIGHTS,
        process_score_mapping=_process_score(),
    )
    assert result["contract_version"] == "v1"
    assert result["schema_id"] == "optimization.multi_objective_evaluation.v1"
    assert result["profit_sole_driver"] is False
    assert 0.0 <= result["composite_score"] <= 1.0


def test_build_and_parse_round_trip() -> None:
    """build then parse returns the same canonical mapping."""
    built = build_multi_objective_mapping(
        candidate_hash=_HASH,
        core_objective="sharpe_ratio",
        core_objective_value=0.5,
        dimension_weights=_WEIGHTS,
        process_score_mapping=_process_score(),
    )
    parsed = parse_multi_objective_mapping(built)
    assert parsed == built


def test_critical_failure_overrides_to_zero() -> None:
    """A critical failure caps the composite to zero regardless of performance."""
    result = evaluate_multi_objective_candidate(
        candidate_hash=_HASH,
        core_objective="sharpe_ratio",
        core_objective_value=1.0,
        dimension_weights=_WEIGHTS,
        process_score_mapping=_process_score(
            critical_failures=[
                {"kind": "safety", "severity": "critical", "detail": "breach"}
            ]
        ),
    )
    assert result["composite_score"] == 0.0
    assert result["overridden_by_critical_failure"] is True


def test_missing_core_objective_adds_caveat() -> None:
    """Unavailable core objective is caveated, not fabricated."""
    result = evaluate_multi_objective_candidate(
        candidate_hash=_HASH,
        core_objective="sharpe_ratio",
        core_objective_value=None,
        dimension_weights=_WEIGHTS,
        process_score_mapping=_process_score(),
    )
    assert "core_objective_unavailable" in result["caveats"]


def test_parse_rejects_wrong_version() -> None:
    """Incompatible version is rejected."""
    mapping = build_multi_objective_mapping(
        candidate_hash=_HASH,
        core_objective="sharpe_ratio",
        core_objective_value=0.5,
        dimension_weights=_WEIGHTS,
        process_score_mapping=_process_score(),
    )
    mapping["contract_version"] = "v2"
    with pytest.raises(ValueError, match="contract version"):
        parse_multi_objective_mapping(mapping)


def test_rejects_empty_dimension_weights() -> None:
    """Empty dimension weights are rejected."""
    with pytest.raises((ValueError, TypeError)):
        evaluate_multi_objective_candidate(
            candidate_hash=_HASH,
            core_objective="sharpe_ratio",
            core_objective_value=0.5,
            dimension_weights={},
            process_score_mapping=_process_score(),
        )


def test_contract_version_and_schema_accessors() -> None:
    """Accessors return canonical strings."""
    assert get_multi_objective_contract_version() == "v1"
    assert (
        get_multi_objective_schema_id() == "optimization.multi_objective_evaluation.v1"
    )


def test_rejects_process_score_without_dimensions() -> None:
    """Process score missing dimension_scores is rejected."""
    bad_score = _process_score()
    bad_score["dimension_scores"] = {}
    with pytest.raises(ValueError, match="dimension_scores"):
        evaluate_multi_objective_candidate(
            candidate_hash=_HASH,
            core_objective="sharpe_ratio",
            core_objective_value=0.5,
            dimension_weights=_WEIGHTS,
            process_score_mapping=bad_score,
        )
