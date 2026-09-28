"""Ownership documents fail closed before any contribution is executed."""

import json
from pathlib import Path
from typing import Any

import pytest
from app.host.packages import Package, confined_file, scan_packages


def make_package(root: Path, name: str, owner: str | None = None) -> dict[str, Any]:
    folder = f"app/ui/app/{'plugins' if owner else 'workspace'}/{name}"
    target = root / folder
    target.mkdir(parents=True, exist_ok=True)
    (target / "entry.ts").write_text("throw new Error('never execute during scan')")
    doc = {
        "schema_version": 1,
        "id": "test." + name,
        "version": "1.0.0",
        "host_contract": "1.0.0",
        "kind": "plugin" if owner else "workspace",
        "mode": "ui_only",
        "owner_workspace_id": owner,
        "attachment": {"slot_id": "test.view", "contract_version": "1.0.0"}
        if owner
        else None,
        "backend_entry": None,
        "ui_entry": folder + "/entry.ts",
        "owned_paths": {
            "source": [folder + "/entry.ts"],
            "metadata": [folder + "/package.json"],
        },
    }
    (target / "package.json").write_text(json.dumps(doc))
    return doc


def test_isolated_removal_and_fingerprint(tmp_path):
    make_package(tmp_path, "workspace")
    child = make_package(tmp_path, "child", "test.workspace")
    original = scan_packages(tmp_path)
    assert len(original.packages) == 2 and not original.issues
    for name in Package.model_validate(child).owned_paths.files():
        (tmp_path / name).unlink()
    remaining = scan_packages(tmp_path)
    assert [p.id for p in remaining.packages] == ["test.workspace"]
    assert remaining.fingerprint != original.fingerprint


def test_missing_owner_and_incomplete_pair(tmp_path):
    child = make_package(tmp_path, "child", "test.missing")
    assert scan_packages(tmp_path).issues[0].code == "missing_owner"
    (tmp_path / child["ui_entry"]).unlink()
    result = scan_packages(tmp_path)
    assert not result.packages
    assert result.issues[0].code == "invalid_package"


def test_duplicate_ownership_rejects_both(tmp_path):
    first = make_package(tmp_path, "first")
    second = make_package(tmp_path, "second")
    second["owned_paths"]["source"].append(first["ui_entry"])
    path = tmp_path / second["owned_paths"]["metadata"][0]
    path.write_text(json.dumps(second))
    result = scan_packages(tmp_path)
    assert not result.packages
    assert {i.code for i in result.issues} == {"overlapping_paths"}


@pytest.mark.parametrize(
    "name",
    [
        "data/a",
        "../secret",
        "app/plugins/../host/a",
        "C:/a",
        "app/plugins/a\\b",
        "app/plugins/a//b",
    ],
)
def test_protected_or_escaped_paths(tmp_path, name):
    with pytest.raises(ValueError):
        confined_file(tmp_path, name)


def test_invalid_modes_and_entry_ownership(tmp_path):
    doc = make_package(tmp_path, "one")
    doc["mode"] = "paired"
    with pytest.raises(ValueError, match="mode"):
        Package.model_validate(doc)
    doc["mode"] = "ui_only"
    doc["ui_entry"] = "app/ui/app/workspace/one/other.ts"
    with pytest.raises(ValueError, match="owned source"):
        Package.model_validate(doc)
