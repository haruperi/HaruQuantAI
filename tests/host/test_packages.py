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


def test_owned_offline_example_is_discoverable(tmp_path):
    """A declared deterministic example must not exclude its whole package."""
    doc = make_package(tmp_path, "workspace")
    example = "tests/examples/offline.py"
    (tmp_path / example).parent.mkdir(parents=True)
    (tmp_path / example).write_text("# Deterministic offline example\n")
    doc["owned_paths"]["examples"] = [example]
    (tmp_path / doc["owned_paths"]["metadata"][0]).write_text(json.dumps(doc))
    result = scan_packages(tmp_path)
    assert not result.issues
    assert result.packages[0].owned_paths.examples == (example,)


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


def test_workspace_cli_paths_removal_restore_and_retained_data(tmp_path: Path) -> None:
    """Exact named clients belong to one workspace closure; data stays independent."""
    from app.host.packages import apply_removal, plan_removal, restore_removal
    from app.persistence.resources import ResourceStore

    doc = make_package(tmp_path, "workspace")
    make_package(tmp_path, "child", "test.workspace")
    clients = ("scripts/workspace_cli.py", "tests/test_workspace_cli.py")
    for name in clients:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Workspace-owned client fixture\n")
        with pytest.raises(ValueError, match="protected"):
            confined_file(tmp_path, name)
        assert (
            confined_file(tmp_path, name, client_workspace_ids=("test.workspace",))
            == path
        )
    doc["owned_paths"]["source"].append(clients[0])
    doc["owned_paths"]["tests"] = [clients[1]]
    (tmp_path / doc["owned_paths"]["metadata"][0]).write_text(json.dumps(doc))
    store = ResourceStore(tmp_path / "retained/resources")
    ref = store.publish(
        "test.child",
        "1.0.0",
        b"retained",
        schema_id="test.retained",
        schema_version="1.0.0",
        schema_json='{"type":"string"}',
        media_type="text/plain",
        readers=("*",),
    )
    inventory = scan_packages(tmp_path)
    assert not inventory.issues
    child_plan = plan_removal(tmp_path, inventory, "test.child")
    assert not set(clients).intersection(child_plan.files)
    assert child_plan.client_workspace_ids == ()
    plan = plan_removal(tmp_path, inventory, "test.workspace")
    assert set(clients).issubset(plan.files)
    assert plan.client_workspace_ids == ("test.workspace",)
    journal = apply_removal(tmp_path, plan)
    assert all(not (tmp_path / name).exists() for name in clients)
    assert store.read("independent", ref)[0] == b"retained"
    restore_removal(tmp_path, journal)
    assert scan_packages(tmp_path).fingerprint == inventory.fingerprint
    assert all((tmp_path / name).is_file() for name in clients)


@pytest.mark.parametrize(
    "name",
    [
        "scripts/other_cli.py",
        "scripts/ci_check.py",
        "scripts/main.py",
        "scripts/workspace_cli.py/escape",
        "tests/test_cli.py",
        "tests/test_other_cli.py",
        "tests/host/test_packages.py",
    ],
)
def test_workspace_cli_allowance_does_not_open_generic_roots(
    tmp_path: Path, name: str
) -> None:
    """A workspace cannot claim arbitrary CLI files, host tests or workflow scripts."""
    doc = make_package(tmp_path, "workspace")
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Protected fixture\n")
    doc["owned_paths"]["source"].append(name)
    (tmp_path / doc["owned_paths"]["metadata"][0]).write_text(json.dumps(doc))
    assert scan_packages(tmp_path).issues[0].code == "invalid_package"
    with pytest.raises(ValueError, match="protected"):
        confined_file(tmp_path, name, client_workspace_ids=("test.workspace",))


def test_plugin_cannot_claim_named_workspace_cli(tmp_path: Path) -> None:
    """External client path authority belongs exclusively to workspace declarations."""
    make_package(tmp_path, "workspace")
    doc = make_package(tmp_path, "child", "test.workspace")
    path = tmp_path / "scripts/child_cli.py"
    path.parent.mkdir()
    path.write_text("# Not a workspace client\n")
    doc["owned_paths"]["source"].append("scripts/child_cli.py")
    (tmp_path / doc["owned_paths"]["metadata"][0]).write_text(json.dumps(doc))
    assert any(
        issue.code == "invalid_package" for issue in scan_packages(tmp_path).issues
    )
