"""Tests for deterministic compact Task packets and risk tiers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "task_packet.py"
SPEC = importlib.util.spec_from_file_location("hq_task_packet", MODULE_PATH)
assert SPEC
assert SPEC.loader
packet_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = packet_module
SPEC.loader.exec_module(packet_module)


def _task() -> dict[str, str]:
    return {
        "task_kind": "feature",
        "task_id": "FEAT-ORCH-MANAGE_JOBS",
        "task_slug": "manage-jobs",
        "task_name": "Manage jobs",
        "task_request": "Implement entry 1.18.",
        "implementation_file": "docs/dev/Phased_Feature_Implementation_Plan.md",
        "implementation_entry": "1.18",
    }


def test_real_manage_jobs_packet_is_complete_and_critical() -> None:
    """The designated critical pilot must never bypass Planner."""
    repo = Path(__file__).resolve().parents[2]
    packet = packet_module.build_task_packet(repo, _task(), baseline="abc123")

    assert packet["risk"]["tier"] == "CRITICAL"
    assert packet["planner_required"] is True
    assert packet["status"] == "READY_FOR_PLANNING"
    assert len(packet["requirements"]) == 4
    assert packet["local_nfrs"]
    assert packet["authorized_write_paths"]
    assert packet["authoring"]["route"] == "REUSE_EXISTING_FIRST"
    assert packet["controller_projection_paths"]
    assert all(item["sha256"] for item in packet["source_locations"])


def test_missing_contract_blocks_instead_of_inventing(tmp_path: Path) -> None:
    """Missing structured authority must make a feature packet non-ready."""
    repo = Path(__file__).resolve().parents[2]
    packet = packet_module.build_task_packet(
        repo,
        {**_task(), "task_id": "FEAT-NOT-REAL"},
        baseline="abc123",
    )

    assert packet["status"] == "BLOCKED"
    assert any("missing contract" in item for item in packet["unresolved_decisions"])


def test_source_change_invalidates_packet(tmp_path: Path) -> None:
    """A packet cannot authorize work after an authority source changes."""
    source = tmp_path / "authority.json"
    source.write_text("{}\n", encoding="utf-8")
    packet = {
        "schema_version": 1,
        "identity": {"baseline_commit": "base"},
        "source_locations": [
            {
                "path": "authority.json",
                "selector": "all",
                "sha256": packet_module._sha_bytes(source.read_bytes()),
            }
        ],
    }
    path = tmp_path / "packet.json"
    packet_module.write_task_packet(path, packet)
    packet_module.validate_task_packet(path, tmp_path, baseline="base")

    source.write_text('{"changed": true}\n', encoding="utf-8")
    with pytest.raises(packet_module.TaskPacketError, match="source changed"):
        packet_module.validate_task_packet(path, tmp_path, baseline="base")


def test_routine_requires_explicit_nonsemantic_task_wording() -> None:
    """Ordinary features cannot be down-tiered merely because they are small."""
    routine = packet_module.classify_risk(
        {
            "task_kind": "task",
            "task_request": "Documentation-only nonsemantic typo correction.",
        },
        [],
    )
    standard = packet_module.classify_risk(
        {"task_kind": "feature", "task_request": "Render a bounded panel."}, []
    )
    critical = packet_module.classify_risk(
        {"task_kind": "feature", "task_request": "Change session authorization."},
        [],
    )
    structural_keys_only = packet_module.classify_risk(
        {"task_kind": "feature", "task_request": "Render a bounded result."},
        [{"required_providers": [], "operation_gates": []}],
    )

    assert routine.tier is packet_module.RiskTier.ROUTINE
    assert standard.tier is packet_module.RiskTier.STANDARD
    assert structural_keys_only.tier is packet_module.RiskTier.STANDARD
    assert critical.tier is packet_module.RiskTier.CRITICAL


def test_authoring_route_scaffolds_only_missing_standard_backend(
    tmp_path: Path,
) -> None:
    """The first generator shape excludes existing, critical, and UI owners."""
    standard = packet_module.RiskClassification(
        packet_module.RiskTier.STANDARD, ("bounded",)
    )
    critical = packet_module.RiskClassification(
        packet_module.RiskTier.CRITICAL, ("security",)
    )
    task = {"task_kind": "feature"}
    contract = {
        "primary_capability": "demo.lookup@1",
        "state_ownership": "None; immutable results only.",
    }

    eligible = packet_module._authoring_route(
        repo=tmp_path,
        task=task,
        owner_path="app/services/demo/lookup",
        contract_target="app/contracts/demo/lookup.py",
        contract=contract,
        classification=standard,
    )
    excluded = packet_module._authoring_route(
        repo=tmp_path,
        task=task,
        owner_path="app/services/demo/lookup",
        contract_target="app/contracts/demo/lookup.py",
        contract=contract,
        classification=critical,
    )

    assert eligible["route"] == "SCAFFOLD_STATELESS_BACKEND"
    assert excluded["route"] == "NO_AUTOMATIC_SCAFFOLD"


def test_real_stateless_strategy_ast_packet_routes_to_scaffold() -> None:
    """The first scaffold has a real, bounded future feature consumer."""
    repo = Path(__file__).resolve().parents[2]
    task = {
        "task_kind": "feature",
        "task_id": "FEAT-STRAT-DEFINE_AST",
        "task_slug": "define-ast",
        "task_name": "Define strategy AST",
        "task_request": "Implement entry 3.07.",
        "implementation_file": "docs/dev/Phased_Feature_Implementation_Plan.md",
        "implementation_entry": "3.07",
    }

    packet = packet_module.build_task_packet(repo, task, baseline="abc123")

    assert packet["risk"]["tier"] == "STANDARD"
    assert packet["authoring"]["route"] == "SCAFFOLD_STATELESS_BACKEND"
    assert packet["compatible_example"]["feature_id"] == ("FEAT-PLUG-DECLARE_MANIFESTS")
    assert (
        "app/services/strategy/define_ast/feature.py"
        in packet["authorized_write_paths"]
    )
    assert packet["serialized_integration_write_paths"] == ["pyproject.toml"]
