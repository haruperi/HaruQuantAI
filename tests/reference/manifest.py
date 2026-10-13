"""Validate bounded reference manifests and reconcile donor inventory.

Description:
    Reference qualification resolves explicitly supplied roots, reads bounded JSON,
    validates donor/repository artifact identities, and compares actual bytes and
    directory counts. Fixture and ledger validators reuse these safe reads; no
    donor executable or operational database is touched.

Purpose:
    FEAT-HOST-EVIDENCE: Preserve reference provenance and detect inventory drift.
    Implements DEC-HOST-P00-BOUNDED-FIXTURES, DEC-HOST-P00-LOGGING-ADAPTER, and
    DEC-HOST-P00-RELEASE-GATES as independently tested tooling.

Key Capabilities:
    - FR-HOST-EVIDENCE-ROOT-RESOLUTION: Resolve roots and contain logical locators.
      Associated: `ReferenceRoots`, `resolve_roots()`, `resolve_locator()`,
      `logical_locator()`, `repository_source()`
      Logging: DEBUG records logical resolution; INFO records accepted roots;
      ERROR records stable failure codes without physical paths.
    - FR-HOST-EVIDENCE-MANIFEST-VALIDATION: Read JSON and validate typed identities.
      Associated: `ResourceFile`, `DonorArtifact`, `Manifest`, `read_json()`,
      `load_manifest()`, `timestamp()`
      Logging: DEBUG records validation; INFO records counts; ERROR records codes.
    - FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION: Compare donor/repository bytes.
      Associated: `fingerprint()`, `verify_inventory()`
      Logging: DEBUG records hashing; INFO records verified totals; ERROR records
      drift or missing files.

Python API Usage:
    ```python
    from pathlib import Path
    from tests.reference.manifest import (
        load_manifest,
        resolve_roots,
        verify_inventory,
    )

    roots = resolve_roots(Path.cwd())
    manifest = load_manifest(Path("docs/dev/evidence/p00-inventory.json"))
    verify_inventory(manifest, roots)
    ```

CLI Usage:
    ```bash
    uv run python -m tests.reference.validate --check-donor
    ```
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from logging import Logger
from logging import getLogger as get_logger  # noqa: N813 - approved adapter name
from pathlib import Path
from typing import Literal, Never, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ValidationError,
    field_validator,
)

logger = get_logger(__name__)
MAX_JSON_BYTES = 4 * 1024 * 1024
ROOT_FR = "FR-HOST-EVIDENCE-ROOT-RESOLUTION"
MANIFEST_FR = "FR-HOST-EVIDENCE-MANIFEST-VALIDATION"
INVENTORY_FR = "FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION"
ReferenceCohort = Literal["145-dev1"]
ArtifactFamily = Literal[
    "config", "documentation", "encrypted_jar", "library", "xml_template"
]


class EvidenceError(ValueError):
    """A stable diagnostic code without sensitive input or physical paths."""


def fail(fr: str, code: str, *, event_logger: Logger | None = None) -> Never:
    """Emit the owning FR failure and raise a stable diagnostic."""
    target = logger if event_logger is None else event_logger
    target.error("%s: %s", fr, code, extra={"fr_id": fr, "code": code})
    raise EvidenceError(code)


def timestamp(value: str) -> str:
    """Require an ISO timestamp with an explicit UTC offset."""
    logger.debug("%s: timestamp", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        fail(MANIFEST_FR, "TIMESTAMP_INVALID")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail(MANIFEST_FR, "TIMESTAMP_NAIVE")
    return value


def logical_locator(value: str) -> str:
    """Require a canonical relative forward-slash locator."""
    logger.debug("%s: locator", ROOT_FR, extra={"fr_id": ROOT_FR})
    if (
        not value
        or any(ord(char) < 32 for char in value)
        or "\\" in value
        or ":" in value
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        fail(ROOT_FR, "LOCATOR_INVALID")
    return value


def resolve_locator(root: Path, locator: str) -> Path:
    """Resolve a locator, rejecting links escaping the explicitly supplied root."""
    logger.debug("%s: containment", ROOT_FR, extra={"fr_id": ROOT_FR})
    logical_locator(locator)
    try:
        base = root.resolve(strict=True)
        target = (base / locator).resolve()
    except OSError, RuntimeError:
        fail(ROOT_FR, "ROOT_INVALID")
    if not target.is_relative_to(base):
        fail(ROOT_FR, "LOCATOR_ESCAPE")
    return target


@dataclass(frozen=True, slots=True)
class ReferenceRoots:
    """Resolved repository and donor roots for read-only inventory checks."""

    repository: Path
    donor: Path
    cohort: ReferenceCohort = "145-dev1"


def resolve_roots(
    repository: Path,
    donor: Path | None = None,
    *,
    cohort: ReferenceCohort = "145-dev1",
) -> ReferenceRoots:
    """Resolve explicit roots; never search the machine or invent a fallback."""
    logger.debug("%s: resolve", ROOT_FR, extra={"fr_id": ROOT_FR})
    if cohort != "145-dev1":
        fail(ROOT_FR, "COHORT_UNKNOWN")
    if donor is None:
        configured = os.environ.get("SQX_REFERENCE_ROOT") or os.environ.get(
            "SQX_145_REFERENCE_ROOT"
        )
        if not configured:
            fail(ROOT_FR, "ROOT_UNRESOLVED")
        donor = Path(configured)
    try:
        repo = repository.resolve(strict=True)
        source = donor.resolve(strict=True)
    except OSError, RuntimeError:
        fail(ROOT_FR, "ROOT_INVALID")
    if not repo.is_dir() or not source.is_dir() or source == repo:
        fail(ROOT_FR, "ROOT_INVALID")
    logger.info("%s: logical roots resolved", ROOT_FR, extra={"fr_id": ROOT_FR})
    return ReferenceRoots(repo, source, cohort)


def _pairs(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
    """Reject duplicate keys before a JSON object can discard evidence."""
    logger.debug("%s: JSON keys", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            fail(MANIFEST_FR, "JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _constant(_value: str) -> Never:
    """Reject JSON NaN and infinity tokens without logging their content."""
    fail(MANIFEST_FR, "JSON_NONFINITE")


def _finite_float(value: str) -> float:
    """Reject exponent overflow as well as explicit nonfinite tokens."""
    logger.debug("%s: JSON float", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    result = float(value)
    if not math.isfinite(result):
        fail(MANIFEST_FR, "JSON_NONFINITE")
    return result


def read_json(path: Path, *, limit: int = MAX_JSON_BYTES) -> dict[str, JsonValue]:
    """Read a bounded UTF-8 JSON object with no duplicate or nonfinite values."""
    logger.debug("%s: read JSON", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    if type(limit) is not int or limit < 1 or limit > MAX_JSON_BYTES:
        fail(MANIFEST_FR, "JSON_LIMIT_INVALID")
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        fail(MANIFEST_FR, "JSON_READ_FAILED")
    if len(data) > limit:
        fail(MANIFEST_FR, "JSON_TOO_LARGE")
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
            parse_float=_finite_float,
        )
    except UnicodeError, json.JSONDecodeError, RecursionError:
        fail(MANIFEST_FR, "JSON_INVALID")
    if not isinstance(value, dict):
        fail(MANIFEST_FR, "JSON_OBJECT_REQUIRED")
    return cast("dict[str, JsonValue]", value)


def fingerprint(path: Path) -> str:
    """Hash bytes through a read-only bounded-memory stream."""
    logger.debug("%s: fingerprint", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    try:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    except OSError:
        fail(INVENTORY_FR, "ARTIFACT_READ_FAILED")


class ResourceFile(BaseModel):
    """A source locator and its exact observed SHA-256 fingerprint."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    locator: str = Field(strict=True)
    sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    _locator = field_validator("locator")(logical_locator)


def repository_source(repository: Path, source: ResourceFile) -> Path:
    """Resolve current bytes and reject drift; never use a substitute source."""
    logger.debug("%s: repository source", ROOT_FR, extra={"fr_id": ROOT_FR})
    path = resolve_locator(repository, source.locator)
    if fingerprint(path) != source.sha256:
        fail(INVENTORY_FR, "SOURCE_HASH")
    return path


class DonorArtifact(ResourceFile):
    """An inspected donor file's identity, family, and target stage allocation."""

    family: ArtifactFamily
    stage: str = Field(strict=True, pattern=r"^Stage [0-7]$")
    proposed_feature_id: str = Field(strict=True, pattern=r"^FEAT-[A-Z]+-[A-Z0-9-]+$")


class Manifest(BaseModel):
    """A versioned static reference manifest for SQX-145 and repository sources."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: int = Field(strict=True, ge=1, le=1)
    captured_at: str = Field(strict=True)
    reference_cohort: ReferenceCohort
    installed_build: None
    activation_status: Literal["unverified"]
    donor_artifacts: list[DonorArtifact] = Field(min_length=1)
    repository_sources: list[ResourceFile] = Field(min_length=1)
    totals: dict[str, int]
    _timestamp = field_validator("captured_at")(timestamp)


def load_manifest(path: Path) -> Manifest:
    """Validate manifest types, locator uniqueness, and summary totals."""
    logger.debug("%s: validate manifest", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    try:
        result = Manifest.model_validate(read_json(path))
    except ValidationError:
        fail(MANIFEST_FR, "MANIFEST_INVALID")
    donor_locs = [item.locator for item in result.donor_artifacts]
    repo_locs = [item.locator for item in result.repository_sources]
    if len(set(donor_locs)) != len(donor_locs) or len(set(repo_locs)) != len(repo_locs):
        fail(MANIFEST_FR, "MANIFEST_DUPLICATE")
    required_keys = {
        "donor_artifacts",
        "encrypted_jars",
        "xml_templates",
        "plugin_directories",
        "snippet_java_files",
    }
    if (
        set(result.totals) != required_keys
        or result.totals["donor_artifacts"] != len(result.donor_artifacts)
        or result.totals["encrypted_jars"]
        != sum(item.family == "encrypted_jar" for item in result.donor_artifacts)
        or result.totals["xml_templates"]
        != sum(item.family == "xml_template" for item in result.donor_artifacts)
        or result.totals["plugin_directories"] < 1
        or result.totals["snippet_java_files"] < 1
    ):
        fail(MANIFEST_FR, "MANIFEST_TOTALS")
    logger.info(
        "%s: accepted",
        MANIFEST_FR,
        extra={"fr_id": MANIFEST_FR, "donor_artifacts": len(result.donor_artifacts)},
    )
    return result


def verify_inventory(manifest: Manifest, roots: ReferenceRoots) -> None:
    """Reconcile repository and donor SHA-256 digests and directory counts."""
    logger.debug("%s: verify inventory", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    for source in manifest.repository_sources:
        repository_source(roots.repository, source)
    for artifact in manifest.donor_artifacts:
        target = resolve_locator(roots.donor, artifact.locator)
        if fingerprint(target) != artifact.sha256:
            fail(INVENTORY_FR, "DONOR_ARTIFACT_HASH")
    libs_dir = resolve_locator(roots.donor, "internal/libs")
    plugins_dir = resolve_locator(roots.donor, "internal/plugins")
    snippets_dir = resolve_locator(roots.donor, "internal/extend/Snippets/SQ")
    if not libs_dir.is_dir() or not plugins_dir.is_dir() or not snippets_dir.is_dir():
        fail(INVENTORY_FR, "DONOR_STRUCTURE_MISSING")
    enc_count = sum(1 for p in libs_dir.glob("*.jar.enc") if p.is_file())
    plugin_count = sum(1 for p in plugins_dir.iterdir() if p.is_dir())
    snippet_count = sum(1 for p in snippets_dir.rglob("*.java") if p.is_file())
    if (
        enc_count != manifest.totals["encrypted_jars"]
        or plugin_count != manifest.totals["plugin_directories"]
        or snippet_count != manifest.totals["snippet_java_files"]
    ):
        fail(INVENTORY_FR, "DONOR_COUNT_DRIFT")
    logger.info(
        "%s: inventory reconciled",
        INVENTORY_FR,
        extra={
            "fr_id": INVENTORY_FR,
            "donor_artifacts": len(manifest.donor_artifacts),
            "plugins": plugin_count,
        },
    )
