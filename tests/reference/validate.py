"""Validate the SQX-145 clean-room evidence ledger, ownership gates, and CLI.

Description:
    Offline and donor-bound reference qualification verifies schema compliance,
    monotonic `SQX145-EV-NNNNNN` record allocation, source catalog and SHA-256
    bindings, reciprocal supersession/contradiction graphs, domain registry
    mappings, and fixture provenance before any application stage executes.

Purpose:
    FEAT-HOST-EVIDENCE: Enforce clean-room evidence integrity and ownership gates.
    Implements DEC-HOST-P00-SCHEMA-EVOLUTION, DEC-HOST-P00-REGISTRY-BOUNDARY,
    DEC-HOST-P00-VALIDATION-DEPENDENCY, and DEC-HOST-SQX145-REFERENCE.

Key Capabilities:
    - FR-HOST-EVIDENCE-LEDGER-INTEGRITY: Validate schema v4, sources, and links.
      Associated: `ValidationIssue`, `validate_evidence()`
      Logging: DEBUG records validation phases; INFO records checked record count;
      ERROR records stable diagnostic codes without physical paths.
    - FR-HOST-EVIDENCE-OWNERSHIP-GATES: Verify registry mappings and runtime gate.
      Associated: `validate_ownership()`
      Logging: DEBUG records ownership checks; WARNING records unresolved runtime
      authority; INFO records completion; ERROR records blocked runtime claims.
    - FR-HOST-EVIDENCE-QUALIFICATION-CLI: Run offline and `--check-donor` checks.
      Associated: `main()`
      Logging: INFO records CLI start and valid static baseline; ERROR records
      validation failures and nonzero exit codes.

Python API Usage:
    ```python
    from pathlib import Path
    from tests.reference.validate import validate_evidence, validate_ownership

    repo = Path.cwd()
    issues = validate_evidence(repo) + validate_ownership(repo)
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

from jsonschema import Draft202012Validator

from tests.reference.fixtures import load_fixtures
from tests.reference.manifest import (
    EvidenceError,
    fingerprint,
    load_manifest,
    read_json,
    repository_source,
    resolve_locator,
    resolve_roots,
    verify_inventory,
)

logger = get_logger(__name__)
EVIDENCE_DIRECTORY = "docs/dev/evidence"
LEDGER_FR = "FR-HOST-EVIDENCE-LEDGER-INTEGRITY"
OWNER_FR = "FR-HOST-EVIDENCE-OWNERSHIP-GATES"
CLI_FR = "FR-HOST-EVIDENCE-QUALIFICATION-CLI"
LOCATION_KEYS = ("section", "symbol", "line_range", "json_pointer", "xpath")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A stable validation failure code and optional offending record ID."""

    code: str
    record_id: str | None = None


def _issue(code: str, record_id: str | None = None) -> ValidationIssue:
    """Log a structured ledger error and return the corresponding issue."""
    logger.error(
        "%s: %s",
        LEDGER_FR,
        code,
        extra={"fr_id": LEDGER_FR, "code": code, "record_id": record_id},
    )
    return ValidationIssue(code, record_id)


def _registry_ids(readme: Path) -> set[str]:
    """Extract registered FEAT-*, FR-*, and DEC-* tokens from a domain README."""
    text = readme.read_text(encoding="utf-8")
    return set(re.findall(r"`((?:FEAT|FR|DEC)-[A-Z0-9-]+)`", text))


def _matches_catalog_locator(locator: str, allowed: list[str]) -> bool:
    """Check whether an artifact locator falls under a catalog entry's locators."""
    return any(
        locator == prefix or locator.startswith(f"{prefix}/") for prefix in allowed
    )


def _check_allocation(ledger: dict[str, Any]) -> list[ValidationIssue]:
    """Verify monotonic SQX145-EV-NNNNNN numbers and high-water mark."""
    floor = int(ledger["minimum_record_number"])
    high_water = int(ledger["allocation_high_water_mark"])
    numbers = [int(key.rsplit("-", 1)[1]) for key in ledger["records"]]
    if (
        not numbers
        or min(numbers) < floor
        or max(numbers) > high_water
        or max(numbers) != high_water
        or len(set(numbers)) != len(numbers)
    ):
        return [_issue("RECORD_ID_ALLOCATION")]
    return []


def _check_source(
    repository: Path,
    identity: str,
    source: dict[str, Any],
    catalogs: dict[str, Any],
    donor_hashes: dict[str, str],
) -> list[ValidationIssue]:
    """Validate one source reference against catalog, location, and SHA-256."""
    catalog = catalogs.get(source["catalog_id"])
    if catalog is None:
        return [_issue("SOURCE_CATALOG", identity)]
    if all(source["location"].get(k) is None for k in LOCATION_KEYS):
        return [_issue("SOURCE_LOCATION", identity)]
    locator = str(source["artifact_locator"])
    is_repo = catalog["root"] == "HARUQUANTAI_ROOT"
    target = resolve_locator(repository, locator) if is_repo else None
    if not _matches_catalog_locator(locator, list(catalog["locators"])) or (
        target is not None and not target.is_file()
    ):
        return [_issue("SOURCE_LOCATOR", identity)]
    pin = source["fingerprint"]
    if target is not None and (pin is None or fingerprint(target) != pin["value"]):
        return [_issue("SOURCE_HASH", identity)]
    if catalog["root"] == "SQX_REFERENCE_ROOT" and (
        pin is None or donor_hashes.get(locator) != pin["value"]
    ):
        return [_issue("SOURCE_DONOR_BINDING", identity)]
    return []


def _check_mapping(
    identity: str, mapping: dict[str, Any], registered: set[str]
) -> list[ValidationIssue]:
    """Validate target_mapping registration status and registered IDs."""
    status = mapping["registration_status"]
    feats = list(mapping["feature_ids"])
    reqs = list(mapping["requirement_ids"])
    decs = list(mapping["decision_ids"])
    if status == "registered":
        if (
            not feats
            or not reqs
            or mapping["proposed_owner"] is not None
            or mapping["proposed_feature_id"] is not None
            or mapping["proposed_requirement_ids"]
            or mapping["proposed_decision_ids"]
        ):
            return [_issue("PROPOSED_MAPPING", identity)]
        if not ({*feats, *reqs, *decs} <= registered):
            return [_issue("REGISTRY_ID", identity)]
        return []
    if (
        not mapping["proposed_owner"]
        or not mapping["proposed_feature_id"]
        or feats
        or reqs
    ):
        return [_issue("PROPOSED_MAPPING", identity)]
    return []


def _check_validation_block(
    repository: Path,
    identity: str,
    record: dict[str, Any],
    catalogs: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate artifact paths and runtime provenance for passed records."""
    val = record["validation"]
    if val["state"] != "passed":
        return []
    for rel_path in val["artifact_paths"]:
        if not resolve_locator(repository, str(rel_path)).is_file():
            return [_issue("PASS_ARTIFACT", identity)]
    if val["kind"] == "runtime" and not any(
        catalogs.get(s["catalog_id"], {}).get("kind") == "runtime_observation"
        for s in record["sources"]
    ):
        return [_issue("PASS_RUNTIME_SOURCE", identity)]
    return []


def _check_supersession_chain(
    identity: str, later: str | None, records: dict[str, Any]
) -> list[ValidationIssue]:
    """Check reciprocal supersession links and detect supersession cycles."""
    if later is not None and (
        later not in records
        or identity not in records[later]["relationships"]["supersedes_records"]
    ):
        return [_issue("SUPERSESSION_RECIPROCAL", identity)]
    seen: set[str] = set()
    cursor = later
    while isinstance(cursor, str) and cursor in records:
        if cursor == identity or cursor in seen:
            return [_issue("SUPERSESSION_CYCLE", identity)]
        seen.add(cursor)
        cursor = records[cursor]["relationships"]["superseded_by"]
    return []


def _check_relationships(records: dict[str, Any]) -> list[ValidationIssue]:
    """Verify record link resolution, reciprocity, and supersession acyclicity."""
    issues: list[ValidationIssue] = []
    for identity, record in records.items():
        links = record["relationships"]
        for field in ("supports_records", "contradicts_records", "supersedes_records"):
            for target in links[field]:
                if target not in records or target == identity:
                    issues.append(_issue("RECORD_LINK", identity))
        for peer in links["contradicts_records"]:
            if peer in records and (
                identity not in records[peer]["relationships"]["contradicts_records"]
            ):
                issues.append(_issue("CONTRADICTION_RECIPROCAL", identity))
        for earlier in links["supersedes_records"]:
            if earlier in records and (
                records[earlier]["relationships"]["superseded_by"] != identity
            ):
                issues.append(_issue("SUPERSESSION_RECIPROCAL", identity))
        issues.extend(
            _check_supersession_chain(identity, links["superseded_by"], records)
        )
    return issues


def validate_evidence(repository: Path) -> list[ValidationIssue]:
    """Validate reimplementation.json against schema v4 and repository truth."""
    logger.debug("%s: begin", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    directory = resolve_locator(repository, EVIDENCE_DIRECTORY)
    schema = cast(
        "dict[str, Any]", read_json(directory / "reimplementation.schema.json")
    )
    ledger = cast("dict[str, Any]", read_json(directory / "reimplementation.json"))
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    if list(validator.iter_errors(ledger)):
        return [_issue("LEDGER_SCHEMA")]
    issues = _check_allocation(ledger)
    manifest = load_manifest(directory / "p00-inventory.json")
    donor_hashes = {item.locator: item.sha256 for item in manifest.donor_artifacts}
    registered = _registry_ids(resolve_locator(repository, "app/host/README.md"))
    catalogs = cast("dict[str, Any]", ledger["source_catalog"])
    records = cast("dict[str, Any]", ledger["records"])
    for identity, record in records.items():
        for source in record["sources"]:
            issues.extend(
                _check_source(repository, identity, source, catalogs, donor_hashes)
            )
        issues.extend(_check_mapping(identity, record["target_mapping"], registered))
        issues.extend(_check_validation_block(repository, identity, record, catalogs))
    issues.extend(_check_relationships(records))
    logger.info(
        "%s: checked current records",
        LEDGER_FR,
        extra={"fr_id": LEDGER_FR, "records": len(records)},
    )
    return issues


def validate_ownership(
    repository: Path, *, qualify_runtime: bool = False
) -> list[ValidationIssue]:
    """Validate manifest repository sources and refuse premature runtime parity."""
    logger.debug("%s: begin", OWNER_FR, extra={"fr_id": OWNER_FR})
    directory = resolve_locator(repository, EVIDENCE_DIRECTORY)
    manifest = load_manifest(directory / "p00-inventory.json")
    issues: list[ValidationIssue] = []
    for source in manifest.repository_sources:
        try:
            repository_source(repository, source)
        except EvidenceError as error:
            issues.append(ValidationIssue(str(error)))
    if qualify_runtime:
        logger.error("%s: runtime blocked", OWNER_FR, extra={"fr_id": OWNER_FR})
        issues.append(ValidationIssue("RUNTIME_AUTHORITY_BLOCKED"))
    logger.warning(
        "%s: unresolved runtime authority",
        OWNER_FR,
        extra={"fr_id": OWNER_FR, "donor_artifacts": len(manifest.donor_artifacts)},
    )
    logger.info("%s: ownership checked", OWNER_FR, extra={"fr_id": OWNER_FR})
    return issues


def _fixture_checks(repository: Path, ledger: dict[str, Any]) -> list[ValidationIssue]:
    """Bind fixtures to registered identities and fingerprinted evidence records."""
    logger.debug("%s: fixture links", LEDGER_FR, extra={"fr_id": LEDGER_FR})
    cases = load_fixtures(
        resolve_locator(repository, "tests/reference/p00-fixtures.json")
    ).cases
    registered = _registry_ids(resolve_locator(repository, "app/host/README.md"))
    issues: list[ValidationIssue] = []
    for case in cases:
        if not (
            {case.feature_id, case.requirement_id, *case.decision_ids} <= registered
        ):
            issues.append(_issue("FIXTURE_REGISTRY_ID"))
        if not (set(case.evidence_ids) <= set(ledger["records"])):
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
    """Qualify repository evidence; optionally reconcile explicit donor roots."""
    logger.info("%s: begin", CLI_FR, extra={"fr_id": CLI_FR})
    parser = argparse.ArgumentParser(description="Qualify Stage 0 evidence ledger")
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
