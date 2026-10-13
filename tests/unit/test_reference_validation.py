"""Exercise evidence ledger integrity, ownership gates, and CLI qualification.

Description:
    Isolated temporary copies of the repository evidence files test Draft 2020-12
    schema v4 validation, monotonic `SQX145-EV-NNNNNN` allocation, source catalog
    and SHA-256 fingerprint checks, reciprocal supersession/contradiction links,
    cycle detection, registry/proposal mappings, and CLI exit behavior.

Purpose:
    FEAT-HOST-EVIDENCE: Verify `tests/reference/validate.py` and its FR logs.

Key Capabilities:
    - FR-HOST-EVIDENCE-LEDGER-INTEGRITY: Assert schema, sources, and lineage.
      Associated: `test_current_ledger_ownership_and_logs()`,
      `test_ledger_failures()`
      Logging: caplog verifies `LEDGER_FR` events.
    - FR-HOST-EVIDENCE-OWNERSHIP-GATES: Assert registry mappings and runtime gate.
      Associated: `test_current_ledger_ownership_and_logs()`,
      `test_ownership_and_fixture_failures()`
      Logging: caplog verifies `OWNER_FR` warning and error events.
    - FR-HOST-EVIDENCE-QUALIFICATION-CLI: Assert CLI outcomes and exit codes.
      Associated: `test_cli_main_execution()`
      Logging: caplog verifies `CLI_FR` lifecycle events.

Python API Usage:
    ```python
    import pytest

    pytest.main(["tests/unit/test_reference_validation.py", "--no-cov"])
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/test_reference_validation.py --no-cov
    ```
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from tests.reference import validate
from tests.reference.manifest import EvidenceError


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy bounded Stage 0 evidence and repository sources into tmp_path."""
    source = Path(__file__).resolve().parents[2]
    root = tmp_path / "repo"
    for path in (source / "docs/dev/evidence").rglob("*"):
        if path.is_file():
            target = root / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for locator in (
        "AGENTS.md",
        "docs/PROJECT.md",
        "docs/ARCHITECTURE.md",
        "app/host/README.md",
        "docs/SQX/README.md",
        "docs/SQX/architecture-and-reimplementation.md",
        "docs/SQX/libs/SQLib.md",
        "docs/SQX/libs/SQDataLib.md",
        "docs/SQX/libs/SQTradingLib.md",
        "tests/reference/p00-fixtures.json",
    ):
        target = root / locator
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / locator).read_bytes())
    return root


def test_current_ledger_ownership_and_logs(
    repository: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    assert validate.validate_evidence(repository) == []
    assert validate.validate_ownership(repository) == []
    assert any(r.__dict__.get("fr_id") == validate.LEDGER_FR for r in caplog.records)
    assert any(
        r.__dict__.get("fr_id") == validate.OWNER_FR and r.levelno == logging.WARNING
        for r in caplog.records
    )
    assert str(repository) not in caplog.text
    assert [
        i.code for i in validate.validate_ownership(repository, qualify_runtime=True)
    ] == ["RUNTIME_AUTHORITY_BLOCKED"]


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("schema", "LEDGER_SCHEMA"),
        ("high_water_mismatch", "RECORD_ID_ALLOCATION"),
        ("catalog", "SOURCE_CATALOG"),
        ("location", "SOURCE_LOCATION"),
        ("source_locator", "SOURCE_LOCATOR"),
        ("repo_missing_file", "SOURCE_LOCATOR"),
        ("source_hash", "SOURCE_HASH"),
        ("donor_hash", "SOURCE_DONOR_BINDING"),
        ("registry", "REGISTRY_ID"),
        ("registered_with_proposed", "PROPOSED_MAPPING"),
        ("proposed_valid", ""),
        ("proposed_bad", "PROPOSED_MAPPING"),
        ("pass_artifact", "PASS_ARTIFACT"),
        ("runtime_source", "PASS_RUNTIME_SOURCE"),
        ("record_link", "RECORD_LINK"),
        ("contradiction_reciprocal", "CONTRADICTION_RECIPROCAL"),
        ("supersession_reciprocal_forward", "SUPERSESSION_RECIPROCAL"),
        ("supersession_reciprocal_backward", "SUPERSESSION_RECIPROCAL"),
        ("supersession_cycle", "SUPERSESSION_CYCLE"),
    ],
)
def test_ledger_failures(repository: Path, mutation: str, code: str) -> None:  # noqa: C901
    path = repository / "docs/dev/evidence/reimplementation.json"
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rec1 = data["records"]["SQX145-EV-000001"]
    rec2 = data["records"]["SQX145-EV-000002"]
    if mutation == "schema":
        data["extra_field"] = True
    elif mutation == "high_water_mismatch":
        data["allocation_high_water_mark"] = 99
    elif mutation == "catalog":
        rec1["sources"][0]["catalog_id"] = "E-R99"
    elif mutation == "location":
        for k in ("section", "symbol", "line_range", "json_pointer", "xpath"):
            rec1["sources"][0]["location"][k] = None
    elif mutation == "source_locator":
        rec1["sources"][0]["artifact_locator"] = "unlisted/file.txt"
    elif mutation == "repo_missing_file":
        data["source_catalog"]["E-R01"]["locators"].append("docs/missing.md")
        rec2["sources"][0]["artifact_locator"] = "docs/missing.md"
    elif mutation == "source_hash":
        rec2["sources"][0]["fingerprint"]["value"] = "0" * 64
    elif mutation == "donor_hash":
        rec1["sources"][0]["fingerprint"]["value"] = "0" * 64
    elif mutation == "registry":
        rec1["target_mapping"]["requirement_ids"] = ["FR-HOST-UNREGISTERED"]
    elif mutation == "registered_with_proposed":
        rec1["target_mapping"]["proposed_owner"] = "app/host"
    elif mutation == "proposed_valid":
        rec1["target_mapping"] = {
            "domain": "workspace",
            "registration_status": "proposed",
            "feature_ids": [],
            "requirement_ids": [],
            "decision_ids": [],
            "proposed_owner": "app/workspace/simulator/README.md",
            "proposed_feature_id": "FEAT-SIMULATOR-CORE",
            "proposed_requirement_ids": ["FR-SIMULATOR-ORDERS"],
            "proposed_decision_ids": [],
            "notes": None,
        }
    elif mutation == "proposed_bad":
        rec1["target_mapping"]["registration_status"] = "proposed"
    elif mutation == "pass_artifact":
        rec1["validation"]["artifact_paths"] = ["docs/dev/evidence/missing.json"]
    elif mutation == "runtime_source":
        rec1["validation"]["kind"] = "runtime"
    elif mutation == "record_link":
        rec1["relationships"]["supports_records"] = ["SQX145-EV-999999"]
    elif mutation == "contradiction_reciprocal":
        rec1["relationships"]["contradicts_records"] = ["SQX145-EV-000002"]
    elif mutation == "supersession_reciprocal_forward":
        rec1["record_status"] = "superseded"
        rec1["relationships"]["superseded_by"] = "SQX145-EV-000002"
    elif mutation == "supersession_reciprocal_backward":
        rec2["relationships"]["supersedes_records"] = ["SQX145-EV-000001"]
    elif mutation == "supersession_cycle":
        rec1["record_status"] = "superseded"
        rec2["record_status"] = "superseded"
        rec1["relationships"]["superseded_by"] = "SQX145-EV-000002"
        rec2["relationships"]["supersedes_records"] = ["SQX145-EV-000001"]
        rec2["relationships"]["superseded_by"] = "SQX145-EV-000001"
        rec1["relationships"]["supersedes_records"] = ["SQX145-EV-000002"]
    path.write_text(json.dumps(data), encoding="utf-8")
    issues = validate.validate_evidence(repository)
    if not code:
        assert issues == []
    else:
        assert any(i.code == code for i in issues)


def test_ownership_and_fixture_failures(repository: Path) -> None:
    (repository / "AGENTS.md").write_bytes(b"modified")
    issues = validate.validate_ownership(repository)
    assert any(i.code == "SOURCE_HASH" for i in issues)

    ledger = json.loads(
        (repository / "docs/dev/evidence/reimplementation.json").read_text(
            encoding="utf-8"
        )
    )
    fix_path = repository / "tests/reference/p00-fixtures.json"
    fix_data = json.loads(fix_path.read_text(encoding="utf-8"))
    fix_data["cases"][0]["evidence_ids"] = ["SQX145-EV-999999"]
    fix_path.write_text(json.dumps(fix_data), encoding="utf-8")
    assert any(
        i.code == "FIXTURE_RECORD_LINK"
        for i in validate._fixture_checks(repository, ledger)
    )

    fix_data["cases"][0]["evidence_ids"] = ["SQX145-EV-000002"]
    fix_data["cases"][0]["requirement_id"] = "FR-HOST-EVIDENCE-UNKNOWN"
    fix_data["cases"][0]["capture_artifact"] = "docs/dev/evidence/missing.json"
    fix_data["cases"][0]["artifact_sha256"] = "f" * 64
    fix_path.write_text(json.dumps(fix_data), encoding="utf-8")
    codes = {i.code for i in validate._fixture_checks(repository, ledger)}
    assert {
        "FIXTURE_REGISTRY_ID",
        "FIXTURE_CAPTURE_ARTIFACT",
        "FIXTURE_SOURCE_HASH",
    } <= codes


def test_cli_main_execution(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    assert validate.main([]) == 0
    assert any(r.__dict__.get("fr_id") == validate.CLI_FR for r in caplog.records)

    monkeypatch.setattr(
        validate,
        "validate_evidence",
        lambda _repo: [validate.ValidationIssue("LEDGER_SCHEMA")],
    )
    assert validate.main([]) == 1

    def _raise_error(_repo: Path) -> list[validate.ValidationIssue]:
        raise EvidenceError("BOOM")

    monkeypatch.setattr(validate, "validate_evidence", _raise_error)
    assert validate.main([]) == 1
