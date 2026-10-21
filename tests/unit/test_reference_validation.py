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

import hashlib
import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from tests.reference import validate
from tests.reference.manifest import EvidenceError


def _home_repository(tmp_path: Path, foreign: bool = False) -> Path:
    """Build a bounded synthetic Home owner and a single pending ledger record."""
    source = Path(__file__).resolve().parents[2]
    directory = tmp_path / "docs/dev/evidence"
    directory.mkdir(parents=True)
    for name in ("reimplementation.schema.json", "p00-inventory.json"):
        (directory / name).write_bytes(
            (source / "docs/dev/evidence" / name).read_bytes()
        )
    owner = tmp_path / "app/workspace/home/README.md"
    owner.parent.mkdir(parents=True)
    owner.write_text(
        "`FEAT-HOME-DASHBOARD` `FR-HOME-INDEX` `DEC-HOME-HOST-REUSE`", encoding="utf-8"
    )
    host = tmp_path / "app/host/README.md"
    host.parent.mkdir(parents=True)
    host.write_text("`FR-HOST-UNRELATED`", encoding="utf-8")
    ledger = json.loads(
        (source / "docs/dev/evidence/reimplementation.json").read_text()
    )
    record = deepcopy(ledger["records"]["SQX145-EV-000001"])
    record["target_mapping"].update(
        domain="workspace",
        feature_ids=["FEAT-HOME-DASHBOARD"],
        requirement_ids=["FR-HOST-UNRELATED" if foreign else "FR-HOME-INDEX"],
        decision_ids=["DEC-HOME-HOST-REUSE"],
    )
    reference = deepcopy(record["sources"][0])
    reference.update(
        catalog_id="E-R01",
        artifact_locator="app/workspace/home/README.md",
        fingerprint={
            "algorithm": "sha256",
            "value": hashlib.sha256(owner.read_bytes()).hexdigest(),
        },
    )
    record["sources"] = [reference]
    record["validation"].update(
        state="pending", artifact_paths=[], executed_at=None, actual_observation=None
    )
    locators = ledger["source_catalog"]["E-R01"]["locators"]
    if "app/workspace/home" not in locators:
        locators.append("app/workspace/home")
    ledger["records"] = {"SQX145-EV-000001": record}
    ledger["allocation_high_water_mark"] = 1
    (directory / "reimplementation.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )
    return tmp_path


@pytest.mark.parametrize("foreign", [False, True])
def test_home_registry_resolves_only_its_own_ids(tmp_path: Path, foreign: bool) -> None:
    """Validate a Home record against its real owner rather than host tokens."""
    repository = _home_repository(tmp_path, foreign)
    assert [issue.code for issue in validate.validate_evidence(repository)] == (
        ["REGISTRY_ID"] if foreign else []
    )


def _add_home_inventory(repository: Path) -> tuple[Path, dict[str, Any]]:
    """Attach a single independent Home donor binding to a synthetic ledger."""
    directory = repository / "docs/dev/evidence"
    baseline = json.loads((directory / "p00-inventory.json").read_text())
    artifact = {
        "locator": "internal/plugins/AppHome/module.js",
        "sha256": "a" * 64,
        "family": "web_resource",
        "stage": "Stage 2",
        "proposed_feature_id": "FEAT-HOME-DASHBOARD",
    }
    owner = repository / "app/workspace/home/README.md"
    source = {
        "locator": "app/workspace/home/README.md",
        "sha256": hashlib.sha256(owner.read_bytes()).hexdigest(),
    }
    home = {
        **baseline,
        "donor_artifacts": [artifact],
        "repository_sources": [source],
        "totals": {
            **baseline["totals"],
            "donor_artifacts": 1,
            "encrypted_jars": 0,
            "xml_templates": 0,
        },
    }
    path = directory / "home-inventory.json"
    path.write_text(json.dumps(home), encoding="utf-8")
    ledger_path = directory / "reimplementation.json"
    ledger = json.loads(ledger_path.read_text())
    record = ledger["records"]["SQX145-EV-000001"]
    record["sources"][0].update(
        catalog_id="E-L01",
        artifact_locator=artifact["locator"],
        fingerprint={"algorithm": "sha256", "value": artifact["sha256"]},
    )
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    return path, home


@pytest.mark.parametrize("mutation", ["none", "missing", "changed", "invalid"])
def test_home_inventory_donor_binding(tmp_path: Path, mutation: str) -> None:
    """Require a strict, independent Home inventory for new donor references."""
    repository = _home_repository(tmp_path)
    path, inventory = _add_home_inventory(repository)
    if mutation == "missing":
        path.unlink()
    elif mutation == "changed":
        inventory["donor_artifacts"][0]["sha256"] = "b" * 64
        path.write_text(json.dumps(inventory), encoding="utf-8")
    elif mutation == "invalid":
        inventory["totals"]["donor_artifacts"] = 2
        path.write_text(json.dumps(inventory), encoding="utf-8")
        with pytest.raises(EvidenceError, match="MANIFEST_TOTALS"):
            validate.validate_evidence(repository)
        return
    codes = [issue.code for issue in validate.validate_evidence(repository)]
    assert codes == ([] if mutation == "none" else ["SOURCE_DONOR_BINDING"])


@pytest.mark.parametrize("kind", ["donor", "repository", "cohort"])
def test_home_inventory_conflicts_fail_closed(tmp_path: Path, kind: str) -> None:
    """Reject ambiguous identities or cohort counts rather than picking a pin."""
    repository = _home_repository(tmp_path)
    path, home = _add_home_inventory(repository)
    baseline = json.loads((path.parent / "p00-inventory.json").read_text())
    if kind == "donor":
        home["donor_artifacts"] = [deepcopy(baseline["donor_artifacts"][0])]
        home["donor_artifacts"][0]["sha256"] = "b" * 64
    elif kind == "repository":
        home["repository_sources"] = [deepcopy(baseline["repository_sources"][0])]
        home["repository_sources"][0]["sha256"] = "b" * 64
    else:
        home["totals"]["plugin_directories"] += 1
    path.write_text(json.dumps(home), encoding="utf-8")
    with pytest.raises(EvidenceError, match=r"INVENTORY_.*CONFLICT"):
        validate.validate_evidence(repository)


def test_home_inventory_repository_source_is_checked(tmp_path: Path) -> None:
    """Include Home owner fingerprints in public ownership qualification."""
    repository = _home_repository(tmp_path)
    path, home = _add_home_inventory(repository)
    baseline_path = path.parent / "p00-inventory.json"
    baseline = json.loads(baseline_path.read_text())
    baseline["repository_sources"] = home["repository_sources"]
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    assert validate.validate_ownership(repository) == []
    (repository / "app/workspace/home/README.md").write_text(
        "Changed", encoding="utf-8"
    )
    assert [issue.code for issue in validate.validate_ownership(repository)] == [
        "SOURCE_HASH"
    ]


def test_home_inventory_is_included_in_donor_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inspect the combined manifest passed to the CLI reconciliation boundary."""
    repository = _home_repository(tmp_path)
    _add_home_inventory(repository)
    received = []
    monkeypatch.setattr(
        validate, "__file__", str(repository / "tests/reference/validate.py")
    )
    monkeypatch.setattr(validate, "validate_ownership", lambda root: [])
    monkeypatch.setattr(validate, "_fixture_checks", lambda root, ledger: [])
    monkeypatch.setattr(validate, "resolve_roots", lambda root: root)
    monkeypatch.setattr(
        validate, "verify_inventory", lambda manifest, roots: received.append(manifest)
    )
    assert validate.main(["--check-donor"]) == 0
    assert any(
        item.locator == "internal/plugins/AppHome/module.js"
        for item in received[0].donor_artifacts
    )
    assert received[0].totals["encrypted_jars"] == 8


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
