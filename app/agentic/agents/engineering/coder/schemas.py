"""Typed specifications, staged artefacts, and sandbox evidence.

`CodeSpecification` carries what a human authorised, never what a model
proposed. `SandboxLease` makes the four `FR-AGENTIC-046` isolation properties
explicit fields, so a lease that attests to less than all four is a different
value the agent can refuse rather than a flag it might overlook.

`CodeArtifact` makes manifest completeness structural (`FR-AGENTIC-047`):
files, per-file digests, dependency entries, tests, model and prompt
provenance, and the complete search history are all required, and the artefact
digest is derived over the whole manifest.

Promotion readiness is also structural (`FR-AGENTIC-048`): an artefact whose
declared indicators are not all registered cannot claim `ready`, so a strategy
can never present itself as promotable on top of a primitive no human has
merged.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 4_000
_MAX_SHORT_TEXT = 200
_MAX_SOURCE_BYTES = 200_000
_MAX_ITEMS = 64
_MAX_FILES = 32

type ArtifactKind = Literal["strategy_evaluator", "indicator_candidate"]
type PromotionStatus = Literal[
    "ready",
    "blocked_on_indicator_merge",
    "blocked_on_tests",
]

# Content a generated file must never contain. These are the escapes that would
# let staged code reach outside its own module at import time.
_FORBIDDEN_SOURCE_MARKERS: tuple[str, ...] = (
    "__import__",
    "importlib",
    "eval(",
    "exec(",
    "compile(",
    "subprocess",
    "os.system",
    "socket.",
    "urllib.request",
    "sys.path",
    "open(",
)


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _statements(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of required statements.

    Args:
        value: Candidate statements.
        field: Safe field label for validation.

    Returns:
        Validated statements.

    Raises:
        ValueError: If the tuple is empty or oversized.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_text(item, field, limit=_MAX_SHORT_TEXT) for item in value)


class SandboxLease(BaseModel):
    """Attested isolation properties of one ephemeral generation environment.

    Each `FR-AGENTIC-046` property is its own required field rather than a
    single flag, so a lease attesting to less than all four is a distinct
    value the agent refuses instead of a condition it might overlook.

    Attributes:
        lease_id: Stable lease identity.
        ephemeral: Whether the environment is destroyed after this use.
        credential_free: Whether the environment carries no secret material.
        network_denied: Whether egress is blocked.
        cpu_seconds: Bounded CPU allowance.
        memory_bytes: Bounded memory allowance.
        wall_clock_seconds: Bounded wall-clock allowance.
        staging_root: Directory the environment may write to.
        runtime_ref: Identity of the bound sandbox runtime.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    lease_id: str
    ephemeral: bool
    credential_free: bool
    network_denied: bool
    cpu_seconds: int
    memory_bytes: int
    wall_clock_seconds: int
    staging_root: str
    runtime_ref: str

    @field_validator("lease_id", "staging_root", "runtime_ref")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required lease reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "lease reference", limit=_MAX_TEXT)

    @field_validator("cpu_seconds", "memory_bytes", "wall_clock_seconds")
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate that a resource allowance is a positive bound.

        Args:
            value: Candidate allowance.

        Returns:
            Validated allowance.

        Raises:
            ValueError: If the allowance is not positive.
        """
        if value <= 0:
            message = "a resource bound must be positive; unbounded is not a bound"
            raise ValueError(message)
        return value

    def unattested_properties(self) -> tuple[str, ...]:
        """Return the isolation properties this lease does not attest.

        Returns:
            Ordered names of the properties that are not attested.
        """
        return tuple(
            name
            for name, attested in (
                ("credential_free", self.credential_free),
                ("ephemeral", self.ephemeral),
                ("network_denied", self.network_denied),
            )
            if not attested
        )


class GeneratedFile(BaseModel):
    """One staged source file and its content digest.

    Attributes:
        relative_path: Staging-relative POSIX path.
        content: Full file content.
        content_hash: Derived digest of the content.
        byte_count: Content length in bytes.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    relative_path: str
    content: str
    content_hash: str
    byte_count: int

    @field_validator("relative_path", "content_hash")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required file reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "file reference", limit=_MAX_SHORT_TEXT)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        """Validate bounded non-empty file content.

        Args:
            value: Candidate content.

        Returns:
            Validated content.

        Raises:
            ValueError: If the content is empty or oversized.
        """
        if not value.strip():
            message = "generated file content must not be empty"
            raise ValueError(message)
        if len(value.encode("utf-8")) > _MAX_SOURCE_BYTES:
            message = f"generated file must not exceed {_MAX_SOURCE_BYTES} bytes"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_digest(self) -> Self:
        """Validate that the digest and byte count describe the content.

        Returns:
            The validated file.

        Raises:
            ValueError: If the digest or byte count disagrees with the content.
        """
        if self.content_hash != derive_content_hash(self.content):
            message = f"content_hash does not describe {self.relative_path}"
            raise ValueError(message)
        if self.byte_count != len(self.content.encode("utf-8")):
            message = f"byte_count does not describe {self.relative_path}"
            raise ValueError(message)
        return self


class CodeSpecification(BaseModel):
    """One authenticated request to author staged code.

    Attributes:
        specification_id: Stable specification identity.
        task_id: Owning task identity.
        principal_id: Authenticated human principal who authorised this.
        artifact_kinds: Artefact kinds this specification authorises.
        objective: What the artefact must do.
        target_contract: Contract the artefact implements.
        acceptance_criteria: Conditions the artefact must satisfy.
        required_indicators: Registry identifiers the artefact relies on.
        thesis_refs: Thesis or hypothesis references motivating the work.
        constraints: Explicit constraints the author must respect.
        environment: Environment this specification is authorised for.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    specification_id: str
    task_id: str
    principal_id: str
    artifact_kinds: tuple[ArtifactKind, ...]
    objective: str
    target_contract: str
    acceptance_criteria: tuple[str, ...]
    required_indicators: tuple[str, ...]
    thesis_refs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    environment: str = "sandbox"

    @field_validator(
        "specification_id",
        "task_id",
        "principal_id",
        "target_contract",
        "environment",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required specification reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "specification reference", limit=_MAX_SHORT_TEXT)

    @field_validator("objective")
    @classmethod
    def _validate_objective(cls, value: str) -> str:
        """Validate the stated objective.

        Args:
            value: Candidate objective.

        Returns:
            Validated objective.
        """
        return _text(value, "objective")

    @field_validator("acceptance_criteria")
    @classmethod
    def _validate_acceptance(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the required acceptance criteria.

        Args:
            value: Candidate criteria.

        Returns:
            Validated criteria.
        """
        return _statements(value, "acceptance criteria")

    @field_validator(
        "required_indicators",
        "thesis_refs",
        "constraints",
    )
    @classmethod
    def _validate_optional_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded optional specification tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"specification tuples must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _text(item, "specification entry", limit=_MAX_SHORT_TEXT) for item in value
        )

    @field_validator("artifact_kinds")
    @classmethod
    def _validate_kinds(
        cls, value: tuple[ArtifactKind, ...]
    ) -> tuple[ArtifactKind, ...]:
        """Validate the authorised artefact kinds.

        Args:
            value: Candidate kinds.

        Returns:
            Deduplicated ordered kinds.

        Raises:
            ValueError: If no kind was authorised.
        """
        if not value:
            message = "a specification must authorise at least one artefact kind"
            raise ValueError(message)
        return tuple(sorted(set(value)))


class SandboxResult(BaseModel):
    """Evidence of what happened when staged code was exercised.

    Attributes:
        result_id: Stable result identity.
        lease_id: Lease the run executed under.
        compiled: Whether every generated file parsed.
        tests_run: Number of generated tests executed.
        tests_passed: Number that passed.
        duration_seconds: Observed wall-clock duration.
        network_attempted: Whether the run attempted egress.
        diagnostics: Bounded diagnostic lines.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    result_id: str
    lease_id: str
    compiled: bool
    tests_run: int
    tests_passed: int
    duration_seconds: int
    network_attempted: bool = False
    diagnostics: tuple[str, ...] = ()

    @field_validator("result_id", "lease_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required result reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "sandbox result reference", limit=_MAX_SHORT_TEXT)

    @field_validator("tests_run", "tests_passed", "duration_seconds")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one non-negative observation.

        Args:
            value: Candidate observation.

        Returns:
            Validated observation.

        Raises:
            ValueError: If the observation is negative.
        """
        if value < 0:
            message = "a sandbox observation must not be negative"
            raise ValueError(message)
        return value

    @field_validator("diagnostics")
    @classmethod
    def _validate_diagnostics(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the bounded diagnostic lines.

        Args:
            value: Candidate diagnostics.

        Returns:
            Validated diagnostics.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"diagnostics must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(_text(item, "diagnostic") for item in value)

    @model_validator(mode="after")
    def _validate_counts(self) -> Self:
        """Validate that the pass count is consistent with the run count.

        Returns:
            The validated result.

        Raises:
            ValueError: If more tests passed than ran.
        """
        if self.tests_passed > self.tests_run:
            message = "tests_passed cannot exceed tests_run"
            raise ValueError(message)
        return self

    @property
    def all_passed(self) -> bool:
        """Report whether the run compiled and every test passed.

        Returns:
            True when the artefact is test-clean.
        """
        return (
            self.compiled and self.tests_run > 0 and self.tests_passed == self.tests_run
        )


class CodeArtifact(BaseModel):
    """One staged, content-addressed code artefact and its full provenance.

    Attributes:
        artifact_id: Stable artefact identity.
        task_id: Owning task identity.
        specification_id: Specification this artefact answers.
        kind: Artefact kind produced.
        files: Generated files with their digests.
        dependencies: Declared dependency and SBOM entries.
        tests: Test identifiers the artefact carries.
        required_indicators: Registry identifiers the artefact relies on.
        unregistered_indicators: Required identifiers not in the registry.
        model_profile_id: Model profile that authored this.
        base_prompt_hash: Digest of the role instruction in force.
        composite_instruction_hash: Digest of the full instruction chain.
        tool_refs: Governed tools used while authoring.
        search_history: Complete ordered record of authoring attempts.
        sandbox_result: Evidence from exercising the artefact.
        staging_path: Staging-relative directory the artefact occupies.
        promotion_status: Whether the artefact may be considered for promotion.
        artifact_hash: Derived digest over the whole manifest.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    artifact_id: str
    task_id: str
    specification_id: str
    kind: ArtifactKind
    files: tuple[GeneratedFile, ...]
    dependencies: Mapping[str, str]
    tests: tuple[str, ...]
    required_indicators: tuple[str, ...]
    unregistered_indicators: tuple[str, ...]
    model_profile_id: str
    base_prompt_hash: str
    composite_instruction_hash: str
    tool_refs: tuple[str, ...]
    search_history: tuple[str, ...]
    sandbox_result: SandboxResult
    staging_path: str
    promotion_status: PromotionStatus
    artifact_hash: str

    @field_validator(
        "artifact_id",
        "task_id",
        "specification_id",
        "model_profile_id",
        "base_prompt_hash",
        "composite_instruction_hash",
        "staging_path",
        "artifact_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required artefact reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "artefact reference", limit=_MAX_SHORT_TEXT)

    @field_validator("files")
    @classmethod
    def _validate_files(
        cls,
        value: tuple[GeneratedFile, ...],
    ) -> tuple[GeneratedFile, ...]:
        """Validate the generated file set.

        Args:
            value: Candidate files.

        Returns:
            Validated files.

        Raises:
            ValueError: If the set is empty, oversized, or has duplicate paths.
        """
        if not value:
            message = "an artefact must contain at least one generated file"
            raise ValueError(message)
        if len(value) > _MAX_FILES:
            message = f"an artefact must not exceed {_MAX_FILES} files"
            raise ValueError(message)
        paths = [item.relative_path for item in value]
        if len(set(paths)) != len(paths):
            message = "generated files must have unique relative paths"
            raise ValueError(message)
        return value

    @field_validator("tests", "search_history")
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required provenance tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _statements(value, "artefact provenance")

    @field_validator("tool_refs", "required_indicators", "unregistered_indicators")
    @classmethod
    def _validate_optional_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded optional artefact tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"artefact tuples must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _text(item, "artefact entry", limit=_MAX_SHORT_TEXT) for item in value
        )

    @field_validator("dependencies")
    @classmethod
    def _validate_dependencies(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the declared dependency and SBOM entries.

        Args:
            value: Candidate mapping.

        Returns:
            Deterministically ordered read-only mapping.

        Raises:
            ValueError: If the mapping is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"dependencies must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        frozen = {
            _text(key, "dependency name", limit=_MAX_SHORT_TEXT): _text(
                item,
                "dependency version",
                limit=_MAX_SHORT_TEXT,
            )
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @model_validator(mode="after")
    def _validate_promotion(self) -> Self:
        """Validate that readiness agrees with the evidence carried.

        Returns:
            The validated artefact.

        Raises:
            ValueError: If the artefact claims readiness while an indicator it
                requires is unregistered, or while its tests are not clean, or
                if it reports unregistered indicators it does not require.
        """
        unknown = sorted(
            set(self.unregistered_indicators) - set(self.required_indicators)
        )
        if unknown:
            message = (
                "unregistered_indicators names identifiers this artefact does not "
                f"require: {', '.join(unknown)}"
            )
            raise ValueError(message)
        if self.promotion_status == "ready" and self.unregistered_indicators:
            message = (
                "an artefact requiring unregistered indicators cannot be ready; "
                f"a human must merge: {', '.join(self.unregistered_indicators)}"
            )
            raise ValueError(message)
        if self.promotion_status == "ready" and not self.sandbox_result.all_passed:
            message = "an artefact whose tests are not clean cannot be ready"
            raise ValueError(message)
        return self

    @field_serializer("dependencies", mode="plain")
    def _serialize_dependencies(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the dependency mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def derive_content_hash(content: str) -> str:
    """Derive the canonical digest of one file's content.

    Args:
        content: Full file content.

    Returns:
        The canonical content digest.
    """
    return canonical_digest(content)


def derive_artifact_hash(fields: Mapping[str, object]) -> str:
    """Derive the manifest digest of one staged artefact.

    The digest covers the whole manifest — files, dependencies, tests,
    provenance, and search history — so a manifest altered after staging no
    longer matches its own identity.

    Args:
        fields: Artefact fields excluding the derived digest.

    Returns:
        The canonical manifest digest.
    """
    payload = {
        key: _json_safe(value)
        for key, value in fields.items()
        if key != "artifact_hash"
    }
    return canonical_digest(payload)


def _json_safe(value: object) -> object:
    """Convert one declared artefact field to JSON-safe data.

    Args:
        value: Declared field value.

    Returns:
        JSON-safe field data.
    """
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    return value


def build_generated_file(relative_path: str, content: str) -> GeneratedFile:
    """Build one staged file with its derived digest.

    Args:
        relative_path: Staging-relative POSIX path.
        content: Full file content.

    Returns:
        A validated immutable generated file.
    """
    return GeneratedFile.model_validate(
        {
            "relative_path": relative_path,
            "content": content,
            "content_hash": derive_content_hash(content),
            "byte_count": len(content.encode("utf-8")),
        },
    )


def build_code_specification(fields: Mapping[str, object]) -> CodeSpecification:
    """Build one authenticated code specification.

    Args:
        fields: Complete specification fields.

    Returns:
        A validated immutable specification.
    """
    logger.debug("Building a code specification")
    return CodeSpecification.model_validate(fields)


def build_sandbox_lease(fields: Mapping[str, object]) -> SandboxLease:
    """Build one attested sandbox lease.

    Args:
        fields: Complete lease fields.

    Returns:
        A validated immutable lease.
    """
    return SandboxLease.model_validate(fields)


def build_sandbox_result(fields: Mapping[str, object]) -> SandboxResult:
    """Build one sandbox result.

    Args:
        fields: Complete result fields.

    Returns:
        A validated immutable result.
    """
    return SandboxResult.model_validate(fields)


def build_code_artifact(fields: Mapping[str, object]) -> CodeArtifact:
    """Build one staged code artefact carrying its manifest digest.

    Args:
        fields: Complete artefact fields excluding the derived digest.

    Returns:
        A validated immutable artefact.
    """
    logger.debug("Building a staged code artefact")
    return CodeArtifact.model_validate(
        {**fields, "artifact_hash": derive_artifact_hash(fields)},
    )


def forbidden_source_markers(content: str) -> tuple[str, ...]:
    """Return the escape markers one generated file contains.

    Staged code is never imported by this system, so these markers are not a
    sandbox. They are a review signal: generated code reaching for an import,
    a subprocess, a socket, or the filesystem is worth a human's attention
    before anything merges it.

    Args:
        content: Generated file content.

    Returns:
        Ordered markers found in the content.
    """
    return tuple(marker for marker in _FORBIDDEN_SOURCE_MARKERS if marker in content)
