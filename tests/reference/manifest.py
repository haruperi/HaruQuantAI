"""Validate bounded reference manifests and reconcile donor inventory.

Description:
    Reference qualification resolves explicitly supplied roots, reads bounded JSON,
    validates archive/resource identities, and compares actual donor bytes. Fixture
    and ledger tools reuse these safe reads; no donor or database is executed.
    Typed models describe observations; they do not confer runtime authority.

Purpose:
    FEAT-HOST-EVIDENCE: Preserve reference provenance and detect inventory drift.
    Implements DEC-HOST-P00-BOUNDED-FIXTURES, DEC-HOST-P00-LOGGING-ADAPTER and
    DEC-HOST-P00-RELEASE-GATES as independently tested tooling.

Key Capabilities:
    - FR-HOST-EVIDENCE-ROOT-RESOLUTION: Resolve roots and contain logical locators.
      Associated: `ReferenceRoots`, `resolve_roots()`, `resolve_locator()`
      and `repository_source()` for exact current document fingerprints.
      Logging: DEBUG records logical resolution; ERROR records stable failure codes.
    - FR-HOST-EVIDENCE-MANIFEST-VALIDATION: Read JSON and validate typed identities.
      Associated: `Artifact`, `ResourceFile`, `Resource`, `Manifest`, `load_manifest()`
      and typed current archive/member index models.
      Logging: DEBUG records validation; INFO records counts; ERROR records codes.
    - FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION: Compare archive/resource bytes.
      Associated: `fingerprint()`, `verify_inventory()`, `reconcile_metadata()`
      Logging: DEBUG records hashing; INFO records totals; ERROR records drift.
      Private parsing, containment and failure helpers log their owning FR as well.

Python API Usage:
    ```python
    from pathlib import Path
    from tests.reference.manifest import load_manifest, resolve_roots, verify_inventory

    roots = resolve_roots(Path.cwd())  # Explicit SQX_145_REFERENCE_ROOT environment.
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
import re
import zipfile
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


class EvidenceError(ValueError):
    """A stable diagnostic code without sensitive input or exception payloads."""


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


@dataclass(frozen=True)
class ReferenceRoots:
    """Resolved repository/donor authority for read-only inventory checks."""

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
    variable = "SQX_145_REFERENCE_ROOT"
    configured = os.environ.get(variable) if donor is None else None
    if donor is None:
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
    """Read a bounded UTF-8 JSON object with no duplicate/nonfinite values."""
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


class Artifact(ResourceFile):
    """An installed archive's observed identity and proposed phase allocation."""

    class_count: int = Field(strict=True, ge=0)
    family: Literal["library", "plugin", "runtime"]
    feature_id: str = Field(strict=True, pattern=r"^FEAT-[A-Z]+-[A-Z0-9-]+$")
    phase: str = Field(strict=True, pattern=r"^P(?:0[0-9]|1[0-9])$")


class Resource(BaseModel):
    """A resource-only directory, including its complete observed file set."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    locator: str = Field(strict=True)
    feature_id: str = Field(strict=True, pattern=r"^FEAT-[A-Z]+-[A-Z0-9-]+$")
    requirement_id: str = Field(strict=True, pattern=r"^FR-[A-Z]+-[A-Z0-9-]+$")
    phase: str = Field(strict=True, pattern=r"^P(?:0[0-9]|1[0-9])$")
    files: list[ResourceFile]
    activation_status: Literal["unverified"]
    _locator = field_validator("locator")(logical_locator)


class Manifest(BaseModel):
    """A versioned static observation; activation/build may remain unavailable."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: int = Field(strict=True, ge=1, le=1)
    captured_at: str = Field(strict=True)
    reference_cohort: ReferenceCohort
    installed_build: None
    activation_status: Literal["unverified"]
    source_head: str = Field(strict=True, pattern=r"^[0-9a-f]{40}$")
    roadmap: ResourceFile
    artifacts: list[Artifact]
    resources: list[Resource]
    totals: dict[str, int]
    _timestamp = field_validator("captured_at")(timestamp)


def load_manifest(path: Path) -> Manifest:
    """Validate manifest types, identity uniqueness, counts and resource bounds."""
    logger.debug("%s: validate manifest", MANIFEST_FR, extra={"fr_id": MANIFEST_FR})
    try:
        result = Manifest.model_validate(read_json(path))
    except ValidationError:
        fail(MANIFEST_FR, "MANIFEST_INVALID")
    locators = [a.locator for a in result.artifacts]
    features = [a.feature_id for a in result.artifacts]
    dirs = [r.locator for r in result.resources]
    if (
        len(set(locators)) != len(locators)
        or len(set(features)) != len(features)
        or len(set(dirs)) != len(dirs)
        or set(dirs) & set(locators)
    ):
        fail(MANIFEST_FR, "MANIFEST_DUPLICATE")
    for resource in result.resources:
        names = [f.locator for f in resource.files]
        if len(set(names)) != len(names) or any(
            not n.startswith(resource.locator + "/") or n.endswith(".jar")
            for n in names
        ):
            fail(MANIFEST_FR, "RESOURCE_INVALID")
    totals = {
        "archives": len(result.artifacts),
        "classes": sum(a.class_count for a in result.artifacts),
        "resources": len(result.resources),
        **{
            family: sum(a.family == family for a in result.artifacts)
            for family in ("library", "plugin", "runtime")
        },
    }
    if result.totals != totals:
        fail(MANIFEST_FR, "MANIFEST_TOTALS")
    logger.info(
        "%s: accepted",
        MANIFEST_FR,
        extra={"fr_id": MANIFEST_FR, "archives": len(result.artifacts)},
    )
    return result


def _verify_archives(artifacts: list[Artifact], donor: Path) -> None:
    """Compare each exact archive identity and observed class-entry count."""
    logger.debug("%s: archives", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    for artifact in artifacts:
        path = resolve_locator(donor, artifact.locator)
        if fingerprint(path) != artifact.sha256:
            fail(INVENTORY_FR, "INVENTORY_HASH")
        try:
            with zipfile.ZipFile(path) as archive:
                count = sum(n.endswith(".class") for n in archive.namelist())
        except OSError, zipfile.BadZipFile:
            fail(INVENTORY_FR, "INVENTORY_ARCHIVE_INVALID")
        if count != artifact.class_count:
            fail(INVENTORY_FR, "INVENTORY_CLASSES")


def _verify_resources(resources: list[Resource], donor: Path) -> None:
    """Compare complete directory/file sets and resource fingerprints."""
    logger.debug("%s: resources", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    plugin_root = donor / "internal/plugins"
    actual_dirs = (
        {
            p.relative_to(donor).as_posix()
            for p in plugin_root.iterdir()
            if p.is_dir() and not list(p.rglob("*.jar"))
        }
        if plugin_root.is_dir()
        else set()
    )
    if actual_dirs != {r.locator for r in resources}:
        fail(INVENTORY_FR, "INVENTORY_RESOURCE_SET")
    for resource in resources:
        directory = resolve_locator(donor, resource.locator)
        actual_names = {
            p.relative_to(donor).as_posix() for p in directory.rglob("*") if p.is_file()
        }
        if actual_names != {f.locator for f in resource.files}:
            fail(INVENTORY_FR, "INVENTORY_RESOURCE_FILES")
        for entry in resource.files:
            if fingerprint(resolve_locator(donor, entry.locator)) != entry.sha256:
                fail(INVENTORY_FR, "INVENTORY_RESOURCE_HASH")


def verify_inventory(manifest: Manifest, roots: ReferenceRoots) -> None:
    """Compare complete scoped archive/resource file sets, hashes and counts."""
    logger.debug("%s: verify", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    if roots.cohort != manifest.reference_cohort:
        fail(INVENTORY_FR, "COHORT_MISMATCH")
    expected = {a.locator for a in manifest.artifacts}
    files = (
        list((roots.donor / "internal/libs").glob("*.jar"))
        + list((roots.donor / "internal/plugins").rglob("*.jar"))
        + list((roots.donor / "j64/lib").glob("jrt-fs.jar"))
    )
    if {p.relative_to(roots.donor).as_posix() for p in files} != expected:
        fail(INVENTORY_FR, "INVENTORY_ARCHIVE_SET")
    _verify_archives(manifest.artifacts, roots.donor)
    _verify_resources(manifest.resources, roots.donor)
    if fingerprint(repository_source(roots.repository, manifest.roadmap)) != (
        manifest.roadmap.sha256
    ):
        fail(INVENTORY_FR, "ROADMAP_HASH")
    logger.info(
        "%s: reconciled",
        INVENTORY_FR,
        extra={"fr_id": INVENTORY_FR, "archives": len(expected)},
    )


class ClassOccurrence(BaseModel):
    """One exact raw class occurrence, including duplicate ZIP entries."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    entry: str
    occurrence: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    member_shard: str
    _paths = field_validator("entry", "member_shard")(logical_locator)


class ArchiveIndex(BaseModel):
    """Current archive entry fingerprints and complete member-shard bindings."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    captured_at: str
    root: Literal["SQX_145_REFERENCE_ROOT"]
    artifact_locator: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    class_count: int = Field(ge=0)
    unique_class_entries: int = Field(ge=0)
    resource_count: int = Field(ge=0)
    duplicate_entries: list[str]
    classes: dict[str, str]
    resources: dict[str, str]
    class_occurrences: list[ClassOccurrence]
    member_shards: list[ResourceFile]
    _locator = field_validator("artifact_locator")(logical_locator)
    _timestamp = field_validator("captured_at")(timestamp)


class DeclaredMember(BaseModel):
    """Observed JVM member metadata without code or constant-pool text."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    name: str = Field(min_length=1)
    descriptor: str = Field(min_length=1)
    access: int = Field(ge=0)
    generic_signature: str | None = None
    code_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    code_length: int | None = Field(default=None, ge=0)
    throws: list[str] = Field(default_factory=list)


class ClassDeclaration(BaseModel):
    """One class payload's declared members, hierarchy and reference names."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    entry: str
    occurrence: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    name: str = Field(min_length=1)
    major: int = Field(ge=45)
    minor: int = Field(ge=0)
    access: int = Field(ge=0)
    superclass: str | None
    interfaces: list[str]
    fields: list[DeclaredMember]
    methods: list[DeclaredMember]
    generic_signature: str | None = None
    class_references: list[str]
    _entry = field_validator("entry")(logical_locator)


class MemberShard(BaseModel):
    """A bounded metadata shard tied to one current archive fingerprint."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1]
    reference_cohort: ReferenceCohort
    root: Literal["SQX_145_REFERENCE_ROOT"]
    artifact_locator: str
    archive_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    captured_at: str
    classes: list[ClassDeclaration] = Field(min_length=1)
    _locator = field_validator("artifact_locator")(logical_locator)
    _timestamp = field_validator("captured_at")(timestamp)


class Metadata(BaseModel):
    """Complete current inventory/index/member bindings; no fallback sources."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1]
    reference_cohort: ReferenceCohort
    manifest: ResourceFile
    class_indices: list[ResourceFile]
    member_shards: list[ResourceFile]
    coexisting_policy: Literal["unverified_classpath_no_automatic_alias"]


def _bound_file(repository: Path, source: ResourceFile) -> Path:
    """Read a current source only after checking its byte fingerprint."""
    logger.debug("%s: bound source", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    return repository_source(repository, source)


def _class_member_checks(
    row: ClassDeclaration,
    source: ResourceFile,
    expected: dict[tuple[str, int], tuple[str, str]],
    seen: set[tuple[str, int]],
) -> int:
    """Bind one declaration and verify paired code fingerprints and lengths."""
    logger.debug("%s: class members", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    key = (row.entry, row.occurrence)
    if key in seen or expected.get(key) != (row.sha256, source.locator):
        fail(INVENTORY_FR, "MEMBER_CLASS_BINDING")
    if not row.entry.endswith(row.name + ".class"):
        fail(INVENTORY_FR, "MEMBER_CLASS_NAME")
    for member in row.fields + row.methods:
        if (member.code_sha256 is None) != (member.code_length is None):
            fail(INVENTORY_FR, "MEMBER_CODE_BINDING")
    seen.add(key)
    return len(row.fields) + len(row.methods)


def _member_checks(repository: Path, index: ArchiveIndex) -> int:
    """Reconcile every raw occurrence with its typed declared-member metadata."""
    logger.debug("%s: members", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    expected = {
        (row.entry, row.occurrence): (row.sha256, row.member_shard)
        for row in index.class_occurrences
    }
    if len(expected) != len(index.class_occurrences):
        fail(INVENTORY_FR, "MEMBER_OCCURRENCE_DUPLICATE")
    seen: set[tuple[str, int]] = set()
    count = 0
    shard_names = [source.locator for source in index.member_shards]
    if len(shard_names) != len(set(shard_names)):
        fail(INVENTORY_FR, "MEMBER_SHARD_SET")
    for source in index.member_shards:
        try:
            shard = MemberShard.model_validate(
                read_json(_bound_file(repository, source))
            )
        except ValidationError:
            fail(MANIFEST_FR, "MEMBER_SHARD_INVALID")
        if (
            shard.artifact_locator != index.artifact_locator
            or shard.archive_sha256 != index.sha256
        ):
            fail(INVENTORY_FR, "MEMBER_SHARD_BINDING")
        for row in shard.classes:
            count += _class_member_checks(row, source, expected, seen)
    if seen != set(expected):
        fail(INVENTORY_FR, "MEMBER_CLASS_SET")
    return count


def _index_checks(index: ArchiveIndex, artifact: Artifact) -> None:
    """Validate class/resource counts, fingerprints and duplicate occurrences."""
    logger.debug("%s: index", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    duplicate_classes = sum(n.endswith(".class") for n in index.duplicate_entries)
    if (
        index.sha256 != artifact.sha256
        or index.class_count != artifact.class_count
        or index.unique_class_entries != len(index.classes)
        or index.class_count != len(index.classes) + duplicate_classes
        or index.resource_count != len(index.resources)
        or index.class_count != len(index.class_occurrences)
    ):
        fail(INVENTORY_FR, "CLASS_INDEX_BINDING")
    for expected_class, entries in ((True, index.classes), (False, index.resources)):
        for name, value in entries.items():
            logical_locator(name)
            if name.endswith(".class") != expected_class or not re.fullmatch(
                r"[0-9a-f]{64}", value
            ):
                fail(MANIFEST_FR, "CLASS_INDEX_INVALID")
    names: dict[str, list[ClassOccurrence]] = {}
    for row in index.class_occurrences:
        names.setdefault(row.entry, []).append(row)
    if set(names) != set(index.classes):
        fail(INVENTORY_FR, "CLASS_OCCURRENCE_SET")
    for name, rows in names.items():
        if (
            sorted(r.occurrence for r in rows) != list(range(len(rows)))
            or index.classes[name] != max(rows, key=lambda r: r.occurrence).sha256
        ):
            fail(INVENTORY_FR, "CLASS_OCCURRENCE_BINDING")
    if sorted(n for n, rows in names.items() for _ in rows[1:]) != sorted(
        n for n in index.duplicate_entries if n.endswith(".class")
    ):
        fail(INVENTORY_FR, "CLASS_DUPLICATE_BINDING")


def reconcile_metadata(repository: Path, path: Path) -> dict[str, int]:
    """Verify exhaustive current archive indices and declared-member coverage."""
    logger.debug("%s: metadata", INVENTORY_FR, extra={"fr_id": INVENTORY_FR})
    try:
        metadata = Metadata.model_validate(read_json(path))
    except ValidationError:
        fail(MANIFEST_FR, "METADATA_INVALID")
    manifest = load_manifest(_bound_file(repository, metadata.manifest))
    _bound_file(repository, manifest.roadmap)
    expected = {a.locator: a for a in manifest.artifacts}
    seen: set[str] = set()
    shards: dict[str, str] = {}
    names = [r.locator for r in metadata.class_indices]
    if len(names) != len(set(names)):
        fail(INVENTORY_FR, "CLASS_INDEX_SET")
    members = 0
    for source in metadata.class_indices:
        try:
            index = ArchiveIndex.model_validate(
                read_json(_bound_file(repository, source))
            )
        except ValidationError:
            fail(MANIFEST_FR, "CLASS_INDEX_INVALID")
        artifact = expected.get(index.artifact_locator)
        if artifact is None or index.artifact_locator in seen:
            fail(INVENTORY_FR, "CLASS_INDEX_SET")
        _index_checks(index, artifact)
        members += _member_checks(repository, index)
        for shard in index.member_shards:
            if shard.locator in shards:
                fail(INVENTORY_FR, "MEMBER_SHARD_SET")
            shards[shard.locator] = shard.sha256
        seen.add(index.artifact_locator)
    if seen != set(expected):
        fail(INVENTORY_FR, "CLASS_INDEX_SET")
    bound_shards = {r.locator: r.sha256 for r in metadata.member_shards}
    if len(bound_shards) != len(metadata.member_shards) or bound_shards != shards:
        fail(INVENTORY_FR, "MEMBER_SHARD_SET")
    counts = {
        "archives": len(seen),
        "classes": manifest.totals["classes"],
        "members": members,
    }
    logger.info(
        "%s: current metadata reconciled", INVENTORY_FR, extra={"fr_id": INVENTORY_FR}
    )
    return counts
