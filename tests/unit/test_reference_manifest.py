"""Verify inventory provenance, safe roots and adversarial JSON inputs.

Description:
    Synthetic temporary archives exercise read-only reconciliation and failure
    diagnostics. Operational stores and installed donor data are never changed.
Purpose:
    FEAT-HOST-EVIDENCE; DEC-HOST-P00-BOUNDED-FIXTURES and RELEASE-GATES.
Key Capabilities:
    - FR-HOST-EVIDENCE-MANIFEST-VALIDATION: Assert bounded/typed parsing and logs.
      Associated: all test functions; Logging: caplog verifies delivered FR codes.
    - FR-HOST-EVIDENCE-ROOT-RESOLUTION: Assert explicit authority and containment.
      Associated: root/path tests; Logging: captured root success/failure events.
    - FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION: Assert complete cohort comparison.
      Associated: inventory tests; Logging: captured reconciliation/failure events.
Python API Usage:
    Run isolated tests through pytest; no application runtime API is exposed.
CLI Usage:
    uv run pytest tests/unit/test_reference_manifest.py --no-cov
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from tests.reference.manifest import (
    MANIFEST_FR,
    MAX_JSON_BYTES,
    EvidenceError,
    fingerprint,
    load_manifest,
    read_json,
    resolve_locator,
    resolve_roots,
    timestamp,
    verify_inventory,
)


@pytest.fixture
def inventory(tmp_path: Path) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repo"
    donor = tmp_path / "donor"
    repository.mkdir()
    archive = donor / "internal/libs/test.jar"
    archive.parent.mkdir(parents=True)
    resource = donor / "internal/plugins/Panel"
    resource.mkdir(parents=True)
    (resource / "module.js").write_text("independent test asset", encoding="utf-8")
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("sample/A.class", b"independent class-count fixture")
    roadmap = repository / "roadmap.md"
    roadmap.write_text("independent allocation fixture", encoding="utf-8")
    data = {
        "schema_version": 1,
        "captured_at": "2026-10-06T14:00:00+00:00",
        "reference_cohort": "144.2953",
        "installed_build": None,
        "activation_status": "unverified",
        "source_head": "a" * 40,
        "roadmap": {"locator": "roadmap.md", "sha256": fingerprint(roadmap)},
        "artifacts": [
            {
                "locator": "internal/libs/test.jar",
                "sha256": fingerprint(archive),
                "class_count": 1,
                "family": "library",
                "feature_id": "FEAT-HOST-TEST",
                "phase": "P01",
            }
        ],
        "resources": [
            {
                "locator": "internal/plugins/Panel",
                "feature_id": "FEAT-UI-PANEL",
                "requirement_id": "FR-UI-PANEL-RESOURCE",
                "phase": "P01",
                "activation_status": "unverified",
                "files": [
                    {
                        "locator": "internal/plugins/Panel/module.js",
                        "sha256": fingerprint(resource / "module.js"),
                    }
                ],
            }
        ],
        "totals": {
            "archives": 1,
            "classes": 1,
            "resources": 1,
            "library": 1,
            "plugin": 0,
            "runtime": 0,
        },
    }
    manifest = repository / "manifest.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return repository, donor, manifest


def test_inventory_success_logs(
    inventory: tuple[Path, Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    repository, donor, path = inventory
    caplog.set_level(logging.DEBUG)
    verify_inventory(load_manifest(path), resolve_roots(repository, donor))
    assert {
        "FR-HOST-EVIDENCE-ROOT-RESOLUTION",
        MANIFEST_FR,
        "FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION",
    } <= {r.__dict__.get("fr_id") for r in caplog.records}
    assert str(donor) not in caplog.text


@pytest.mark.parametrize(
    "change,code",
    [
        ("hash", "INVENTORY_HASH"),
        ("missing", "INVENTORY_ARCHIVE_SET"),
        ("extra", "INVENTORY_ARCHIVE_SET"),
        ("classes", "INVENTORY_CLASSES"),
        ("invalid", "INVENTORY_ARCHIVE_INVALID"),
        ("resource_file", "INVENTORY_RESOURCE_FILES"),
        ("resource_hash", "INVENTORY_RESOURCE_HASH"),
        ("resource_dir", "INVENTORY_RESOURCE_SET"),
        ("roadmap", "ROADMAP_HASH"),
    ],
)
def test_inventory_drift(
    inventory: tuple[Path, Path, Path], change: str, code: str
) -> None:
    repository, donor, path = inventory
    manifest = load_manifest(path)
    archive = donor / "internal/libs/test.jar"
    if change == "hash":
        archive.write_bytes(b"changed")
    elif change == "missing":
        archive.unlink()
    elif change == "extra":
        (archive.parent / "extra.jar").write_bytes(b"extra")
    elif change == "classes":
        manifest.artifacts[0].__dict__["class_count"] = 0
    elif change == "invalid":
        archive.write_bytes(b"invalid zip")
        manifest.artifacts[0].__dict__["sha256"] = fingerprint(archive)
    elif change == "resource_file":
        (donor / "internal/plugins/Panel/extra.js").write_text("extra")
    elif change == "resource_hash":
        (donor / "internal/plugins/Panel/module.js").write_text("changed")
    elif change == "resource_dir":
        (donor / "internal/plugins/Extra").mkdir()
    else:
        (repository / "roadmap.md").write_text("changed")
    with pytest.raises(EvidenceError, match=code):
        verify_inventory(manifest, resolve_roots(repository, donor))


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("schema_version", 2, "MANIFEST_INVALID"),
        ("captured_at", "bad", "MANIFEST_INVALID"),
        ("captured_at", "2026-10-06", "MANIFEST_INVALID"),
        ("totals", {}, "MANIFEST_TOTALS"),
        ("extra", True, "MANIFEST_INVALID"),
    ],
)
def test_manifest_invalid(
    inventory: tuple[Path, Path, Path], field: str, value: object, code: str
) -> None:
    path = inventory[2]
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(EvidenceError, match=code):
        load_manifest(path)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "bad_hash",
        "bool_count",
        "resource_escape",
        "resource_jar",
        "resource_duplicate",
    ],
)
def test_manifest_identity_errors(
    inventory: tuple[Path, Path, Path], mutation: str
) -> None:
    path = inventory[2]
    data = json.loads(path.read_text())
    if mutation == "duplicate":
        data["artifacts"].append(data["artifacts"][0])
    elif mutation == "bad_hash":
        data["artifacts"][0]["sha256"] = "bad"
    elif mutation == "bool_count":
        data["artifacts"][0]["class_count"] = True
    elif mutation == "resource_escape":
        data["resources"][0]["files"][0]["locator"] = "outside.js"
    elif mutation == "resource_jar":
        data["resources"][0]["files"][0]["locator"] += ".jar"
    else:
        data["resources"][0]["files"].append(data["resources"][0]["files"][0])
    path.write_text(json.dumps(data))
    with pytest.raises(EvidenceError):
        load_manifest(path)


@pytest.mark.parametrize(
    "data,code",
    [
        (b'{"x":1,"x":2}', "JSON_DUPLICATE_KEY"),
        (b'{"x":NaN}', "JSON_NONFINITE"),
        (b'{"x":Infinity}', "JSON_NONFINITE"),
        (b"[]", "JSON_OBJECT_REQUIRED"),
        (b"\xff", "JSON_INVALID"),
        (b"{", "JSON_INVALID"),
        (b'{"x":1e999}', "JSON_NONFINITE"),
    ],
)
def test_json_bad_inputs(
    tmp_path: Path, data: bytes, code: str, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "input.json"
    path.write_bytes(data)
    with pytest.raises(EvidenceError, match=code):
        read_json(path)
    assert any(r.__dict__.get("fr_id") == MANIFEST_FR for r in caplog.records)
    assert str(path) not in caplog.text


def test_json_size_and_read_errors(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_bytes(b"{}" + b" " * (MAX_JSON_BYTES - 2))
    assert read_json(path) == {}
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(EvidenceError, match="JSON_TOO_LARGE"):
        read_json(path)
    for limit in (0, -1, MAX_JSON_BYTES + 1, True):
        with pytest.raises(EvidenceError, match="JSON_LIMIT_INVALID"):
            read_json(path, limit=limit)
    with pytest.raises(EvidenceError, match="JSON_READ_FAILED"):
        read_json(tmp_path / "absent")
    with pytest.raises(EvidenceError, match="ARTIFACT_READ_FAILED"):
        fingerprint(tmp_path / "absent")


@pytest.mark.parametrize(
    "locator",
    [
        "../escape",
        "/absolute",
        "C:/drive",
        "C:relative",
        "\\\\server\\share",
        "a//b",
        "a/./b",
        "",
        "a/",
    ],
)
def test_unsafe_locators(tmp_path: Path, locator: str) -> None:
    with pytest.raises(EvidenceError, match="LOCATOR_INVALID"):
        resolve_locator(tmp_path, locator)


def test_roots_and_link_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    donor = tmp_path / "donor"
    donor.mkdir()
    repository = tmp_path / "repo"
    repository.mkdir()
    monkeypatch.delenv("SQX_REFERENCE_ROOT", raising=False)
    with pytest.raises(EvidenceError, match="ROOT_UNRESOLVED"):
        resolve_roots(repository)
    monkeypatch.setenv("SQX_REFERENCE_ROOT", str(donor))
    assert resolve_roots(repository).donor == donor
    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_roots(repository, repository)
    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_roots(repository, tmp_path / "absent")
    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_locator(tmp_path / "absent", "a")
    link = repository / "escape"
    try:
        link.symlink_to(donor, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            pytest.skip("Temporary symlink creation unavailable")
        # A test-owned junction needs no symlink privilege and cannot touch shared links.
        script = tmp_path / "create-junction.ps1"
        script.write_text(
            "param([string]$LinkPath, [string]$TargetPath)\n"
            "$ErrorActionPreference = 'Stop'\n"
            "New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-File",
                str(script),
                "-LinkPath",
                str(link),
                "-TargetPath",
                str(donor),
            ],
            capture_output=True,
            check=False,
            timeout=10,
        )
        assert result.returncode == 0
    with pytest.raises(EvidenceError, match="LOCATOR_ESCAPE"):
        resolve_locator(repository, "escape/file")


def test_classless_archive(inventory: tuple[Path, Path, Path]) -> None:
    repository, donor, path = inventory
    archive = donor / "internal/libs/test.jar"
    with zipfile.ZipFile(archive, "w"):
        pass
    data = json.loads(path.read_text())
    data["artifacts"][0]["sha256"] = fingerprint(archive)
    data["artifacts"][0]["class_count"] = 0
    data["totals"]["classes"] = 0
    path.write_text(json.dumps(data))
    verify_inventory(load_manifest(path), resolve_roots(repository, donor))
    assert timestamp("2026-10-06T14:00:00Z").endswith("Z")
