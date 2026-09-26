"""Discovery never executes descriptors; defects and removals stay isolated."""

import json
from typing import Any

from app.host.catalog import scan_catalog
from app.host.customizations import scan_presets


def descriptor(name: str = "test.plugin") -> dict[str, Any]:
    return {
        "id": name,
        "version": "1.0.0",
        "compatibility": "1",
        "parameter_schema": {"type": "object"},
    }


def test_literal_discovery_does_not_execute_and_removal_is_orthogonal(tmp_path):
    good = tmp_path / "good.py"
    good.write_text(
        "raise RuntimeError('must never execute')\nPLUGIN = " + repr(descriptor())
    )
    bad = tmp_path / "bad.py"
    bad.write_text("PLUGIN = eval('1')")
    view = scan_catalog((tmp_path,))
    assert len(view["domains"]) == 1
    assert view["domains"][0]["available"] is False
    assert len(view["domains"][0]["sha256"]) == 64
    assert len(view["issues"]) == 1
    bad.unlink()
    assert not scan_catalog((tmp_path,))["issues"]
    good.unlink()
    assert scan_catalog((tmp_path,))["domains"] == []


def test_duplicate_and_malformed_manifests_are_visible(tmp_path):
    for name in ("one", "two"):
        root = tmp_path / name
        root.mkdir()
        (root / "manifest.json").write_text(json.dumps(descriptor()))
    (tmp_path / "bad.py").write_text("syntax error here !!!")
    view = scan_catalog((tmp_path,))
    assert all(item["reason"] == "ambiguous_descriptor" for item in view["domains"])
    assert len(view["issues"]) == 3


def test_unknown_schema_and_missing_provider_fail_closed(tmp_path):
    data = descriptor()
    data["compatibility"] = "99"
    (tmp_path / "manifest.json").write_text(json.dumps(data))
    assert scan_catalog((tmp_path,))["issues"]
    data["compatibility"] = "1"
    data["requires"] = [{"id": "test.missing", "version": "1.0.0"}]
    (tmp_path / "manifest.json").write_text(json.dumps(data))
    assert scan_catalog((tmp_path,))["domains"][0]["reason"] == "unbound_capabilities"


def test_preset_json_inventory_is_not_owner_validation(tmp_path):
    (tmp_path / "valid.json").write_text('{"theme":"dark"}')
    (tmp_path / "bad.json").write_text("[]")
    (tmp_path / "huge.json").write_text("x" * 262145)
    snapshot = scan_presets(tmp_path)
    assert len(snapshot["entries"]) == 1
    assert snapshot["entries"][0]["status"] == "owner_validation_unavailable"
    assert len(snapshot["issues"]) == 2
