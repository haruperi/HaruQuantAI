"""Domain models and DTOs for plugin manifests and packages."""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import Field, StringConstraints, model_validator

from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    DecimalValue,
    JsonObject,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)


class PluginType(StrEnum):
    """Supported plugin contribution types."""

    BLOCK = "BLOCK"
    INDICATOR = "INDICATOR"
    METRIC = "METRIC"
    FILTER = "FILTER"
    FITNESS = "FITNESS"
    RESEARCH_METHOD = "RESEARCH_METHOD"
    DATA_CONNECTOR = "DATA_CONNECTOR"
    PROJECT_TASK = "PROJECT_TASK"
    SOURCE_EMITTER = "SOURCE_EMITTER"
    RESULT_PANEL = "RESULT_PANEL"


@dataclass(frozen=True, slots=True)
class PluginPermission:
    """Declared execution permissions for a plugin."""

    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()
    network_endpoints: tuple[str, ...] = ()
    subprocess_allow: bool = False
    secrets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginResourceLimits:
    """Declared execution resource limits for a plugin."""

    cpu_limit_cores: float = 1.0
    memory_limit_mb: int = 512
    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class PluginFileEntry:
    """Metadata for an individual file contained in a plugin package."""

    path: str
    sha256: str
    size_bytes: int = 0


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Authoritative manifest declaring plugin metadata and capabilities."""

    id: str
    version: str
    api_range: str
    types: tuple[PluginType, ...] = ()
    entry_point: str = "main.py"
    schemas: dict[str, Any] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()
    permissions: PluginPermission = field(default_factory=PluginPermission)
    resources: PluginResourceLimits = field(default_factory=PluginResourceLimits)
    sha256_by_file: dict[str, str] = field(default_factory=dict)
    signature: str | None = None


@dataclass(frozen=True, slots=True)
class PluginPackageValidation:
    """Result of validating a plugin package zip file and its manifest."""

    manifest: PluginManifest
    package_hash: str
    files: tuple[PluginFileEntry, ...] = ()
    is_valid: bool = True
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginPackageRef:
    """Reference descriptor for a validated plugin package."""

    plugin_id: str
    version: str
    package_path: str
    package_hash: str


@dataclass(frozen=True, slots=True)
class PluginContributionDescriptor:
    """Descriptor declaring a single typed plugin contribution."""

    plugin_id: str
    plugin_type: PluginType
    contribution_id: str
    name: str
    description: str = ""
    schema_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContributionTestResult:
    """Result of executing contract verification on a plugin contribution."""

    contribution_id: str
    plugin_type: PluginType
    passed: bool
    details: str = ""
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContributionRegistrationResult:
    """Outcome of registering one or more contributions from a plugin manifest."""

    plugin_id: str
    contributions: tuple[PluginContributionDescriptor, ...] = ()
    test_results: tuple[ContributionTestResult, ...] = ()
    is_successful: bool = True
    errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Ratified v1 wire contracts (additive; the frozen v1 dataclasses above stay
# unchanged as process contracts). The v1-backed ``PluginManifest`` gains a
# ``PluginManifestWire`` projection; wire-native records keep their inventory
# names. Plugin stable IDs are external-origin string identifiers
# ``^[a-z0-9][a-z0-9._-]{0,127}$``, the documented ``Uuid7`` exception for
# this namespace; v1 ``Any`` positions take ``JsonObject``; v1 float resource
# limits take ``DecimalValue``. Process-local ``Path`` packages and
# implementation objects never cross wires.

# Constrained local string aliases reused across Plugins wire records.
type NonEmptyStr = typing.Annotated[str, StringConstraints(min_length=1)]
# Documented Uuid7 exception: plugin stable IDs are external-origin string
# identifiers of at most 128 characters.
type PluginStableId = typing.Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
]
# Domain assumption: a syntactic SemVer 2.0.0 core check only; this does not
# validate build/precedence semantics.
type SemverString = typing.Annotated[
    str,
    StringConstraints(
        pattern=r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
    ),
]
# Domain assumption: API-range grammar (e.g. ``>=1.0.0 <2.0.0``) is verified
# by the process layer; the wire form requires a nonempty string.
type ApiRangeStr = NonEmptyStr
# Plugin-package relative POSIX path: non-empty segments, no backslashes,
# and no leading root; ``..`` and drive anchors are rejected by record
# validators.
type RelativePackagePath = typing.Annotated[
    str, StringConstraints(pattern=r"^[^/\\]+(?:/[^/\\]+)*$")
]
type NonNegativeInt = typing.Annotated[int, Field(ge=0)]

# Closed literal unions reused across Plugins wire records.
type PluginTypeValue = typing.Literal[
    "BLOCK",
    "INDICATOR",
    "METRIC",
    "FILTER",
    "FITNESS",
    "RESEARCH_METHOD",
    "DATA_CONNECTOR",
    "PROJECT_TASK",
    "SOURCE_EMITTER",
    "RESULT_PANEL",
]
type PluginActivationState = typing.Literal["INSTALLED", "ENABLED", "DISABLED"]
type PluginExecutionState = typing.Literal[
    "LOADED",
    "STARTED",
    "RUNNING",
    "TIMED_OUT",
    "CRASHED",
    "STOPPED",
]
type PluginAnalysisOutcome = typing.Literal["SUCCEEDED", "FAILED"]
type PanelBridgeOperation = typing.Literal[
    "READ_RESULTS",
    "QUERY_DATA",
    "RECEIVE_MESSAGES",
]
type CompatibilityVerdict = typing.Literal["SUPPORTED", "DEPRECATED", "UNSUPPORTED"]


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


def _require_positive_decimal(fields: tuple[tuple[str, DecimalValue], ...]) -> None:
    """Reject decimal fields that are not strictly positive.

    Args:
        fields: ``(field name, value)`` pairs bounded to ``> 0``.

    Raises:
        ValueError: Any listed decimal is zero or negative.
    """
    for name, value in fields:
        if Decimal(value) <= 0:
            raise ValueError(name + " must be positive")


def _validate_relative_package_path(name: str, value: str) -> None:
    """Reject package paths that anchor outside the package root.

    Args:
        name: Field name reported in the validation error.
        value: Declared package-relative path.

    Raises:
        ValueError: The path traverses with a ``..`` segment or carries a
            Windows drive anchor (a colon marks a drive anchor; the wire
            pattern already rejects absolute roots and backslashes).
    """
    if ":" in value:
        raise ValueError(name + " must be a package-relative path")
    if ".." in value.split("/"):
        raise ValueError(name + " must not contain '..' segments")


class PluginPermissionWire(WireModel):
    """Wire form of the v1 declared plugin execution permissions.

    ``secrets`` carries Workspace ``SecretRef`` names only; secret values
    never cross the wire.
    """

    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()
    network_endpoints: tuple[str, ...] = ()
    subprocess_allow: bool = False
    secrets: tuple[NonEmptyStr, ...] = ()


class PluginResourceLimitsWire(WireModel):
    """Wire form of the v1 declared plugin resource limits.

    The v1 float limits take ``DecimalValue``; CPU cores and the elapsed-time
    limit must exceed zero.
    """

    cpu_limit_cores: DecimalValue = "1"
    memory_limit_mb: int = Field(default=512, ge=1)
    timeout_seconds: DecimalValue = "30"

    @model_validator(mode="after")
    def validate_positive_limits(self) -> PluginResourceLimitsWire:
        """Reject non-positive CPU or elapsed-time limits.

        Returns:
            The validated limits.

        Raises:
            ValueError: ``cpu_limit_cores`` or ``timeout_seconds`` is zero
                or negative.
        """
        _require_positive_decimal(
            (
                ("cpu_limit_cores", self.cpu_limit_cores),
                ("timeout_seconds", self.timeout_seconds),
            )
        )
        return self


class PluginRef(WireModel):
    """Wire-native stable reference to one declared plugin."""

    plugin_id: PluginStableId
    schema_version: typing.Literal[1] = 1


class PluginVersion(WireModel):
    """Wire-native immutable version record of one declared plugin.

    ``(plugin_id, version)`` is unique and the record is immutable once
    persisted.
    """

    plugin_id: PluginStableId
    version: SemverString
    api_range: ApiRangeStr
    types: tuple[PluginTypeValue, ...] = ()
    manifest_hash: ContentHash
    package_hash: ContentHash
    capabilities: tuple[CapabilityIdentifier, ...] = ()
    permissions: PluginPermissionWire
    resources: PluginResourceLimitsWire
    content_hash: ContentHash
    schema_version: typing.Literal[1] = 1


class PluginManifestWire(WireModel):
    """Wire projection of the v1 ``PluginManifest`` (record R3).

    The v1 field names are kept; ``schemas`` takes ``JsonObject`` in place
    of the v1 ``Any``. Package paths are normalized relative paths with no
    ``..``, drive, or absolute anchors.
    """

    id: PluginStableId
    version: SemverString
    api_range: ApiRangeStr
    types: tuple[PluginTypeValue, ...] = ()
    entry_point: RelativePackagePath = "main.py"
    schemas: dict[str, JsonObject] = Field(default_factory=dict)
    capabilities: tuple[CapabilityIdentifier, ...] = ()
    permissions: PluginPermissionWire = Field(default_factory=PluginPermissionWire)
    resources: PluginResourceLimitsWire = Field(
        default_factory=PluginResourceLimitsWire
    )
    sha256_by_file: dict[RelativePackagePath, ContentHash] = Field(default_factory=dict)
    signature: str | None = None
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_package_paths(self) -> PluginManifestWire:
        """Reject unsafe entry points and file-hash paths.

        Returns:
            The validated manifest.

        Raises:
            ValueError: ``entry_point`` or a ``sha256_by_file`` key contains
                a ``..`` segment or a drive anchor.
        """
        _validate_relative_package_path("entry_point", self.entry_point)
        for path in self.sha256_by_file:
            _validate_relative_package_path("sha256_by_file", path)
        return self


class PluginCompatibility(WireModel):
    """Wire-native published plugin API compatibility declaration.

    A supported older plugin runs unchanged or is rejected before activation
    with a precise reason.
    """

    plugin_api_version: SemverString
    supported_range: ApiRangeStr
    is_deprecated: bool = False
    deprecation_diagnostic: str = ""
    migration_guide_ref: str | None = None
    conformance_suite: NonEmptyStr
    schema_version: typing.Literal[1] = 1


class PluginPermissionSet(WireModel):
    """Wire-native effective sandbox grants for one plugin in a workspace.

    Effective grants narrow the declared manifest permissions only; the
    provider rejects any grant exceeding the declared manifest, grants no
    network the manifest did not declare, and supplies only declared
    endpoints and credentials. ``secrets`` carries Workspace ``SecretRef``
    names only.
    """

    plugin_id: PluginStableId
    workspace_id: Uuid7
    version: SemverString
    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()
    network_endpoints: tuple[str, ...] = ()
    subprocess_allow: bool = False
    secrets: tuple[NonEmptyStr, ...] = ()
    cpu_limit_cores: DecimalValue = "1"
    memory_limit_mb: int = Field(default=1024, ge=1)
    timeout_seconds: DecimalValue = "60"
    max_output_mb: int = Field(default=64, ge=1)
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_positive_limits(self) -> PluginPermissionSet:
        """Reject non-positive CPU or elapsed-time limits.

        Returns:
            The validated permission set.

        Raises:
            ValueError: ``cpu_limit_cores`` or ``timeout_seconds`` is zero
                or negative.
        """
        _require_positive_decimal(
            (
                ("cpu_limit_cores", self.cpu_limit_cores),
                ("timeout_seconds", self.timeout_seconds),
            )
        )
        return self


class PluginActivation(WireModel):
    """Wire-native transactional plugin activation state in a workspace.

    ``(plugin_id, workspace_id)`` is unique (``plugin_activations``); a
    failed upgrade preserves the previous usable version and dependent
    objects remain diagnosable.
    """

    plugin_id: PluginStableId
    workspace_id: Uuid7
    installed_version: SemverString
    previous_version: SemverString | None = None
    state: PluginActivationState
    enabled_at: UtcTimestamp | None = None
    disabled_at: UtcTimestamp | None = None
    row_version: int = Field(default=1, ge=1)
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    schema_version: typing.Literal[1] = 1


class PluginLifecycleState(WireModel):
    """Wire-native observational plugin execution lifecycle record.

    Append-only observational state; kill, timeout, or crash leaves the API
    and committed inputs intact.
    """

    plugin_id: PluginStableId
    workspace_id: Uuid7
    execution_state: PluginExecutionState
    entered_at: UtcTimestamp
    last_heartbeat_at: UtcTimestamp | None = None
    exit_reason: str = ""
    schema_version: typing.Literal[1] = 1


class PluginContribution(WireModel):
    """Wire-native registered typed plugin contribution.

    The v1 ``PluginContributionDescriptor`` remains the process type; each
    type passes its contract-test kit before stable enablement.
    """

    contribution_id: NonEmptyStr
    plugin_id: PluginStableId
    plugin_type: PluginTypeValue
    name: NonEmptyStr
    description: str = ""
    schema_ref: NonEmptyStr | None = None
    metadata: JsonObject = Field(default_factory=dict)
    registered_at: UtcTimestamp
    is_enabled: bool = True
    schema_version: typing.Literal[1] = 1


class PluginInputHandle(WireModel):
    """Wire-native immutable read-only artifact input handle.

    Direct database or artifact mutation is impossible through the plugin
    contract.
    """

    artifact_id: Uuid7
    content_hash: ContentHash
    media_type: NonEmptyStr
    read_only: typing.Literal[True] = True


class PluginAnalysisRequest(WireModel):
    """Wire-native isolated plugin analysis request.

    Handles are immutable; the request reaches the plugin through the
    analysis boundary only.
    """

    request_id: Uuid7
    plugin_id: PluginStableId
    contribution_id: NonEmptyStr
    input_handles: tuple[PluginInputHandle, ...] = ()
    parameters: JsonObject = Field(default_factory=dict)
    schema_version: typing.Literal[1] = 1


class PluginAnalysisResult(WireModel):
    """Wire-native isolated plugin analysis outcome.

    Output is staged only (``STAGED``, schema-validated) and never committed
    by the plugin boundary.
    """

    request_id: Uuid7
    contribution_id: NonEmptyStr
    status: PluginAnalysisOutcome
    staged_artifact_id: Uuid7 | None = None
    errors: tuple[ValidationIssue, ...] = ()
    schema_version: typing.Literal[1] = 1


class ResultPanelDescriptor(WireModel):
    """Wire-native sandboxed result-panel descriptor.

    Sandboxed browser boundary with a narrow read/query/message bridge; no
    control-plane credentials; undeclared navigation and commands are
    blocked.
    """

    panel_id: NonEmptyStr
    contribution_id: NonEmptyStr
    plugin_id: PluginStableId
    title: NonEmptyStr
    bridge_operations: tuple[PanelBridgeOperation, ...] = ()
    content_source: NonEmptyStr
    schema_version: typing.Literal[1] = 1


class ContributionTestResultWire(WireModel):
    """Wire form of the v1 contribution contract-fixture test result."""

    contribution_id: NonEmptyStr
    plugin_type: PluginTypeValue
    passed: bool
    details: str = ""
    errors: tuple[str, ...] = ()


class PluginValidationReport(WireModel):
    """Wire-native plugin package validation report.

    A reference plugin passes identically in CI and the local harness.
    """

    report_id: Uuid7
    plugin_id: PluginStableId
    version: SemverString
    manifest_checks: tuple[ValidationIssue, ...] = ()
    contract_fixture_results: tuple[ContributionTestResultWire, ...] = ()
    permission_simulation_findings: tuple[NonEmptyStr, ...] = ()
    captured_log_counts: dict[NonEmptyStr, NonNegativeInt] = Field(default_factory=dict)
    package_hash: ContentHash
    is_valid: bool
    schema_version: typing.Literal[1] = 1


class PluginFileEntryWire(WireModel):
    """Wire form of the v1 plugin package file entry metadata."""

    path: RelativePackagePath
    sha256_hash: ContentHash
    size_bytes: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_relative_path(self) -> PluginFileEntryWire:
        """Reject package file paths that anchor outside the package root.

        Returns:
            The validated file entry.

        Raises:
            ValueError: ``path`` contains a ``..`` segment or drive anchor.
        """
        _validate_relative_package_path("path", self.path)
        return self


class PluginPackageReceipt(WireModel):
    """Wire-native retained plugin package installation receipt.

    The v1 ``PluginPackageValidation``/``PluginPackageRef`` wire facts are
    carried here; ``signature_verified`` stays false when the package
    carried no verifiable detached signature.
    """

    receipt_id: Uuid7
    plugin_id: PluginStableId
    version: SemverString
    package_hash: ContentHash
    manifest_hash: ContentHash
    files: tuple[PluginFileEntryWire, ...] = ()
    signature_verified: bool = False
    installed_at: UtcTimestamp
    schema_version: typing.Literal[1] = 1


class ManageLifecycleRequest(WireModel):
    """Operation-discriminated plugin lifecycle request.

    ``INSTALL`` and ``UPGRADE`` require ``receipt`` (plugin identity and
    version arrive on the receipt; ``plugin_id`` and ``workspace_id`` stay
    optional addressors); ``ENABLE``, ``DISABLE``, and ``REMOVE`` require
    ``plugin_id`` and ``workspace_id`` and forbid the receipt; ``UPGRADE``
    additionally accepts an optional target ``version`` and every other
    operation forbids it.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal["INSTALL", "ENABLE", "DISABLE", "UPGRADE", "REMOVE"]
    receipt: PluginPackageReceipt | None = None
    plugin_id: PluginStableId | None = None
    workspace_id: Uuid7 | None = None
    version: SemverString | None = None
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageLifecycleRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "INSTALL":
                _require_present((("receipt", self.receipt),))
                _require_absent((("version", self.version),))
            case "UPGRADE":
                _require_present((("receipt", self.receipt),))
            case "ENABLE" | "DISABLE" | "REMOVE":
                _require_present(
                    (
                        ("plugin_id", self.plugin_id),
                        ("workspace_id", self.workspace_id),
                    )
                )
                _require_absent(
                    (
                        ("receipt", self.receipt),
                        ("version", self.version),
                    )
                )
        return self


class ManageLifecycleSuccess(WireModel):
    """Successful plugin lifecycle operation result.

    ``activation`` and ``lifecycle`` are returned when the operation
    produces them; the event union is empty.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    activation: PluginActivation | None = None
    lifecycle: PluginLifecycleState | None = None
    schema_version: typing.Literal[1] = 1


class SandboxPermissionsRequest(WireModel):
    """Operation-discriminated plugin sandbox permission request.

    ``GRANT`` carries the immutable manifest, package hash, requested
    permissions, and resource limits. ``INSPECT`` and ``EXECUTE`` address an
    existing grant; only ``EXECUTE`` carries bounded JSON input.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal["GRANT", "INSPECT", "EXECUTE"]
    plugin_id: PluginStableId | None = None
    workspace_id: Uuid7 | None = None
    version: SemverString | None = None
    manifest: PluginManifestWire | None = None
    package_hash: ContentHash | None = None
    requested_permissions: PluginPermissionWire | None = None
    requested_resources: PluginResourceLimitsWire | None = None
    input: JsonObject | None = None
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> SandboxPermissionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "GRANT":
                _require_present(
                    (
                        ("plugin_id", self.plugin_id),
                        ("workspace_id", self.workspace_id),
                        ("version", self.version),
                        ("manifest", self.manifest),
                        ("package_hash", self.package_hash),
                        ("requested_permissions", self.requested_permissions),
                        ("requested_resources", self.requested_resources),
                    )
                )
                _require_absent((("input", self.input),))
            case "INSPECT":
                _require_present(
                    (
                        ("plugin_id", self.plugin_id),
                        ("workspace_id", self.workspace_id),
                        ("version", self.version),
                    )
                )
                _require_absent(
                    (
                        ("manifest", self.manifest),
                        ("package_hash", self.package_hash),
                        ("requested_permissions", self.requested_permissions),
                        ("requested_resources", self.requested_resources),
                        ("input", self.input),
                    )
                )
            case "EXECUTE":
                _require_present(
                    (
                        ("plugin_id", self.plugin_id),
                        ("workspace_id", self.workspace_id),
                        ("version", self.version),
                        ("input", self.input),
                    )
                )
                _require_absent(
                    (
                        ("manifest", self.manifest),
                        ("package_hash", self.package_hash),
                        ("requested_permissions", self.requested_permissions),
                        ("requested_resources", self.requested_resources),
                    )
                )
        return self


class SandboxPermissionsSuccess(WireModel):
    """Successful plugin sandbox permission operation result.

    The event union is empty.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    permission_set: PluginPermissionSet | None = None
    lifecycle_state: typing.Literal["GRANTED", "INSPECTED", "EXECUTED"] | None = None
    output: JsonObject | None = None
    schema_version: typing.Literal[1] = 1


class IsolateAnalysisRequest(WireModel):
    """Operation-discriminated plugin analysis boundary request.

    ``ANALYZE`` requires the ``analysis`` request record; the event union is
    empty.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal["ANALYZE"]
    analysis: PluginAnalysisRequest
    schema_version: typing.Literal[1] = 1


class IsolateAnalysisSuccess(WireModel):
    """Successful plugin analysis boundary operation result.

    The event union is empty.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    result: PluginAnalysisResult | None = None
    schema_version: typing.Literal[1] = 1


class RenderResultPanelsRequest(WireModel):
    """Operation-discriminated plugin result panel request.

    ``DESCRIBE_PANELS`` accepts an optional ``contribution_id`` filter and
    forbids ``panel_id``; ``RESOLVE_PANEL`` requires ``panel_id`` and
    forbids ``contribution_id``. The event union is empty.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal["DESCRIBE_PANELS", "RESOLVE_PANEL"]
    contribution_id: NonEmptyStr | None = None
    panel_id: NonEmptyStr | None = None
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> RenderResultPanelsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DESCRIBE_PANELS":
                _require_absent((("panel_id", self.panel_id),))
            case "RESOLVE_PANEL":
                _require_present((("panel_id", self.panel_id),))
                _require_absent((("contribution_id", self.contribution_id),))
        return self


class RenderResultPanelsSuccess(WireModel):
    """Successful plugin result panel operation result.

    The event union is empty.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    panels: tuple[ResultPanelDescriptor, ...] = ()
    schema_version: typing.Literal[1] = 1


class MaintainCompatibilityRequest(WireModel):
    """Operation-discriminated plugin compatibility request.

    ``PUBLISH`` requires ``compatibility`` and forbids ``plugin_id`` and
    ``version``; ``CHECK`` requires ``plugin_id`` and ``version`` and
    forbids ``compatibility``. Publication is observational Kernel
    ``PUBLISH`` with no subscription; the event union is empty.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal["PUBLISH", "CHECK"]
    compatibility: PluginCompatibility | None = None
    plugin_id: PluginStableId | None = None
    version: SemverString | None = None
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> MaintainCompatibilityRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "PUBLISH":
                _require_present((("compatibility", self.compatibility),))
                _require_absent(
                    (
                        ("plugin_id", self.plugin_id),
                        ("version", self.version),
                    )
                )
            case "CHECK":
                _require_present(
                    (
                        ("plugin_id", self.plugin_id),
                        ("version", self.version),
                    )
                )
                _require_absent((("compatibility", self.compatibility),))
        return self


class MaintainCompatibilitySuccess(WireModel):
    """Successful plugin compatibility operation result.

    ``compatibility`` is returned when the operation yields a published
    declaration; ``verdict`` classifies the checked plugin version for
    ``CHECK``.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    compatibility: PluginCompatibility | None = None
    verdict: CompatibilityVerdict | None = None
    schema_version: typing.Literal[1] = 1


# Wire projections register under their inventory names (``PluginManifest``
# -> ``PluginManifestWire``); wire-native and request/success records
# register directly. Nested components (``PluginPermissionWire``,
# ``PluginResourceLimitsWire``, ``PluginInputHandle``,
# ``ContributionTestResultWire``, ``PluginFileEntryWire``) are inline record
# parts, not registered public records.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "PluginRef": PluginRef,
    "PluginVersion": PluginVersion,
    "PluginManifest": PluginManifestWire,
    "PluginCompatibility": PluginCompatibility,
    "PluginPermissionSet": PluginPermissionSet,
    "PluginActivation": PluginActivation,
    "PluginLifecycleState": PluginLifecycleState,
    "PluginContribution": PluginContribution,
    "PluginAnalysisRequest": PluginAnalysisRequest,
    "PluginAnalysisResult": PluginAnalysisResult,
    "ResultPanelDescriptor": ResultPanelDescriptor,
    "PluginValidationReport": PluginValidationReport,
    "PluginPackageReceipt": PluginPackageReceipt,
    "ManageLifecycleRequest": ManageLifecycleRequest,
    "ManageLifecycleSuccess": ManageLifecycleSuccess,
    "SandboxPermissionsRequest": SandboxPermissionsRequest,
    "SandboxPermissionsSuccess": SandboxPermissionsSuccess,
    "IsolateAnalysisRequest": IsolateAnalysisRequest,
    "IsolateAnalysisSuccess": IsolateAnalysisSuccess,
    "RenderResultPanelsRequest": RenderResultPanelsRequest,
    "RenderResultPanelsSuccess": RenderResultPanelsSuccess,
    "MaintainCompatibilityRequest": MaintainCompatibilityRequest,
    "MaintainCompatibilitySuccess": MaintainCompatibilitySuccess,
}
