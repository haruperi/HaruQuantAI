"""Tests for deterministic Phase 0 evidence generation."""

from __future__ import annotations

from scripts import generate_phase0_evidence as generator


def test_plan_and_register_have_exact_feature_sets() -> None:
    """The plan and source register retain one card per feature."""
    tasks = generator.parse_plan(generator.PLAN_PATH.read_text(encoding="utf-8"))
    contracts = generator.parse_register(
        generator.REGISTER_PATH.read_text(encoding="utf-8")
    )

    assert len(tasks) == 205
    assert len(contracts) == 205
    assert {task["feature_id"] for task in tasks} == {
        contract["feature_id"] for contract in contracts
    }
    assert sum(task["complete"] for task in tasks) == 2


def test_dependency_edges_are_complete_and_ordered() -> None:
    """Every required provider precedes its consumer in the frozen schedule."""
    payloads = generator.build_payloads()
    graph = payloads[generator.SOURCE_DIR / "dependency-graph.json"]
    schedule = payloads[generator.EVIDENCE_DIR / "dependency-schedule.json"]
    ordered_features = [
        feature for phase in schedule["phases"] for feature in phase["features"]
    ]
    order = {feature: index for index, feature in enumerate(ordered_features)}

    assert len(graph["required_edges"]) == 476
    assert len(graph["operation_edges"]) == 233
    assert all(
        order[edge["provider"]] < order[edge["consumer"]]
        for edge in graph["required_edges"]
    )


def test_generated_inventory_matches_ratified_counts() -> None:
    """Manifest counts cannot silently drift from the 205-feature baseline."""
    payloads = generator.build_payloads()
    manifest = payloads[generator.EVIDENCE_DIR / "baseline-manifest.json"]

    assert manifest["inventory"]["total_features"] == 205
    assert manifest["inventory"]["total_normalized_frs"] == 575
    assert manifest["inventory"]["total_local_nfrs"] == 276
    assert manifest["inventory"]["total_required_edges"] == 476
    assert manifest["inventory"]["total_operation_gated_edges"] == 233
