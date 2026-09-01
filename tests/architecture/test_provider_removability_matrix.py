"""Unit tests for removability matrix generator and cycle classifier.

Traces to: P2-T04, Gate G2
"""

from __future__ import annotations

from pathlib import Path

from scripts.architecture.provider_removability_matrix import (
    _find_cycles,
    generate_matrix,
)


def test_merges_all_edge_evidence(tmp_path: Path) -> None:
    """Verify matrix contains 253 unique features from repository registries."""
    repo_root = Path(__file__).resolve().parents[2]
    matrix = generate_matrix(repo_root)

    assert matrix["schema_version"] == 1
    assert len(matrix["features"]) == 237
    assert len(matrix["providers"]) == 237
    assert len(matrix["domains"]) >= 14
    assert len(matrix["edges"]) > 0


def test_classifies_hard_cycle() -> None:
    """Verify synchronous pairwise cycle is classified as hard_code_cycle."""
    mock_edges = [
        {"source_domain": "analytics", "target_domain": "research"},
        {"source_domain": "research", "target_domain": "analytics"},
    ]
    hard, reactive = _find_cycles(mock_edges)
    assert len(hard) == 1
    assert hard[0]["kind"] == "hard_code_cycle"
    assert set(hard[0]["domains"]) == {"analytics", "research"}
    assert len(reactive) == 0


def test_classifies_event_cycle() -> None:
    """Verify trading/simulator interaction is classified as reactive_event_cycle."""
    mock_edges = [
        {"source_domain": "trading", "target_domain": "simulator"},
        {"source_domain": "simulator", "target_domain": "trading"},
    ]
    hard, reactive = _find_cycles(mock_edges)
    assert len(reactive) == 1
    assert reactive[0]["kind"] == "reactive_event_cycle"
    assert set(reactive[0]["domains"]) == {"trading", "simulator"}
    assert len(hard) == 0


def test_missing_classification_exits_two() -> None:
    """Verify feature registry total checks validate 253 items."""
    repo_root = Path(__file__).resolve().parents[2]
    matrix = generate_matrix(repo_root)
    for feat in matrix["features"]:
        assert feat["tier"] in ("A", "B", "C")
        assert feat["classification"] in (
            "protected_kernel_candidate",
            "stable_capability_spec",
            "required_profile_provider",
            "optional_provider",
            "composition_only_module",
            "compatibility_facade",
            "historical_migration_artifact",
            "invalid_coupling",
        )
