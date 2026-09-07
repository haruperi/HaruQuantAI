"""Tests for deterministic Phase 0 evidence generation."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

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
    assert sum(task["complete"] for task in tasks) >= 2


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
    assert manifest["baseline"]["plan_git_blob"] == (
        "a6a8754170c5ff1a0ba853f8b3d91f43a68aa2a3"
    )
    assert manifest["baseline"]["plan_sha256"] == (
        "421120edda333378eed98f39e9e0a8c0870f50308cd5b96828175be33bbb328f"
    )
    assert manifest["baseline"]["legacy_unattested_plan_sha256"] == (
        generator.LEGACY_UNATTESTED_PLAN_SHA256
    )
    assert manifest["status_distribution"]["COMPLETE"] == 2


def test_live_completion_does_not_mutate_baseline_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutable tracker progress cannot rewrite immutable baseline statistics."""
    baseline_bytes = generator._git_bytes(
        "show",
        (
            f"{generator.BASELINE_HEAD}:"
            f"{generator.PLAN_PATH.relative_to(generator.REPO).as_posix()}"
        ),
    )
    baseline_tasks = generator.parse_plan(baseline_bytes.decode("utf-8"))
    live_tasks = copy.deepcopy(baseline_tasks)
    changed = next(task for task in live_tasks if not task["complete"])
    changed["complete"] = True
    changed["status"] = "COMPLETE"
    parsed = iter((live_tasks, baseline_tasks))
    monkeypatch.setattr(generator, "parse_plan", lambda _text: next(parsed))

    payloads = generator.build_payloads()
    manifest = payloads[generator.EVIDENCE_DIR / "baseline-manifest.json"]
    current = payloads[generator.EVIDENCE_DIR / "feature-baseline.json"]

    assert manifest["status_distribution"]["COMPLETE"] == 2
    assert (
        next(
            feature
            for feature in current["features"]
            if feature["feature_id"] == changed["feature_id"]
        )["status"]
        == "COMPLETE"
    )


def test_live_entry_points_do_not_mutate_baseline_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live registration changes affect current projection, not baseline counts."""
    live_pyproject = b"""
[project.entry-points."haruquantai.features"]
workspace_probe = "app.ui.src.widgets.workspaces:feature"
"""
    original_read_bytes = Path.read_bytes

    def read_bytes(path: Path) -> bytes:
        if path == generator.REPO / "pyproject.toml":
            return live_pyproject
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)

    payloads = generator.build_payloads()
    manifest = payloads[generator.EVIDENCE_DIR / "baseline-manifest.json"]
    current = payloads[generator.EVIDENCE_DIR / "feature-baseline.json"]
    workspace = next(
        feature
        for feature in current["features"]
        if feature["feature_id"] == "FEAT-UI-01"
    )

    assert manifest["inventory"]["registered_entry_points"] == 41
    assert workspace["entry_point_registered"] is True


def test_plan_parser_accepts_commit_and_closeout_receipt_references() -> None:
    """Accepted evidence supports historical SHAs and future close-out receipts."""
    plan = generator._git_bytes(
        "show",
        (
            f"{generator.BASELINE_HEAD}:"
            f"{generator.PLAN_PATH.relative_to(generator.REPO).as_posix()}"
        ),
    ).decode("utf-8")
    receipt_plan = plan.replace(
        "**Accepted commit:** Not recorded — this is a plan.",
        "**Accepted commit:** `task-closeout:run-1.01`.",
        1,
    )

    assert generator.parse_plan(receipt_plan)[0]["accepted_commit"] == (
        "task-closeout:run-1.01"
    )
    assert generator.ACCEPTANCE_REF_RE.fullmatch("a" * 40)
