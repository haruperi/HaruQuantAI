"""A report cannot turn missing, stale, skipped or failed checks into qualification."""

import json
from pathlib import Path
from typing import Any

import pytest
from app.host.packages import scan_packages
from scripts.package_inventory import source_fingerprint
from scripts.removal_check import required_cases

from scripts import release_check
from tests.host.test_packages import make_package


def report_fixture(root: Path, evidence: Path) -> dict[str, Any]:
    evidence.mkdir(parents=True)
    for name in ("candidate", "ui_boundaries"):
        (evidence / (name + ".log")).write_text(json.dumps({"exit_code": 0}) + "\n")
    make_package(root, "owner")
    make_package(root, "child", "test.owner")
    inventory = scan_packages(root)
    ids = sorted(p.id for p in inventory.packages)
    report: dict[str, Any] = {
        "scope": "release",
        "status": "pass",
        "shipping_ids": ids,
        "qualified_ids": ids,
        "source_sha256": source_fingerprint(root),
        "blockers": [],
        "cases": [],
    }
    for spec in required_cases(inventory):
        closure = set(spec.targets)
        closure.update(
            p.id for p in inventory.packages if p.owner_workspace_id in closure
        )
        checks = []
        for name in (
            "python_survivors",
            "ui_typecheck",
            "ui_tests",
            "ui_build",
            "browser_restart_resources",
        ):
            log = evidence / spec.id / (name + ".log")
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                json.dumps({"command": ["test-command"]})
                + "\n"
                + json.dumps({"exit_code": 0})
                + "\n"
            )
            checks.append(
                {
                    "id": name,
                    "command": ["test-command"],
                    "status": "pass",
                    "exit_code": 0,
                    "evidence_path": log.name,
                }
            )
        report["cases"].append(
            {
                "id": spec.id,
                "kind": spec.kind,
                "target_ids": list(spec.targets),
                "removed_paths": sorted(
                    {
                        name
                        for p in inventory.packages
                        if p.id in closure
                        for name in p.owned_paths.files()
                    }
                ),
                "retained_ids": sorted(
                    p.id for p in inventory.packages if p.id not in closure
                ),
                "checks": checks,
                "status": "pass",
            }
        )
    return report


@pytest.mark.parametrize(
    "failure",
    [
        "missing_case",
        "skipped",
        "failed",
        "missing_log",
        "stale",
        "wrong_closure",
        "cohort",
    ],
)
def test_gate_rejects_invalid_evidence(tmp_path, monkeypatch, failure):
    evidence = tmp_path / "evidence"
    report = report_fixture(tmp_path, evidence)
    monkeypatch.setattr(
        release_check,
        "evidence_bindings",
        lambda root: {"source_sha256": source_fingerprint(root)},
    )
    assert release_check.validate_report(tmp_path, report, evidence) == []
    if failure == "missing_case":
        report["cases"].pop()
    elif failure == "skipped":
        report["cases"][0]["checks"][0]["status"] = "skipped"
    elif failure == "failed":
        report["cases"][0]["checks"][0]["exit_code"] = 1
    elif failure == "missing_log":
        (evidence / "baseline/python_survivors.log").unlink()
    elif failure == "stale":
        (tmp_path / "app/ui/app/workspace/owner/entry.ts").write_text("changed")
    elif failure == "wrong_closure":
        report["cases"][0]["removed_paths"] = ["data/forbidden"]
    elif failure == "cohort":
        report["scope"] = "cohort"
    assert release_check.validate_report(tmp_path, report, evidence)
