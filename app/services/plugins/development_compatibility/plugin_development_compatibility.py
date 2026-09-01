"""Plugin conformance validation and compatibility policy provider.

This feature validates already-supplied plugin ZIP packages through public
capabilities and maintains one in-memory global API compatibility declaration.
It does not execute plugin payloads, persist policy, or expose permission values.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import uuid
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from app.contracts.common.models import ProblemDetails, Uuid7
from app.contracts.plugins.errors import (
    PluginError,
    PluginFailure,
    PluginFailureCode,
)
from app.contracts.plugins.models import (
    ContributionRegistrationResult,
    ContributionTestResult,
    ContributionTestResultWire,
    MaintainCompatibilityRequest,
    MaintainCompatibilitySuccess,
    PluginCompatibility,
    PluginContributionDescriptor,
    PluginFileEntry,
    PluginManifest,
    PluginPackageValidation,
    PluginType,
    PluginValidationReport,
)
from app.contracts.plugins.ports import MaintainCompatibilityCapability
from app.services.plugins.development_compatibility.config import (
    DevelopmentCompatibilityConfig,
)

if TYPE_CHECKING:
    from app.contracts.plugins.ports import (
        DeclareManifestsCapability,
        RegisterContributionsCapability,
    )

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_COMPARATOR_RE = re.compile(r"^(?P<operator>>=|<=|>|<|=)(?P<version>.+)$")
_FORBIDDEN_RANGE_TOKENS = ("||", "^", "~", "*", "x", "X")
_REFERENCE_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REFERENCE_ZIP_PERMISSIONS = 0o100644 << 16
_EXPECTED_CAPTURED_INFO_EVENTS = 2
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _SemVer:
    """Parsed SemVer 2 value used only inside this feature."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Comparator:
    """One accepted compatibility range comparator."""

    operator: str
    version: _SemVer


class _RedactingLogCapture(logging.Handler):
    """Capture only validation log levels, never record message content."""

    def __init__(self) -> None:
        """Initialize a count-only in-memory capture handler."""
        super().__init__()
        self._counts: dict[str, int] = {}

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Count one record without reading its message or arguments."""
        level = record.levelname.lower()
        self._counts[level] = self._counts.get(level, 0) + 1

    def counts(self) -> dict[str, int]:
        """Return a copy of the observed safe level counts."""
        return dict(self._counts)


def _parse_semver(value: str) -> _SemVer:
    """Parse a full SemVer 2 string, ignoring build metadata for precedence.

    Args:
        value: SemVer 2 version string.

    Returns:
        Parsed precedence components.

    Raises:
        ValueError: If the string is not a valid full SemVer 2 value.
    """
    match = _SEMVER_RE.fullmatch(value)
    if match is None:
        message = f"Invalid SemVer 2 version: {value!r}"
        raise ValueError(message)
    prerelease_raw = match.group("prerelease")
    prerelease = tuple(prerelease_raw.split(".")) if prerelease_raw else ()
    has_invalid_numeric_identifier = any(
        part.isdigit() and len(part) > 1 and part.startswith("0") for part in prerelease
    )
    if has_invalid_numeric_identifier:
        message = f"Invalid numeric prerelease identifier: {value!r}"
        raise ValueError(message)
    return _SemVer(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=prerelease,
    )


def _compare_versions(left: _SemVer, right: _SemVer) -> int:
    """Compare two SemVer values according to SemVer 2 precedence.

    Returns:
        A negative, zero, or positive precedence comparison result.
    """
    core_left = (left.major, left.minor, left.patch)
    core_right = (right.major, right.minor, right.patch)
    if core_left != core_right:
        return (core_left > core_right) - (core_left < core_right)
    if not left.prerelease or not right.prerelease:
        return (not left.prerelease) - (not right.prerelease)
    for left_part, right_part in zip(left.prerelease, right.prerelease, strict=False):
        if left_part == right_part:
            continue
        if left_part.isdigit() and right_part.isdigit():
            return (int(left_part) > int(right_part)) - (
                int(left_part) < int(right_part)
            )
        if left_part.isdigit() != right_part.isdigit():
            return -1 if left_part.isdigit() else 1
        return (left_part > right_part) - (left_part < right_part)
    return (len(left.prerelease) > len(right.prerelease)) - (
        len(left.prerelease) < len(right.prerelease)
    )


def _parse_range(value: str) -> tuple[_Comparator, ...]:
    """Parse the narrow, AND-only compatibility range grammar.

    Args:
        value: Comma- or whitespace-separated comparator set.

    Returns:
        Parsed comparator tuple.

    Raises:
        ValueError: If unsupported range syntax is supplied.
    """
    if not value.strip() or any(token in value for token in _FORBIDDEN_RANGE_TOKENS):
        raise ValueError("Unsupported compatibility range grammar")
    tokens = value.replace(",", " ").split()
    if not tokens:
        raise ValueError("Compatibility range requires at least one comparator")
    comparators: list[_Comparator] = []
    for token in tokens:
        match = _COMPARATOR_RE.fullmatch(token)
        if match is None:
            message = f"Invalid compatibility comparator: {token!r}"
            raise ValueError(message)
        comparators.append(
            _Comparator(match.group("operator"), _parse_semver(match.group("version")))
        )
    return tuple(comparators)


def _matches_range(version: _SemVer, comparators: tuple[_Comparator, ...]) -> bool:
    """Return whether a version matches all comparators and prerelease policy."""
    if version.prerelease and not any(item.version.prerelease for item in comparators):
        return False
    for item in comparators:
        comparison = _compare_versions(version, item.version)
        matched = {
            ">": comparison > 0,
            ">=": comparison >= 0,
            "<": comparison < 0,
            "<=": comparison <= 0,
            "=": comparison == 0,
        }[item.operator]
        if not matched:
            return False
    return True


def _failure(
    request_id: Uuid7,
    code: PluginFailureCode,
    status: int,
    title: str,
    detail: str,
) -> PluginFailure:
    """Build a precise redacted failure envelope.

    Returns:
        A structured plugin failure with safe diagnostic detail.
    """
    return PluginFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            type=f"urn:haruquantai:plugins:{code.lower().replace('_', '-')}",
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


def _permission_findings(manifest: PluginManifest) -> tuple[str, ...]:
    """Summarize declared permission categories without exposing values.

    Returns:
        Permission category counts and boolean declarations only.
    """
    permissions = manifest.permissions
    return (
        f"filesystem_read_paths={len(permissions.filesystem_read)}",
        f"filesystem_write_paths={len(permissions.filesystem_write)}",
        f"network_endpoints={len(permissions.network_endpoints)}",
        f"subprocess_declared={str(permissions.subprocess_allow).lower()}",
        f"secret_references={len(permissions.secrets)}",
    )


def _write_reproducible_package(
    package_path: Path,
    manifest: Mapping[str, object],
    payloads: dict[str, bytes],
) -> None:
    """Write a deterministic local reference plugin package.

    Args:
        package_path: Destination ZIP path supplied by the caller.
        manifest: JSON-serializable plugin manifest object.
        payloads: Relative payload paths and their exact bytes.

    Raises:
        ValueError: If a payload path is unsafe or conflicts with the manifest.
    """
    if "plugin.json" in payloads:
        raise ValueError("Payloads must not replace plugin.json")
    for path in payloads:
        normalized = Path(path).as_posix()
        if (
            normalized != path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path.startswith("/")
        ):
            raise ValueError("Reference package payload paths must be safe")
    manifest_bytes = json.dumps(
        manifest, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    ordered_entries = [("plugin.json", manifest_bytes), *sorted(payloads.items())]
    with zipfile.ZipFile(
        package_path, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True
    ) as archive:
        for path, content in ordered_entries:
            info = zipfile.ZipInfo(path, date_time=_REFERENCE_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = _REFERENCE_ZIP_PERMISSIONS
            info.flag_bits = 0
            archive.writestr(info, content, compress_type=zipfile.ZIP_STORED)


def _emit_safe_validation_event(level: int, event: str) -> None:
    """Emit one fixed, value-free validation event through the module logger."""
    record = _LOGGER.makeRecord(
        _LOGGER.name, level, __file__, 0, event, (), None, func="validate_package"
    )
    _LOGGER.handle(record)


class DevelopmentCompatibilityService(MaintainCompatibilityCapability):
    """Validate plugin fixtures and maintain one global compatibility policy."""

    def __init__(
        self,
        config: DevelopmentCompatibilityConfig,
        manifests: DeclareManifestsCapability,
        contributions: RegisterContributionsCapability,
    ) -> None:
        """Initialize the service with required public capability providers."""
        self._config = config
        self._manifests = manifests
        self._contributions = contributions
        self._compatibility: PluginCompatibility | None = None

    def clear(self) -> None:
        """Discard the global in-memory policy during feature removal."""
        self._compatibility = None

    def validate_package(
        self,
        package_path: Path,
        fixtures: tuple[PluginContributionDescriptor, ...] = (),
        implementations: dict[str, object] | None = None,
    ) -> PluginValidationReport | PluginFailure:
        """Validate one supplied package and its optional contribution fixtures.

        Returns:
            A reproducible validation report or a precise failure envelope.
        """
        request_id = str(uuid.uuid7())
        capture = _RedactingLogCapture()
        _LOGGER.addHandler(capture)
        try:
            _emit_safe_validation_event(logging.INFO, "package_validation_started")
            package = self._manifests.validate_package(package_path)
            results: list[ContributionTestResultWire] = []
            for fixture in fixtures:
                result: ContributionTestResult = self._contributions.run_contract_test(
                    fixture, (implementations or {}).get(fixture.contribution_id)
                )
                results.append(
                    ContributionTestResultWire(
                        contribution_id=result.contribution_id,
                        plugin_type=result.plugin_type.value,
                        passed=result.passed,
                        details=result.details,
                        errors=result.errors,
                    )
                )
            all_passed = all(result.passed for result in results)
            _emit_safe_validation_event(logging.INFO, "package_validation_succeeded")
            return PluginValidationReport(
                report_id=request_id,
                plugin_id=package.manifest.id,
                version=package.manifest.version,
                contract_fixture_results=tuple(results),
                permission_simulation_findings=_permission_findings(package.manifest),
                captured_log_counts=capture.counts(),
                package_hash=package.package_hash,
                is_valid=package.is_valid and all_passed,
            )
        except (PluginError, ValueError) as error:
            _emit_safe_validation_event(logging.WARNING, "package_validation_failed")
            return _failure(
                request_id=request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Plugin Package Validation Failed",
                detail=str(error),
            )
        finally:
            _LOGGER.removeHandler(capture)

    @override
    async def maintain_compatibility(  # noqa: PLR0911
        self, request: MaintainCompatibilityRequest
    ) -> MaintainCompatibilitySuccess | PluginFailure:
        """Publish or check the active plugin API compatibility policy.

        Returns:
            A success response for a valid publication/check or a failure envelope.
        """
        if request.operation == "PUBLISH":
            if request.compatibility is None:
                return _failure(
                    request.request_id,
                    "PLUGIN_VALIDATION_FAILED",
                    400,
                    "Missing Compatibility Policy",
                    "PUBLISH requires a compatibility declaration",
                )
            try:
                _parse_range(request.compatibility.supported_range)
            except ValueError as error:
                return _failure(
                    request.request_id,
                    "PLUGIN_VALIDATION_FAILED",
                    400,
                    "Invalid Compatibility Range",
                    str(error),
                )
            self._compatibility = request.compatibility
            return MaintainCompatibilitySuccess(
                request_id=request.request_id,
                compatibility=request.compatibility,
            )

        if request.plugin_id is None or request.version is None:
            return _failure(
                request.request_id,
                "PLUGIN_VALIDATION_FAILED",
                400,
                "Missing Compatibility Check Fields",
                "CHECK requires plugin_id and version",
            )
        compatibility = self._compatibility
        if compatibility is None:
            return _failure(
                request.request_id,
                "PLUGIN_INCOMPATIBLE",
                409,
                "No Compatibility Policy Published",
                (
                    f"Plugin '{request.plugin_id}' cannot be checked before policy "
                    "publication"
                ),
            )
        try:
            requested_version = _parse_semver(request.version)
            comparators = _parse_range(compatibility.supported_range)
        except ValueError as error:
            return _failure(
                request.request_id,
                "PLUGIN_VALIDATION_FAILED",
                400,
                "Invalid Compatibility Check",
                str(error),
            )
        if not _matches_range(requested_version, comparators):
            return _failure(
                request.request_id,
                "PLUGIN_INCOMPATIBLE",
                409,
                "Unsupported Plugin API Version",
                (
                    f"Plugin '{request.plugin_id}' API version {request.version} is "
                    "outside the published supported range"
                ),
            )
        return MaintainCompatibilitySuccess(
            request_id=request.request_id,
            verdict="DEPRECATED" if compatibility.is_deprecated else "SUPPORTED",
        )


def fr_plug_validate_plugin_packages(
    package_path: Path,
    manifests: DeclareManifestsCapability,
    contributions: RegisterContributionsCapability,
    fixtures: tuple[PluginContributionDescriptor, ...] = (),
) -> PluginValidationReport | PluginFailure:
    """Trace FR-PLUG-VALIDATE_PLUGIN_PACKAGES through public capabilities.

    Returns:
        A plugin validation report or a structured failure.
    """
    service = DevelopmentCompatibilityService(
        config=DevelopmentCompatibilityConfig(),
        manifests=manifests,
        contributions=contributions,
    )
    return service.validate_package(package_path, fixtures)


def fr_plug_declare_plugin_compatibility(
    request: MaintainCompatibilityRequest,
    service: DevelopmentCompatibilityService,
) -> MaintainCompatibilitySuccess | PluginFailure:
    """Trace FR-PLUG-DECLARE_PLUGIN_COMPATIBILITY through the public port.

    Returns:
        The compatibility publication/check result.
    """
    return asyncio.run(service.maintain_compatibility(request))


class _ReferenceManifestAdapter:
    """Usage-only manifest adapter for the deterministic reference package."""

    def parse_manifest(self, raw: str | bytes | dict[str, Any]) -> PluginManifest:
        """Parse the bounded reference manifest used by the executable example.

        Returns:
            The public manifest record for the reference artifact.
        """
        decoded = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        return PluginManifest(
            id=str(decoded["id"]),
            version=str(decoded["version"]),
            api_range=str(decoded["apiRange"]),
            types=tuple(PluginType(value) for value in decoded.get("type", ())),
            entry_point=str(decoded["entryPoint"]),
        )

    def validate_manifest(self, manifest: PluginManifest) -> None:
        """Reject any manifest outside the one bounded usage fixture.

        Raises:
            ValueError: If the manifest is not the reference fixture.
        """
        if (
            manifest.id != "com.haruquantai.reference"
            or manifest.version != "1.0.0"
            or manifest.entry_point != "plugin.py"
        ):
            raise ValueError("Unexpected reference manifest")

    def validate_package(self, package_path: Path) -> PluginPackageValidation:
        """Validate and describe the deterministic local reference ZIP.

        Returns:
            The public package-validation record for the reference artifact.

        Raises:
            ValueError: If the ZIP contents differ from the reference fixture.
        """
        with zipfile.ZipFile(package_path) as archive:
            names = tuple(sorted(archive.namelist()))
            if names != ("plugin.json", "plugin.py"):
                raise ValueError("Unexpected reference package contents")
            manifest = self.parse_manifest(archive.read("plugin.json"))
            self.validate_manifest(manifest)
            files = tuple(
                PluginFileEntry(
                    path=name,
                    sha256=hashlib.sha256(archive.read(name)).hexdigest(),
                    size_bytes=len(archive.read(name)),
                )
                for name in names
            )
        return PluginPackageValidation(
            manifest=manifest,
            package_hash=hashlib.sha256(package_path.read_bytes()).hexdigest(),
            files=files,
        )

    def compute_package_hash(
        self, manifest: PluginManifest, file_hashes: dict[str, str]
    ) -> str:
        """Reject unsupported use outside local package validation."""
        del manifest, file_hashes
        raise NotImplementedError("Usage adapter supports validate_package only")


class _ReferenceContributionsAdapter:
    """Usage-only contribution adapter for the fixture-free example."""

    def register_contributions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
        implementations: dict[str, object] | None = None,
    ) -> ContributionRegistrationResult:
        """Reject unsupported registration in the fixture-free example."""
        del manifest, contributions, implementations
        raise NotImplementedError("Usage adapter does not register contributions")

    def unregister_contributions(self, plugin_id: str) -> int:
        """Reject unsupported removal in the fixture-free example."""
        del plugin_id
        raise NotImplementedError("Usage adapter does not register contributions")

    def get_contributions(
        self, plugin_type: PluginType | None = None
    ) -> tuple[PluginContributionDescriptor, ...]:
        """Return the empty fixture set used by the example."""
        del plugin_type
        return ()

    def get_contribution(
        self, contribution_id: str
    ) -> PluginContributionDescriptor | None:
        """Return no contribution from the empty fixture set."""
        del contribution_id
        return None

    def run_contract_test(
        self,
        contribution: PluginContributionDescriptor,
        implementation: object | None = None,
    ) -> ContributionTestResult:
        """Reject contract tests because the example supplies no fixtures."""
        del contribution, implementation
        raise NotImplementedError("Usage adapter has no contribution fixtures")


def _run_usage_example() -> None:
    """Run bounded package-validation and compatibility scenarios.

    Raises:
        TypeError: The reference package or compatibility check fails.
    """
    from tempfile import TemporaryDirectory

    manifests = _ReferenceManifestAdapter()
    contributions = _ReferenceContributionsAdapter()
    service = DevelopmentCompatibilityService(
        DevelopmentCompatibilityConfig(), manifests, contributions
    )
    with TemporaryDirectory() as directory:
        package_path = Path(directory) / "reference-plugin.zip"
        duplicate_path = Path(directory) / "reference-plugin-copy.zip"
        manifest = {
            "apiRange": ">=1.0.0 <2.0.0",
            "entryPoint": "plugin.py",
            "id": "com.haruquantai.reference",
            "permissions": {},
            "resources": {},
            "type": ["METRIC"],
            "version": "1.0.0",
        }
        payloads = {"plugin.py": b"def compute(): return 1\n"}
        _write_reproducible_package(package_path, manifest, payloads)
        _write_reproducible_package(duplicate_path, manifest, payloads)
        if package_path.read_bytes() != duplicate_path.read_bytes():
            raise TypeError("Reference package is not reproducible")
        report = service.validate_package(package_path)
        if not isinstance(report, PluginValidationReport) or not report.is_valid:
            raise TypeError("Reference package validation failed")
        if report.captured_log_counts.get("info") != _EXPECTED_CAPTURED_INFO_EVENTS:
            raise TypeError("Reference package log capture is incomplete")
    publish = MaintainCompatibilityRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="PUBLISH",
        compatibility=PluginCompatibility(
            plugin_api_version="2.0.0",
            supported_range=">=1.0.0 <2.0.0",
            conformance_suite="plugins-v1",
        ),
    )
    published = asyncio.run(service.maintain_compatibility(publish))
    if not isinstance(published, MaintainCompatibilitySuccess):
        raise TypeError("Compatibility publication failed")
    checked = asyncio.run(
        service.maintain_compatibility(
            MaintainCompatibilityRequest(
                request_id=str(uuid.uuid7()),
                capability_snapshot_id=str(uuid.uuid7()),
                operation="CHECK",
                plugin_id="com.haruquantai.reference",
                version="1.5.0",
            )
        )
    )
    if not isinstance(checked, MaintainCompatibilitySuccess):
        raise TypeError("Compatibility check did not return success")
    if checked.verdict != "SUPPORTED":
        raise TypeError("Compatibility check failed")
    print("FR-PLUG-VALIDATE_PLUGIN_PACKAGES: reference package validated")
    print("FR-PLUG-DECLARE_PLUGIN_COMPATIBILITY: compatible API accepted")


if __name__ == "__main__":
    _run_usage_example()
