"""Tests for the OptimizationStudy v1 contract (TC-IMP-OPT-01)."""

from decimal import Decimal

import pytest
from app.services.optimization import (
    build_optimization_study,
    get_optimization_study_contract_version,
    get_optimization_study_schema_id,
    parse_optimization_study,
)

_HASH = "a" * 64
_VALID_FIELDS: dict[str, object] = {
    "study_id": "study-00000000-0000-4000-8000-000000000000",
    "strategy_ref": "strategy-v1",
    "market_data_ref": "data-ref-1",
    "dataset_id": "dataset-abc",
    "dataset_hash": _HASH,
    "replay_identity": "replay-xyz",
    "objective_hash": _HASH,
    "space_hash": _HASH,
    "max_candidates": 100,
    "max_runtime_seconds": Decimal(3600),
    "max_monte_carlo_simulations": 500,
    "request_id": "req-1",
    "correlation_id": "cor-1",
    "created_at": "2026-08-08T12:00:00+00:00",
}


def test_build_and_parse_round_trip() -> None:
    """build then parse returns the same canonical mapping."""
    built = build_optimization_study(**_VALID_FIELDS)  # type: ignore[arg-type]
    assert built["contract_version"] == "v1"
    assert built["schema_id"] == "optimization.study.v1"
    parsed = parse_optimization_study(built)
    assert parsed == built


def test_contract_version_and_schema_accessors() -> None:
    """Version and schema accessors return canonical strings."""
    assert get_optimization_study_contract_version() == "v1"
    assert get_optimization_study_schema_id() == "optimization.study.v1"


def test_parse_rejects_wrong_version() -> None:
    """Incompatible version is rejected."""
    mapping = dict(_VALID_FIELDS)
    mapping["contract_version"] = "v2"
    with pytest.raises(ValueError, match="contract version"):
        parse_optimization_study(mapping)


def test_parse_rejects_wrong_schema_id() -> None:
    """Incompatible schema id is rejected."""
    built = build_optimization_study(**_VALID_FIELDS)  # type: ignore[arg-type]
    built["schema_id"] = "optimization.study.v2"
    with pytest.raises(ValueError, match="schema id"):
        parse_optimization_study(built)


def test_build_rejects_blank_study_id() -> None:
    """Blank study identity is rejected."""
    fields = dict(_VALID_FIELDS)
    fields["study_id"] = "  "
    with pytest.raises(ValueError, match="text fields"):
        build_optimization_study(**fields)  # type: ignore[arg-type]


def test_build_rejects_malformed_hash() -> None:
    """Malformed provenance hashes are rejected."""
    fields = dict(_VALID_FIELDS)
    fields["dataset_hash"] = "short"
    with pytest.raises(ValueError, match="SHA-256"):
        build_optimization_study(**fields)  # type: ignore[arg-type]


def test_build_rejects_nonpositive_budget() -> None:
    """Non-positive budget caps are rejected."""
    fields = dict(_VALID_FIELDS)
    fields["max_candidates"] = 0
    with pytest.raises(ValueError, match="max_candidates"):
        build_optimization_study(**fields)  # type: ignore[arg-type]


def test_build_rejects_colliding_dataset_and_replay_identity() -> None:
    """dataset_id and replay_identity must be distinct (anti-leakage)."""
    fields = dict(_VALID_FIELDS)
    fields["replay_identity"] = fields["dataset_id"]
    with pytest.raises(ValueError, match="distinct"):
        build_optimization_study(**fields)  # type: ignore[arg-type]


def test_build_rejects_nonpositive_monte_carlo_cap() -> None:
    """Non-positive Monte Carlo cap is rejected."""
    fields = dict(_VALID_FIELDS)
    fields["max_monte_carlo_simulations"] = -1
    with pytest.raises(ValueError, match="max_monte_carlo"):
        build_optimization_study(**fields)  # type: ignore[arg-type]
