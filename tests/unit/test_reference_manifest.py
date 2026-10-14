"""Test bounded reference manifest parsing, root resolution, and inventory checks.

Description:
    Unit tests exercise root resolution, relative locator containment, bounded
    JSON parsing, SHA-256 fingerprinting, manifest validation, and synthetic
    donor reconciliation in `tests/reference/manifest.py` using isolated
    temporary directories.

Purpose:
    FEAT-HOST-EVIDENCE: Verify manifest and inventory reconciliation gates.

Key Capabilities:
    - FR-HOST-EVIDENCE-ROOT-RESOLUTION: Verify root resolution and path containment.
      Associated: `test_resolve_roots_and_locators()`
      Logging: caplog asserts `FR-HOST-EVIDENCE-ROOT-RESOLUTION` events.
    - FR-HOST-EVIDENCE-MANIFEST-VALIDATION: Verify JSON bounds and manifest models.
      Associated: `test_read_json_and_manifest_validation()`
      Logging: caplog asserts `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` events.
    - FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION: Verify SHA-256 and count checks.
      Associated: `test_verify_inventory_and_drift()`
      Logging: caplog asserts `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` events.

Python API Usage:
    ```python
    import pytest

    pytest.main(["tests/unit/test_reference_manifest.py", "--no-cov"])
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/test_reference_manifest.py --no-cov
    ```
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from tests.reference.manifest import (
    INVENTORY_FR,
    MANIFEST_FR,
    ROOT_FR,
    EvidenceError,
    ReferenceRoots,
    ResourceFile,
    fingerprint,
    load_manifest,
    logical_locator,
    read_json,
    repository_source,
    resolve_locator,
    resolve_roots,
    timestamp,
    verify_inventory,
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_resolve_roots_and_locators(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    repo = tmp_path / "repo"
    donor = tmp_path / "donor"
    repo.mkdir()
    donor.mkdir()
    (repo / "docs").mkdir()
    sample = repo / "docs/sample.txt"
    sample.write_bytes(b"ok")

    assert logical_locator("docs/sample.txt") == "docs/sample.txt"
    assert resolve_locator(repo, "docs/sample.txt") == sample.resolve()

    monkeypatch.setenv("SQX_REFERENCE_ROOT", str(donor))
    roots = resolve_roots(repo)
    assert roots.repository == repo.resolve()
    assert roots.donor == donor.resolve()
    assert any(r.__dict__.get("fr_id") == ROOT_FR for r in caplog.records)

    monkeypatch.delenv("SQX_REFERENCE_ROOT", raising=False)
    monkeypatch.setenv("SQX_145_REFERENCE_ROOT", str(donor))
    assert resolve_roots(repo).donor == donor.resolve()

    monkeypatch.delenv("SQX_145_REFERENCE_ROOT", raising=False)
    with pytest.raises(EvidenceError, match="ROOT_UNRESOLVED"):
        resolve_roots(repo)

    with pytest.raises(EvidenceError, match="COHORT_UNKNOWN"):
        resolve_roots(repo, donor, cohort="bad")  # type: ignore[arg-type]

    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_roots(repo, repo)

    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_roots(repo, tmp_path / "missing")

    with pytest.raises(EvidenceError, match="ROOT_INVALID"):
        resolve_locator(tmp_path / "missing", "docs/sample.txt")

    for bad_loc in ("", "../escape", "D:abs", "/root", "a\\b", "a//b", "a/\x01"):
        with pytest.raises(EvidenceError, match="LOCATOR_INVALID"):
            logical_locator(bad_loc)


def test_timestamps_and_read_json_guards(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    assert timestamp("2026-10-13T21:55:00+03:00") == "2026-10-13T21:55:00+03:00"
    with pytest.raises(EvidenceError, match="TIMESTAMP_INVALID"):
        timestamp("not-a-timestamp")
    with pytest.raises(EvidenceError, match="TIMESTAMP_NAIVE"):
        timestamp("2026-10-13T21:55:00")

    valid_json = tmp_path / "valid.json"
    valid_json.write_text('{"a": 1, "b": 2.5}', encoding="utf-8")
    assert read_json(valid_json) == {"a": 1, "b": 2.5}

    with pytest.raises(EvidenceError, match="JSON_LIMIT_INVALID"):
        read_json(valid_json, limit=0)
    with pytest.raises(EvidenceError, match="JSON_LIMIT_INVALID"):
        read_json(valid_json, limit=True)
    with pytest.raises(EvidenceError, match="JSON_READ_FAILED"):
        read_json(tmp_path / "missing.json")
    with pytest.raises(EvidenceError, match="JSON_TOO_LARGE"):
        read_json(valid_json, limit=5)

    dup_json = tmp_path / "dup.json"
    dup_json.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(EvidenceError, match="JSON_DUPLICATE_KEY"):
        read_json(dup_json)

    nan_json = tmp_path / "nan.json"
    nan_json.write_text('{"a": NaN}', encoding="utf-8")
    with pytest.raises(EvidenceError, match="JSON_NONFINITE"):
        read_json(nan_json)

    overflow_json = tmp_path / "overflow.json"
    overflow_json.write_text('{"a": 1e500}', encoding="utf-8")
    with pytest.raises(EvidenceError, match="JSON_NONFINITE"):
        read_json(overflow_json)

    list_json = tmp_path / "list.json"
    list_json.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(EvidenceError, match="JSON_OBJECT_REQUIRED"):
        read_json(list_json)

    bad_json = tmp_path / "bad.json"
    bad_json.write_bytes(b"\xff\xfe")
    with pytest.raises(EvidenceError, match="JSON_INVALID"):
        read_json(bad_json)

    with pytest.raises(EvidenceError, match="ARTIFACT_READ_FAILED"):
        fingerprint(tmp_path / "no-such-file")

    assert any(r.__dict__.get("fr_id") == MANIFEST_FR for r in caplog.records)


def _create_synthetic_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    donor = tmp_path / "donor"
    (repo / "docs").mkdir(parents=True)
    doc = repo / "docs/README.md"
    doc.write_bytes(b"# readme\n")

    (donor / "internal/libs").mkdir(parents=True)
    (donor / "internal/ctemplate").mkdir(parents=True)
    (donor / "internal/plugins/PluginA").mkdir(parents=True)
    (donor / "internal/extend/Snippets/SQ/Blocks").mkdir(parents=True)

    jar_enc = donor / "internal/libs/SQLib.jar.enc"
    jar_enc.write_bytes(b"encrypted-jar")
    xml_tpl = donor / "internal/ctemplate/config.xml"
    xml_tpl.write_bytes(b"<Config/>")
    snippet = donor / "internal/extend/Snippets/SQ/Blocks/Sample.java"
    snippet.write_bytes(b"class Sample {}")

    manifest_data: dict[str, Any] = {
        "schema_version": 1,
        "captured_at": "2026-10-13T21:55:00+03:00",
        "reference_cohort": "145-dev1",
        "installed_build": None,
        "activation_status": "unverified",
        "donor_artifacts": [
            {
                "locator": "internal/libs/SQLib.jar.enc",
                "sha256": _sha256_bytes(b"encrypted-jar"),
                "family": "encrypted_jar",
                "stage": "Stage 2",
                "proposed_feature_id": "FEAT-KERNEL-PRIMITIVES",
            },
            {
                "locator": "internal/ctemplate/config.xml",
                "sha256": _sha256_bytes(b"<Config/>"),
                "family": "xml_template",
                "stage": "Stage 3",
                "proposed_feature_id": "FEAT-STRATEGIES-BLOCKS",
            },
        ],
        "repository_sources": [
            {
                "locator": "docs/README.md",
                "sha256": _sha256_bytes(b"# readme\n"),
            }
        ],
        "totals": {
            "donor_artifacts": 2,
            "encrypted_jars": 1,
            "xml_templates": 1,
            "plugin_directories": 1,
            "snippet_java_files": 1,
        },
    }
    manifest_path = repo / "docs/p00-inventory.json"
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    return repo, donor, manifest_path


def test_load_manifest_and_verify_inventory(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    repo, donor, manifest_path = _create_synthetic_tree(tmp_path)
    manifest = load_manifest(manifest_path)
    roots = ReferenceRoots(repo, donor)
    verify_inventory(manifest, roots)
    assert any(r.__dict__.get("fr_id") == INVENTORY_FR for r in caplog.records)

    with pytest.raises(EvidenceError, match="SOURCE_HASH"):
        repository_source(
            repo,
            ResourceFile(locator="docs/README.md", sha256="0" * 64),
        )


def test_manifest_schema_and_corruption_rejections(tmp_path: Path) -> None:
    repo, _, manifest_path = _create_synthetic_tree(tmp_path)
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    dup = json.loads(json.dumps(raw))
    dup["donor_artifacts"].append(dup["donor_artifacts"][0])
    manifest_path.write_text(json.dumps(dup), encoding="utf-8")
    with pytest.raises(EvidenceError, match="MANIFEST_DUPLICATE"):
        load_manifest(manifest_path)

    bad_totals = json.loads(json.dumps(raw))
    bad_totals["totals"]["encrypted_jars"] = 99
    manifest_path.write_text(json.dumps(bad_totals), encoding="utf-8")
    with pytest.raises(EvidenceError, match="MANIFEST_TOTALS"):
        load_manifest(manifest_path)

    bad_schema = json.loads(json.dumps(raw))
    bad_schema["schema_version"] = 2
    manifest_path.write_text(json.dumps(bad_schema), encoding="utf-8")
    with pytest.raises(EvidenceError, match="MANIFEST_INVALID"):
        load_manifest(manifest_path)


def test_verify_inventory_drift_rejections(tmp_path: Path) -> None:
    repo, donor, manifest_path = _create_synthetic_tree(tmp_path)
    roots = ReferenceRoots(repo, donor)
    valid_manifest = load_manifest(manifest_path)

    (donor / "internal/plugins/PluginExtra").mkdir()
    with pytest.raises(EvidenceError, match="DONOR_COUNT_DRIFT"):
        verify_inventory(valid_manifest, roots)
    (donor / "internal/plugins/PluginExtra").rmdir()

    (donor / "internal/ctemplate/config.xml").write_bytes(b"tampered")
    with pytest.raises(EvidenceError, match="DONOR_ARTIFACT_HASH"):
        verify_inventory(valid_manifest, roots)
    (donor / "internal/ctemplate/config.xml").write_bytes(b"<Config/>")

    (donor / "internal/plugins/PluginA").rmdir()
    (donor / "internal/plugins").rmdir()
    with pytest.raises(EvidenceError, match="DONOR_STRUCTURE_MISSING"):
        verify_inventory(valid_manifest, roots)
