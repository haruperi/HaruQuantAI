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
    - FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION: Assert complete current source/member coverage.
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
from typing import cast

import pytest

from tests.reference.manifest import (
    MANIFEST_FR,
    MAX_JSON_BYTES,
    EvidenceError,
    ReferenceCohort,
    ResourceFile,
    fingerprint,
    load_manifest,
    read_json,
    reconcile_metadata,
    repository_source,
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
        "reference_cohort": "145-dev1",
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
        ("roadmap", "SOURCE_HASH"),
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
    monkeypatch.delenv("SQX_145_REFERENCE_ROOT", raising=False)
    with pytest.raises(EvidenceError, match="ROOT_UNRESOLVED"):
        resolve_roots(repository)
    monkeypatch.setenv("SQX_145_REFERENCE_ROOT", str(donor))
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
            timeout=30,
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


def test_only_explicit_current_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing/unsupported source authority never selects a fallback."""
    monkeypatch.delenv("SQX_145_REFERENCE_ROOT", raising=False)
    with pytest.raises(EvidenceError, match="ROOT_UNRESOLVED"):
        resolve_roots(tmp_path)
    with pytest.raises(EvidenceError, match="COHORT_UNKNOWN"):
        resolve_roots(tmp_path, cohort=cast("ReferenceCohort", "unsupported-build"))


def test_current_source_requires_exact_hash(tmp_path: Path) -> None:
    """Repository source drift fails even when a similarly named file exists."""
    path = tmp_path / "source.md"
    path.write_text("current independent source")
    source = ResourceFile(locator="source.md", sha256=fingerprint(path))
    assert repository_source(tmp_path, source) == path
    path.write_text("changed")
    with pytest.raises(EvidenceError, match="SOURCE_HASH"):
        repository_source(tmp_path, source)
    with pytest.raises(EvidenceError, match="ARTIFACT_READ_FAILED"):
        fingerprint(tmp_path / "missing")


@pytest.fixture
def metadata(inventory: tuple[Path, Path, Path]) -> tuple[Path, Path]:
    """One synthetic raw class binds the archive, declaration and outer index."""
    repo, _, manifest = inventory
    a = load_manifest(manifest).artifacts[0]
    class_hash = "1" * 64
    shard = {
        "schema_version": 1,
        "reference_cohort": "145-dev1",
        "root": "SQX_145_REFERENCE_ROOT",
        "artifact_locator": a.locator,
        "archive_sha256": a.sha256,
        "captured_at": "2026-10-06T14:00:00Z",
        "classes": [
            {
                "entry": "sample/A.class",
                "occurrence": 0,
                "sha256": class_hash,
                "name": "sample/A",
                "major": 61,
                "minor": 0,
                "access": 1,
                "superclass": "java/lang/Object",
                "interfaces": [],
                "fields": [],
                "methods": [
                    {
                        "name": "run",
                        "descriptor": "()V",
                        "access": 1,
                        "code_sha256": "2" * 64,
                        "code_length": 1,
                    }
                ],
                "class_references": ["java/lang/Object"],
            }
        ],
    }
    shard_path = repo / "shard.json"
    shard_path.write_text(json.dumps(shard))
    binding = {"locator": "shard.json", "sha256": fingerprint(shard_path)}
    index = {
        "captured_at": "2026-10-06T14:00:00Z",
        "root": "SQX_145_REFERENCE_ROOT",
        "artifact_locator": a.locator,
        "sha256": a.sha256,
        "class_count": 1,
        "unique_class_entries": 1,
        "resource_count": 0,
        "duplicate_entries": [],
        "classes": {"sample/A.class": class_hash},
        "resources": {},
        "class_occurrences": [
            {
                "entry": "sample/A.class",
                "occurrence": 0,
                "sha256": class_hash,
                "member_shard": "shard.json",
            }
        ],
        "member_shards": [binding],
    }
    index_path = repo / "index.json"
    index_path.write_text(json.dumps(index))
    data = {
        "schema_version": 1,
        "reference_cohort": "145-dev1",
        "manifest": {"locator": manifest.name, "sha256": fingerprint(manifest)},
        "class_indices": [{"locator": "index.json", "sha256": fingerprint(index_path)}],
        "member_shards": [binding],
        "coexisting_policy": "unverified_classpath_no_automatic_alias",
    }
    path = repo / "metadata.json"
    path.write_text(json.dumps(data))
    return repo, path


def test_member_metadata_success_and_logs(
    metadata: tuple[Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Independent synthetic member coverage is complete and observable."""
    caplog.set_level(logging.DEBUG)
    repo, path = metadata
    assert reconcile_metadata(repo, path) == {"archives": 1, "classes": 1, "members": 1}
    assert any(
        r.__dict__.get("fr_id") == "FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION"
        for r in caplog.records
    )
    assert str(repo) not in caplog.text


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("cohort", "METADATA_INVALID"),
        ("metadata_extra", "METADATA_INVALID"),
        ("indices_missing", "CLASS_INDEX_SET"),
        ("indices_duplicate", "CLASS_INDEX_SET"),
        ("index_hash", "SOURCE_HASH"),
        ("manifest_hash", "SOURCE_HASH"),
        ("index_extra", "CLASS_INDEX_INVALID"),
        ("index_count", "CLASS_INDEX_BINDING"),
        ("index_archive", "CLASS_INDEX_SET"),
        ("index_resource", "CLASS_INDEX_INVALID"),
        ("index_entry", "CLASS_INDEX_INVALID"),
        ("class_hash", "CLASS_INDEX_INVALID"),
        ("occurrence_missing", "CLASS_INDEX_BINDING"),
        ("occurrence_entry", "CLASS_OCCURRENCE_SET"),
        ("occurrence_order", "CLASS_OCCURRENCE_BINDING"),
        ("occurrence_hash", "CLASS_OCCURRENCE_BINDING"),
        ("shard_set", "MEMBER_SHARD_SET"),
        ("shard_hash", "SOURCE_HASH"),
        ("shard_binding", "MEMBER_SHARD_BINDING"),
        ("shard_schema", "MEMBER_SHARD_INVALID"),
        ("member_entry", "MEMBER_CLASS_BINDING"),
        ("member_name", "MEMBER_CLASS_NAME"),
        ("member_code", "MEMBER_CODE_BINDING"),
        ("member_duplicate", "MEMBER_CLASS_BINDING"),
        ("outer_shard_duplicate", "MEMBER_SHARD_SET"),
    ],
)
def test_member_metadata_rejects_false_coverage(  # noqa: C901 - independent adversarial cases
    metadata: tuple[Path, Path], mutation: str, code: str
) -> None:
    """Broken identities, coverage and declarations fail despite refreshed pins."""
    repo, path = metadata
    d = json.loads(path.read_text())
    ip = repo / "index.json"
    sp = repo / "shard.json"
    index = json.loads(ip.read_text())
    shard = json.loads(sp.read_text())
    if mutation == "cohort":
        d["reference_cohort"] = "unsupported-build"
    elif mutation == "metadata_extra":
        d["unexpected"] = True
    elif mutation == "indices_missing":
        d["class_indices"] = []
    elif mutation == "indices_duplicate":
        d["class_indices"] *= 2
    elif mutation == "index_hash":
        d["class_indices"][0]["sha256"] = "f" * 64
    elif mutation == "manifest_hash":
        d["manifest"]["sha256"] = "f" * 64
    elif mutation == "index_extra":
        index["unexpected"] = True
    elif mutation == "index_count":
        index["class_count"] = 2
    elif mutation == "index_archive":
        index["artifact_locator"] = "other.jar"
    elif mutation == "index_resource":
        index["resources"] = {"bad.class": "1" * 64}
        index["resource_count"] = 1
    elif mutation == "index_entry":
        index["classes"] = {"bad.txt": "1" * 64}
    elif mutation == "class_hash":
        index["classes"]["sample/A.class"] = "bad"
    elif mutation == "occurrence_missing":
        index["class_occurrences"] = []
    elif mutation == "occurrence_entry":
        index["class_occurrences"][0]["entry"] = "other.class"
    elif mutation == "occurrence_order":
        index["class_occurrences"][0]["occurrence"] = 1
    elif mutation == "occurrence_hash":
        index["class_occurrences"][0]["sha256"] = "f" * 64
    elif mutation == "shard_set":
        d["member_shards"] = []
    elif mutation == "shard_hash":
        index["member_shards"][0]["sha256"] = "f" * 64
    elif mutation == "shard_binding":
        shard["archive_sha256"] = "f" * 64
    elif mutation == "shard_schema":
        shard["classes"][0]["methods"][0]["access"] = True
    elif mutation == "member_entry":
        shard["classes"][0]["entry"] = "other.class"
    elif mutation == "member_name":
        shard["classes"][0]["name"] = "other"
    elif mutation == "member_code":
        del shard["classes"][0]["methods"][0]["code_length"]
    elif mutation == "member_duplicate":
        shard["classes"] *= 2
    else:
        d["member_shards"] *= 2
    sp.write_text(json.dumps(shard))
    if mutation != "shard_hash":
        index["member_shards"][0]["sha256"] = fingerprint(sp)
    if mutation not in {"shard_set", "outer_shard_duplicate"}:
        d["member_shards"] = index["member_shards"].copy()
    ip.write_text(json.dumps(index))
    if mutation != "index_hash":
        for binding in d["class_indices"]:
            binding["sha256"] = fingerprint(ip)
    path.write_text(json.dumps(d))
    with pytest.raises(EvidenceError, match=code):
        reconcile_metadata(repo, path)
