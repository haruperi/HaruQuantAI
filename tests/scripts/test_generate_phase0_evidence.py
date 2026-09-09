"""Tests for deterministic Phase 0 evidence generation."""

from __future__ import annotations

import copy
import json
import sys
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
    """Required edges are forward except the ratified accepted-provider edge."""
    payloads = generator.build_payloads()
    graph = payloads[generator.SOURCE_DIR / "dependency-graph.json"]
    schedule = payloads[generator.EVIDENCE_DIR / "dependency-schedule.json"]
    ordered_features = [
        feature for phase in schedule["phases"] for feature in phase["features"]
    ]
    order = {feature: index for index, feature in enumerate(ordered_features)}

    assert len(graph["required_edges"]) == 477
    assert len(graph["operation_edges"]) == 233
    backward_edges = [
        edge
        for edge in graph["required_edges"]
        if order[edge["provider"]] >= order[edge["consumer"]]
    ]
    assert backward_edges == [
        {
            "provider": "FEAT-WS-EXECUTE_PERSISTENCE",
            "provider_task": "1.09",
            "provider_capability": "workspace.persistence@1",
            "consumer": "FEAT-WS-MANAGE_ACCOUNTS",
            "consumer_task": "1.04",
        }
    ]


def test_generated_inventory_matches_ratified_counts() -> None:
    """Manifest counts cannot silently drift from the 205-feature baseline."""
    payloads = generator.build_payloads()
    manifest = payloads[generator.EVIDENCE_DIR / "baseline-manifest.json"]

    assert manifest["inventory"]["total_features"] == 205
    assert manifest["inventory"]["total_normalized_frs"] == 575
    assert manifest["inventory"]["total_local_nfrs"] == 276
    assert manifest["inventory"]["total_required_edges"] == 477
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
        if feature["feature_id"] == "FEAT-UI-COMPOSE_WORKSPACE"
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


def test_generated_output_inventory_matches_build_payloads() -> None:
    """Published output discovery is complete, ordered, and normalized."""
    inventory = generator.generated_output_paths()

    assert inventory == tuple(
        generator.REPO / path for path in generator.GENERATED_OUTPUT_PATHS
    )
    assert set(inventory) == set(generator.build_payloads())
    assert all("\\" not in path for path in generator.GENERATED_OUTPUT_PATHS)
    assert len(inventory) == 11


def test_list_outputs_does_not_build_or_write(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Output discovery is usable before generation and has no side effects."""
    monkeypatch.setattr(
        generator,
        "build_payloads",
        lambda: pytest.fail("--list-outputs must not build payloads"),
    )
    monkeypatch.setattr(sys, "argv", ["generate_phase0_evidence.py", "--list-outputs"])

    assert generator.main() == 0
    assert capsys.readouterr().out.splitlines() == list(
        generator.GENERATED_OUTPUT_PATHS
    )


def test_write_mode_preserves_pinned_phase0_snapshots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Live regeneration never overwrites historical Phase-0 source bytes."""
    pinned_relative = next(iter(generator.PINNED_OUTPUT_PATHS))
    pinned = tmp_path / pinned_relative
    current_relative = "docs/dev/evidence/feature-baseline.json"
    current = tmp_path / current_relative
    pinned.parent.mkdir(parents=True)
    pinned.write_text('{"historical": true}\n', encoding="utf-8")
    payloads = {
        pinned: {"invented": "replacement"},
        current: {"current": True},
    }
    monkeypatch.setattr(generator, "REPO", tmp_path)
    monkeypatch.setattr(generator, "build_payloads", lambda: payloads)
    monkeypatch.setattr(generator, "generated_output_paths", lambda: tuple(payloads))
    monkeypatch.setattr(sys, "argv", ["generate_phase0_evidence.py", "--write"])

    assert generator.main() == 0
    assert pinned.read_text(encoding="utf-8") == '{"historical": true}\n'
    assert json.loads(current.read_text(encoding="utf-8")) == {"current": True}
