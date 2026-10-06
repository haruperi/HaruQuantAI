"""Exercise evidence lineage, registries and unavailable runtime gates.

Description:
    Temporary current reference copies isolate ledger/source/registry mutations and test
    schema, IDs, source links, ownership and CLI failures. Shared stores are absent.
Purpose:
    FEAT-HOST-EVIDENCE; DEC-HOST-SQX145-REFERENCE and SCHEMA-EVOLUTION.
Key Capabilities:
    - FR-HOST-EVIDENCE-LEDGER-INTEGRITY: Assert current schema, sources and lineage.
      Associated: ledger tests; Logging: caplog verifies integrity events.
    - FR-HOST-EVIDENCE-OWNERSHIP-GATES: Assert proposals and runtime refusal.
      Associated: ownership tests; Logging: warning/error gap events are asserted.
    - FR-HOST-EVIDENCE-QUALIFICATION-CLI: Assert honest process results and errors.
      Associated: CLI tests; Logging: delivered lifecycle/results are asserted.
Python API Usage:
    Execute tests with pytest; no runtime application interface is exposed.
CLI Usage:
    uv run pytest tests/unit/test_reference_validation.py --no-cov
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from tests.reference import validate


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy bounded current evidence; member coverage has its own integration gate."""
    source = Path(__file__).resolve().parents[2]
    root = tmp_path / "repo"
    for path in (source / "docs/dev/evidence").rglob("*"):
        if path.is_file() and not any(
            part in {"archives", "members"} for part in path.parts
        ):
            target = root / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for locator in (
        "docs/dev/sqx-full-application-roadmap.md",
        "app/host/README.md",
        "tests/reference/p00-fixtures.json",
    ):
        target = root / locator
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / locator).read_bytes())
    ownership = json.loads((root / "docs/dev/evidence/p00-ownership.json").read_text())
    for registry in ownership["existing_ui_registries"]:
        target = root / registry["readme"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / registry["readme"]).read_bytes())
    monkeypatch.setattr(validate, "reconcile_metadata", lambda *_: {})
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
    "mutation,code",
    [
        ("schema", "LEDGER_SCHEMA"),
        ("duplicate_id", "RECORD_ID_ALLOCATION"),
        ("low_id", "RECORD_ID_ALLOCATION"),
        ("catalog", "SOURCE_CATALOG"),
        ("registry", "REGISTRY_ID"),
        ("link", "RECORD_LINK"),
        ("supersession", "SUPERSESSION_RECIPROCAL"),
        ("passed_empty", "LEDGER_SCHEMA"),
        ("passed_artifact", "PASS_ARTIFACT"),
        ("runtime", "PASS_RUNTIME_SOURCE"),
        ("clean_room", "LEDGER_SCHEMA"),
        ("location", "SOURCE_LOCATION"),
        ("source_path", "SOURCE_LOCATOR"),
        ("source_hash", "SOURCE_HASH"),
        ("allocation_high_water", "RECORD_ID_ALLOCATION"),
        ("wrong_cohort", "LEDGER_SCHEMA"),
        ("proposed_owner", "PROPOSED_MAPPING"),
        ("donor_hash", "SOURCE_DONOR_BINDING"),
        ("schema_remote", "LEDGER_SCHEMA"),
        ("cycle", "SUPERSESSION_CYCLE"),
    ],
)
def test_ledger_failures(repository: Path, mutation: str, code: str) -> None:  # noqa: C901 - explicit adversarial cases
    path = repository / "docs/dev/evidence/reimplementation.json"
    data = json.loads(path.read_text())
    key = next(iter(data["records"]))
    record = data["records"][key]
    if mutation == "schema":
        data["extra"] = True
    elif mutation == "duplicate_id":
        data["records"]["SQX145-EV-000001"] = data["records"].pop(key)
    elif mutation == "low_id":
        data["records"]["SQX145-EV-000000"] = data["records"].pop(key)
    elif mutation == "catalog":
        record["sources"][0]["catalog_id"] = "E-R99"
    elif mutation == "registry":
        record["target_mapping"]["requirement_ids"] = ["FR-HOST-UNREGISTERED"]
    elif mutation == "link":
        record["relationships"]["supports_records"] = ["SQX145-EV-999999"]
    elif mutation == "supersession":
        record["relationships"]["superseded_by"] = "SQX145-EV-000133"
    elif mutation == "passed_empty":
        record["validation"]["actual_observation"] = None
    elif mutation == "passed_artifact":
        record["validation"]["artifact_paths"] = ["missing.json"]
    elif mutation == "runtime":
        record["validation"]["kind"] = "runtime"
    elif mutation == "clean_room":
        record["clean_room"]["contains_sensitive_data"] = True
    elif mutation == "location":
        record["sources"][0]["location"] = dict.fromkeys(
            record["sources"][0]["location"]
        )
    elif mutation == "source_path":
        record["sources"][0]["artifact_locator"] = "../escape"
    elif mutation == "source_hash":
        record["sources"][0]["fingerprint"]["value"] = "f" * 64
    elif mutation == "allocation_high_water":
        data["allocation_high_water_mark"] = 132
    elif mutation == "wrong_cohort":
        record["reference_scope"]["build"] = "unsupported-build"
    elif mutation == "proposed_owner":
        proposed = next(
            r
            for r in data["records"].values()
            if r["target_mapping"]["registration_status"] == "proposed"
        )
        proposed["target_mapping"]["feature_ids"] = ["FEAT-HOST-UNREGISTERED"]
    elif mutation == "donor_hash":
        donor = next(
            r
            for r in data["records"].values()
            if r["sources"][0]["catalog_id"] == "E-L14"
        )
        donor["sources"][0]["fingerprint"]["value"] = "f" * 64
    elif mutation == "schema_remote":
        schema_path = repository / "docs/dev/evidence/reimplementation.schema.json"
        schema = json.loads(schema_path.read_text())
        schema["$ref"] = "https://example.invalid/schema"
        schema_path.write_text(json.dumps(schema))
    else:
        other = data["records"]["SQX145-EV-000133"]
        record["relationships"]["superseded_by"] = "SQX145-EV-000133"
        record["relationships"]["supersedes_records"] = ["SQX145-EV-000133"]
        other["relationships"]["superseded_by"] = key
        other["relationships"]["supersedes_records"] = [key]
    path.write_text(json.dumps(data))
    assert code in {i.code for i in validate.validate_evidence(repository)}


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("feature", "OWNER_FEATURE_SET"),
        ("mapping", "OWNER_FEATURE_MAPPING"),
        ("seed", "OWNER_SEED_SET"),
        ("resource", "OWNER_RESOURCE_SET"),
        ("runtime", "RUNTIME_AUTHORITY_BLOCKED"),
        ("ui", "UI_REGISTRY_DRIFT"),
    ],
)
def test_ownership_failures(repository: Path, mutation: str, code: str) -> None:
    path = repository / "docs/dev/evidence/p00-ownership.json"
    data = json.loads(path.read_text())
    if mutation == "feature":
        data["feature_proposals"].pop()
    elif mutation == "mapping":
        data["feature_proposals"][0]["phase"] = "P00"
    elif mutation == "seed":
        data["requirement_seeds"].pop()
    elif mutation == "resource":
        data["resource_proposals"].pop()
    elif mutation == "runtime":
        data["runtime_qualified"] = True
    else:
        (repository / data["existing_ui_registries"][0]["readme"]).write_text("changed")
    path.write_text(json.dumps(data))
    assert code in {i.code for i in validate.validate_ownership(repository)}


def test_cli_offline_and_failures(
    repository: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(
        validate, "__file__", str(repository / "tests/reference/validate.py")
    )
    assert validate.main([]) == 0
    assert any(r.__dict__.get("fr_id") == validate.CLI_FR for r in caplog.records)
    monkeypatch.delenv("SQX_145_REFERENCE_ROOT", raising=False)
    assert validate.main(["--check-donor"]) == 1
    path = repository / "tests/reference/p00-fixtures.json"
    data = json.loads(path.read_text())
    data["cases"][0]["evidence_ids"] = ["SQX145-EV-999999"]
    data["cases"][0]["capture_artifact"] = "missing.json"
    path.write_text(json.dumps(data))
    assert validate.main([]) == 1
    path.write_text("invalid")
    assert validate.main([]) == 1
