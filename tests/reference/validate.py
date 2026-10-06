"""Qualify evidence lineage and proposed ownership without donor execution.

Description:
    Offline qualification validates current and historical schemas, relationships,
    provenance and owner registries. The CLI optionally compares actual donor
    bytes through the manifest service. Missing runtime authority remains blocked;
    historical passes do not qualify the current tree. No stores are opened.

Purpose:
    FEAT-HOST-EVIDENCE: Make reference integrity checks repeatable and reviewable.
    Implements DEC-HOST-P00-HISTORICAL-EVIDENCE, DEC-HOST-P00-SCHEMA-EVOLUTION,
    DEC-HOST-P00-REGISTRY-BOUNDARY and DEC-HOST-P00-VALIDATION-DEPENDENCY.

Key Capabilities:
    - FR-HOST-EVIDENCE-LEDGER-INTEGRITY: Check schemas, lineage and observation kinds.
      Associated: `ValidationIssue`, `validate_evidence()` and private ledger helpers
      Logging: DEBUG records checks; INFO records counts; ERROR records issue codes.
    - FR-HOST-EVIDENCE-OWNERSHIP-GATES: Resolve identities and preserve proposals.
      Associated: `validate_ownership()` and private registry helpers
      Logging: DEBUG records checks; WARNING records gaps; ERROR records gate codes.
    - FR-HOST-EVIDENCE-QUALIFICATION-CLI: Run offline or explicit donor checks.
      Associated: `main()`
      Logging: INFO records lifecycle; ERROR records invalid qualification. Only
      the CLI configures handlers; no input values or exception payloads are logged.

Python API Usage:
    ```python
    from pathlib import Path
    from tests.reference.validate import validate_evidence, validate_ownership

    root = Path.cwd()
    issues = validate_evidence(root) + validate_ownership(root)
    ```

CLI Usage:
    ```bash
    uv run python -m tests.reference.validate
    uv run python -m tests.reference.validate --check-donor
    ```
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from logging import getLogger as get_logger  # noqa: N813 - approved adapter name
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from tests.reference.fixtures import load_fixtures
from tests.reference.manifest import (
    EvidenceError,
    Manifest,
    fingerprint,
    load_manifest,
    logical_locator,
    read_json,
    resolve_locator,
    resolve_roots,
    verify_inventory,
)

logger = get_logger(__name__)
LEDGER_FR = "FR-HOST-EVIDENCE-LEDGER-INTEGRITY"
OWNER_FR = "FR-HOST-EVIDENCE-OWNERSHIP-GATES"
CLI_FR = "FR-HOST-EVIDENCE-QUALIFICATION-CLI"
EVIDENCE_DIRECTORY = "docs/dev/evidence"


@dataclass(frozen=True)
class ValidationIssue:
    """A bounded code and optional evidence identity, never raw input values."""

    code: str
    record_id: str | None = None


def _issue(code: str, record_id: str | None = None) -> ValidationIssue:
    """Emit one integrity failure without disclosing its input payload."""
    logger.error("%s: %s", LEDGER_FR, code, extra={"fr_id": LEDGER_FR, "code": code})
    return ValidationIssue(code, record_id)


def _schema_errors(document: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Use full Draft 2020-12 and format validation with no remote resolution."""
    logger.debug("%s: schema", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError:
        return True

    # Only the approved local schema is accepted; remote refs are never fetched.
    def remote_ref(value: object) -> bool:
        logger.debug("%s: schema references", LEDGER_FR, extra={"fr_id": LEDGER_FR})
        if isinstance(value, dict):
            return any(
                (k == "$ref" and isinstance(v, str) and not v.startswith("#"))
                or remote_ref(v)
                for k, v in value.items()
            )
        if isinstance(value, list):
            return any(remote_ref(v) for v in value)
        return False

    if remote_ref(schema):
        return True
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return next(validator.iter_errors(document), None) is not None


def _registry_ids(path: Path) -> set[str]:
    """Read only explicit registry table identities from the owning README."""
    logger.debug("%s: registry", OWNER_FR, extra={"fr_id": OWNER_FR})
    try:
        text = path.read_text(encoding="utf-8")
    except OSError, UnicodeError:
        return set()
    return set(re.findall(r"(?m)^\| `((?:FEAT|FR|DEC)-[A-Z0-9_-]+)` \|", text))


def _relationships(records: dict[str, Any]) -> list[ValidationIssue]:
    """Resolve all links and require reciprocal supersession without cycles."""
    logger.debug("%s: relationships", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    issues = []
    for identity, record in records.items():
        links = record["relationships"]
        for field in ("supports_records", "contradicts_records", "supersedes_records"):
            for target in links[field]:
                if target not in records or target == identity:
                    issues.append(_issue("RECORD_LINK", identity))
        later = links["superseded_by"]
        if later is not None and (
            later not in records
            or identity not in records[later]["relationships"]["supersedes_records"]
        ):
            issues.append(_issue("SUPERSESSION_RECIPROCAL", identity))
        for earlier in links["supersedes_records"]:
            if earlier in records and (
                records[earlier]["relationships"]["superseded_by"] != identity
            ):
                issues.append(_issue("SUPERSESSION_RECIPROCAL", identity))
        seen = {identity}
        cursor = later
        while cursor is not None and cursor in records:
            if cursor in seen:
                issues.append(_issue("SUPERSESSION_CYCLE", identity))
                break
            seen.add(cursor)
            cursor = records[cursor]["relationships"]["superseded_by"]
    return issues


def _source_checks(
    records: dict[str, Any], catalog: dict[str, Any], root: Path, *, current: bool
) -> list[ValidationIssue]:
    """Check narrow sources, mappings, paths and fresh passed observations."""
    logger.debug("%s: records", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    issues = []
    for identity, record in records.items():
        for source in record["sources"]:
            entry = catalog.get(source["catalog_id"])
            if entry is None:
                issues.append(_issue("SOURCE_CATALOG", identity))
                continue
            if entry["root"] is not None:
                try:
                    locator = source["artifact_locator"]
                    # Historical directory notation retains its original trailing /.
                    logical_locator(locator if current else locator.rstrip("/"))
                except EvidenceError:
                    issues.append(_issue("SOURCE_LOCATOR", identity))
            if current and not any(source["location"].values()):
                issues.append(_issue("SOURCE_LOCATION", identity))
            if current and entry["root"] == "HARUQUANTAI_ROOT":
                try:
                    actual = fingerprint(
                        resolve_locator(root, source["artifact_locator"])
                    )
                    if (
                        source["fingerprint"] is None
                        or actual != source["fingerprint"]["value"]
                    ):
                        issues.append(_issue("SOURCE_HASH", identity))
                except EvidenceError:
                    issues.append(_issue("SOURCE_ARTIFACT", identity))
    return issues


def _current_checks(records: dict[str, Any], root: Path) -> list[ValidationIssue]:
    """Require registered target identities and actual passed artifacts."""
    logger.debug("%s: current records", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    issues = []
    for identity, record in records.items():
        mapping = record["target_mapping"]
        registered = set().union(
            *(
                _registry_ids(resolve_locator(root, p))
                for p in mapping["documentation_targets"]
            )
        )
        mapped_ids = (
            mapping["feature_ids"]
            + mapping["requirement_ids"]
            + mapping["decision_ids"]
        )
        if not set(mapped_ids) <= registered:
            issues.append(_issue("REGISTRY_ID", identity))
        validation = record["validation"]
        if validation["state"] == "passed":
            if not validation["artifact_paths"]:
                issues.append(_issue("PASS_ARTIFACT", identity))
            if validation["kind"] == "runtime" and not any(
                s["inspection_method"] == "black_box" for s in record["sources"]
            ):
                issues.append(_issue("PASS_RUNTIME_SOURCE", identity))
            for locator in validation["artifact_paths"]:
                if not resolve_locator(root, locator).is_file():
                    issues.append(_issue("PASS_ARTIFACT", identity))
    return issues


def validate_evidence(repository: Path) -> list[ValidationIssue]:
    """Validate both generations and global IDs without promoting history."""
    logger.debug("%s: begin", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    directory = resolve_locator(repository, EVIDENCE_DIRECTORY)
    ledger = cast("dict[str, Any]", read_json(directory / "reimplementation.json"))
    schema = cast(
        "dict[str, Any]", read_json(directory / "reimplementation.schema.json")
    )
    if _schema_errors(ledger, schema):
        return [_issue("LEDGER_SCHEMA")]
    history = ledger["historical_snapshot"]
    old_path = resolve_locator(repository, history["ledger_locator"])
    old_schema_path = resolve_locator(repository, history["schema_locator"])
    if (
        fingerprint(old_path) != history["ledger_sha256"]
        or fingerprint(old_schema_path) != history["schema_sha256"]
    ):
        return [_issue("HISTORY_HASH")]
    old = cast("dict[str, Any]", read_json(old_path))
    old_schema = cast("dict[str, Any]", read_json(old_schema_path))
    if _schema_errors(old, old_schema):
        return [_issue("HISTORY_SCHEMA")]
    issues: list[ValidationIssue] = []
    historical = old["records"]
    current = ledger["records"]
    if set(historical) & set(current):
        issues.append(_issue("RECORD_ID_COLLISION"))
    maximum = max(int(k.rsplit("-", 1)[1]) for k in historical)
    if history["maximum_id"] != maximum or any(
        int(k.rsplit("-", 1)[1]) <= maximum for k in current
    ):
        issues.append(_issue("RECORD_ID_ALLOCATION"))
    issues.extend(
        _source_checks(historical, old["source_catalog"], repository, current=False)
    )
    issues.extend(
        _source_checks(current, ledger["source_catalog"], repository, current=True)
    )
    issues.extend(_current_checks(current, repository))
    issues.extend(_relationships({**historical, **current}))
    logger.info(
        "%s: checked",
        LEDGER_FR,
        extra={
            "fr_id": LEDGER_FR,
            "historical": len(historical),
            "current": len(current),
        },
    )
    return issues


def validate_ownership(
    repository: Path, *, qualify_runtime: bool = False
) -> list[ValidationIssue]:
    """Validate proposal coverage; refuse runtime qualification across gaps."""
    logger.debug("%s: begin", OWNER_FR, extra={"fr_id": OWNER_FR})
    directory = resolve_locator(repository, EVIDENCE_DIRECTORY)
    manifest = load_manifest(directory / "p00-inventory.json")
    ownership = cast("dict[str, Any]", read_json(directory / "p00-ownership.json"))
    issues = []
    proposals = ownership["feature_proposals"]
    if {p["feature_id"] for p in proposals} != {
        a.feature_id for a in manifest.artifacts
    } or len(proposals) != len(manifest.artifacts):
        issues.append(_issue("OWNER_FEATURE_SET"))
    for proposal in proposals:
        artifact = next(
            (a for a in manifest.artifacts if a.locator == proposal["artifact"]), None
        )
        if (
            artifact is None
            or artifact.feature_id != proposal["feature_id"]
            or artifact.phase != proposal["phase"]
            or proposal["registration_status"] != "proposed"
        ):
            issues.append(_issue("OWNER_FEATURE_MAPPING"))
    issues.extend(_roadmap_checks(repository, manifest, ownership))
    resources = ownership["resource_proposals"]
    if len(resources) != len(manifest.resources) or {
        r["locator"] for r in resources
    } != {r.locator for r in manifest.resources}:
        issues.append(_issue("OWNER_RESOURCE_SET"))
    for registry in ownership["existing_ui_registries"]:
        path = resolve_locator(repository, registry["readme"])
        if fingerprint(path) != registry["sha256"]:
            issues.append(_issue("UI_REGISTRY_DRIFT"))
    if ownership["runtime_qualified"] is not False or qualify_runtime:
        logger.error("%s: runtime blocked", OWNER_FR, extra={"fr_id": OWNER_FR})
        issues.append(ValidationIssue("RUNTIME_AUTHORITY_BLOCKED"))
    logger.warning(
        "%s: unresolved runtime authority",
        OWNER_FR,
        extra={"fr_id": OWNER_FR, "gaps": len(ownership["gaps"])},
    )
    logger.info("%s: proposals checked", OWNER_FR, extra={"fr_id": OWNER_FR})
    return issues


def _roadmap_checks(
    repository: Path, manifest: Manifest, ownership: dict[str, Any]
) -> list[ValidationIssue]:
    """Reconcile exact immutable roadmap allocations and seed declarations."""
    logger.debug("%s: roadmap", OWNER_FR, extra={"fr_id": OWNER_FR})
    issues = []
    seeds = ownership["requirement_seeds"]
    roadmap = resolve_locator(repository, manifest.roadmap.locator).read_text(
        encoding="utf-8"
    )
    if (
        fingerprint(resolve_locator(repository, manifest.roadmap.locator))
        != manifest.roadmap.sha256
    ):
        issues.append(_issue("ROADMAP_HASH"))
    expected_archives = set(
        re.findall(
            r"\| `((?:internal/[^`]+|j64/[^`]+)\.jar)` \| `(FEAT-[A-Z0-9-]+)` \| (P[0-9]{2}) \| ([0-9]+) \|[^\n]+?`([0-9a-f]{64})` \|",
            roadmap,
        )
    )
    actual_archives = {
        (a.locator, a.feature_id, a.phase, str(a.class_count), a.sha256)
        for a in manifest.artifacts
    }
    if actual_archives != expected_archives:
        issues.append(_issue("OWNER_ARCHIVE_ALLOCATION"))
    expected_seeds = set(
        re.findall(
            r"\| `(FEAT-[A-Z0-9-]+)` \| `(FR-[A-Z0-9-]+)` \| `([^`]+)` \| (\w+) \|",
            roadmap,
        )
    )
    actual_seeds = {
        (s["feature_id"], s["requirement_id"], s["donor_symbol"], s["kind"])
        for s in seeds
    }
    if actual_seeds != expected_seeds or len(seeds) != len(actual_seeds):
        issues.append(_issue("OWNER_SEED_SET"))
    return issues


def _fixture_checks(repository: Path, ledger: dict[str, Any]) -> list[ValidationIssue]:
    """Bind fixtures to current registered, fingerprinted static observations."""
    logger.debug("%s: fixture links", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    cases = load_fixtures(repository / "tests/reference/p00-fixtures.json").cases
    registered = _registry_ids(repository / "app/host/README.md")
    issues = []
    for case in cases:
        if not {case.feature_id, case.requirement_id, *case.decision_ids} <= registered:
            issues.append(_issue("FIXTURE_REGISTRY_ID"))
        if not set(case.evidence_ids) <= set(ledger["records"]):
            issues.append(_issue("FIXTURE_RECORD_LINK"))
            continue
        if not resolve_locator(repository, case.capture_artifact).is_file():
            issues.append(_issue("FIXTURE_CAPTURE_ARTIFACT"))
        sources = [
            s
            for identity in case.evidence_ids
            for s in ledger["records"][identity]["sources"]
        ]
        if not any(
            s["artifact_locator"] == case.artifact
            and s["fingerprint"] is not None
            and s["fingerprint"]["value"] == case.artifact_sha256
            for s in sources
        ):
            issues.append(_issue("FIXTURE_SOURCE_HASH"))
    return issues


def main(argv: list[str] | None = None) -> int:
    """Qualify repository evidence; optionally inspect explicit donor roots."""
    logger.info("%s: begin", CLI_FR, extra={"fr_id": CLI_FR})
    parser = argparse.ArgumentParser(description="Qualify P00 evidence infrastructure")
    parser.add_argument("--check-donor", action="store_true")
    arguments = parser.parse_args(argv)
    repository = Path(__file__).resolve().parents[2]
    try:
        issues = validate_evidence(repository) + validate_ownership(repository)
        ledger = cast(
            "dict[str, Any]",
            read_json(repository / EVIDENCE_DIRECTORY / "reimplementation.json"),
        )
        issues.extend(_fixture_checks(repository, ledger))
        if arguments.check_donor:
            manifest = load_manifest(
                repository / EVIDENCE_DIRECTORY / "p00-inventory.json"
            )
            verify_inventory(manifest, resolve_roots(repository))
    except EvidenceError, OSError, KeyError, TypeError, ValueError:
        logger.error("%s: invalid evidence", CLI_FR, extra={"fr_id": CLI_FR})
        return 1
    if issues:
        logger.error(
            "%s: failed", CLI_FR, extra={"fr_id": CLI_FR, "issues": len(issues)}
        )
        return 1
    logger.info(
        "%s: static baseline valid; runtime blocked", CLI_FR, extra={"fr_id": CLI_FR}
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
