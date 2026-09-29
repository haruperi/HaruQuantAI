"""Discovery never executes descriptors; defects and removals stay isolated."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from app.host.discovery import (
    MAX_SOURCE_BYTES,
    read_descriptor,
    safe_files,
    scan_presets,
)
from pydantic import ValidationError


def sample_descriptor(name: str = "test.plugin") -> dict[str, Any]:
    """Return a minimal valid plugin descriptor mapping."""
    return {
        "id": name,
        "version": "1.0.0",
        "compatibility": "1",
        "parameter_schema": {"type": "object"},
    }


def test_literal_discovery_does_not_execute_python_code(tmp_path: Path) -> None:
    """Reading a descriptor parses AST literals only and never executes code."""
    good = tmp_path / "good.py"
    good.write_text(
        "raise RuntimeError('must never execute')\nPLUGIN = "
        + repr(sample_descriptor()),
        encoding="utf-8",
    )
    desc, digest = read_descriptor(good)
    assert desc.id == "test.plugin"
    assert len(digest) == 64


def test_eval_in_descriptor_is_rejected(tmp_path: Path) -> None:
    """Dynamic expression execution is rejected by literal AST evaluation."""
    bad = tmp_path / "bad.py"
    bad.write_text("PLUGIN = eval('1')", encoding="utf-8")
    with pytest.raises(ValueError):
        read_descriptor(bad)


def test_syntax_error_and_missing_plugin_assignment(tmp_path: Path) -> None:
    """Malformed Python and missing PLUGIN declarations fail closed."""
    syntax_bad = tmp_path / "syntax.py"
    syntax_bad.write_text("def broken(: pass", encoding="utf-8")
    with pytest.raises(SyntaxError):
        read_descriptor(syntax_bad)

    no_plugin = tmp_path / "none.py"
    no_plugin.write_text("FOO = 1", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected one literal PLUGIN descriptor"):
        read_descriptor(no_plugin)


def test_descriptor_size_limit_enforced(tmp_path: Path) -> None:
    """Files exceeding MAX_SOURCE_BYTES are rejected before parsing."""
    oversized = tmp_path / "oversized.py"
    oversized.write_bytes(b"#" * (MAX_SOURCE_BYTES + 10))
    with pytest.raises(ValueError, match="Descriptor exceeds size limit"):
        read_descriptor(oversized)


def test_json_manifest_reading_and_validation(tmp_path: Path) -> None:
    """JSON manifests parse into valid PluginDescriptor models or raise ValidationError."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(sample_descriptor()), encoding="utf-8")
    desc, digest = read_descriptor(manifest)
    assert desc.id == "test.plugin"
    assert len(digest) == 64

    bad_manifest = tmp_path / "bad.json"
    bad_data = sample_descriptor()
    bad_data["compatibility"] = "99"
    bad_manifest.write_text(json.dumps(bad_data), encoding="utf-8")
    with pytest.raises(ValidationError):
        read_descriptor(bad_manifest)


def test_safe_files_containment_and_nonexistent_root(tmp_path: Path) -> None:
    """Safe files confines traversal to root and handles missing directories."""
    missing = tmp_path / "nonexistent"
    assert safe_files(missing, "*.json") == []

    file_a = tmp_path / "a.json"
    file_a.write_text("{}", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    file_b = sub / "b.json"
    file_b.write_text("{}", encoding="utf-8")

    assert safe_files(tmp_path, "*.json") == [file_a, file_b]


def test_preset_json_inventory_is_not_owner_validation(tmp_path: Path) -> None:
    """Preset inventory checks structure and size without validating domain schema."""
    (tmp_path / "valid.json").write_text('{"theme":"dark"}', encoding="utf-8")
    (tmp_path / "bad.json").write_text("[]", encoding="utf-8")
    (tmp_path / "huge.json").write_text("x" * (MAX_SOURCE_BYTES + 1), encoding="utf-8")
    snapshot = scan_presets(tmp_path)
    assert len(snapshot["entries"]) == 1
    assert snapshot["entries"][0]["status"] == "owner_validation_unavailable"
    assert len(snapshot["issues"]) == 2
