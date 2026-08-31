"""Public capability protocols (ports) for plugin manifests and packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from app.contracts.plugins.errors import PluginFailure
    from app.contracts.plugins.models import (
        ContributionRegistrationResult,
        ContributionTestResult,
        IsolateAnalysisRequest,
        IsolateAnalysisSuccess,
        MaintainCompatibilityRequest,
        MaintainCompatibilitySuccess,
        ManageLifecycleRequest,
        ManageLifecycleSuccess,
        PluginContributionDescriptor,
        PluginManifest,
        PluginPackageValidation,
        PluginType,
        RenderResultPanelsRequest,
        RenderResultPanelsSuccess,
        SandboxPermissionsRequest,
        SandboxPermissionsSuccess,
    )


@runtime_checkable
class DeclareManifestsCapability(Protocol):
    """Capability protocol for declaring, parsing, and validating plugin manifests."""

    def parse_manifest(self, raw: str | bytes | dict[str, Any]) -> PluginManifest:
        """Parse raw manifest data into a validated PluginManifest instance.

        Args:
            raw: JSON string, raw bytes, or dictionary representation of plugin.json.

        Returns:
            Validated PluginManifest instance.

        Raises:
            PluginManifestError: If raw data is malformed or validation fails.
        """
        ...

    def validate_manifest(self, manifest: PluginManifest) -> None:
        """Validate all fields, constraints, and semantics of a PluginManifest.

        Args:
            manifest: The plugin manifest instance to validate.

        Raises:
            PluginManifestError: If any semantic rule or constraint is violated.
        """
        ...

    def validate_package(self, package_path: Path) -> PluginPackageValidation:
        """Inspect and validate a plugin ZIP archive and its inner manifest.

        Args:
            package_path: Filesystem path to the plugin .zip package archive.

        Returns:
            PluginPackageValidation describing the validated manifest and hash.

        Raises:
            PluginPackageValidationError: If the archive is invalid or unsafe.
        """
        ...

    def compute_package_hash(
        self,
        manifest: PluginManifest,
        file_hashes: dict[str, str],
    ) -> str:
        """Compute the canonical SHA-256 package hash.

        Args:
            manifest: The plugin manifest.
            file_hashes: Mapping of normalized relative paths to SHA-256 strings.

        Returns:
            Hexadecimal SHA-256 string representing the canonical package hash.
        """
        ...


@runtime_checkable
class RegisterContributionsCapability(Protocol):
    """Capability protocol for registering and contract-testing plugin contributions."""

    def register_contributions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
        implementations: dict[str, object] | None = None,
    ) -> ContributionRegistrationResult:
        """Register typed contributions declared by a plugin manifest.

        Args:
            manifest: Validated plugin manifest.
            contributions: Descriptors of contributions to register.
            implementations: Optional mapping of contribution IDs to implementation.

        Returns:
            ContributionRegistrationResult containing descriptors and test outcomes.

        Raises:
            PluginContributionError: If registration fails or violates boundaries.
            PluginContractTestError: If strict contract verification fails.
        """
        ...

    def unregister_contributions(self, plugin_id: str) -> int:
        """Unregister all contributions associated with a plugin ID.

        Args:
            plugin_id: Identifier of the plugin to withdraw.

        Returns:
            Count of removed contribution descriptors.
        """
        ...

    def get_contributions(
        self, plugin_type: PluginType | None = None
    ) -> tuple[PluginContributionDescriptor, ...]:
        """Query currently registered plugin contributions.

        Args:
            plugin_type: Optional filter by PluginType.

        Returns:
            Tuple of active contribution descriptors matching criteria.
        """
        ...

    def get_contribution(
        self, contribution_id: str
    ) -> PluginContributionDescriptor | None:
        """Retrieve a registered contribution by its ID.

        Args:
            contribution_id: Unique contribution identifier.

        Returns:
            PluginContributionDescriptor if found, or None.
        """
        ...

    def run_contract_test(
        self,
        contribution: PluginContributionDescriptor,
        implementation: object | None = None,
    ) -> ContributionTestResult:
        """Execute type-specific contract tests against a contribution.

        Args:
            contribution: Contribution descriptor to test.
            implementation: Optional concrete implementation object or mock.

        Returns:
            ContributionTestResult indicating whether contract rules were satisfied.
        """
        ...


@runtime_checkable
class ManageLifecycleCapability(Protocol):
    """Capability protocol for transactional plugin lifecycle operations."""

    async def manage_lifecycle(
        self,
        request: ManageLifecycleRequest,
    ) -> ManageLifecycleSuccess | PluginFailure:
        """Install, enable, disable, upgrade, or remove plugins transactionally.

        Args:
            request: Operation-discriminated plugin lifecycle request.

        Returns:
            The resulting activation and lifecycle state on success,
            otherwise a structured plugins failure.
        """
        ...


@runtime_checkable
class SandboxPermissionsCapability(Protocol):
    """Capability protocol for plugin sandbox grant, inspection, and execution."""

    async def sandbox_permissions(
        self,
        request: SandboxPermissionsRequest,
    ) -> SandboxPermissionsSuccess | PluginFailure:
        """Grant, inspect, or execute narrowed plugin sandbox permissions.

        Args:
            request: Operation-discriminated plugin sandbox permission
                request.

        Returns:
            The effective permission set on success, otherwise a structured
            plugins failure.
        """
        ...


@runtime_checkable
class IsolateAnalysisCapability(Protocol):
    """Capability protocol for isolated plugin analysis boundary execution."""

    async def isolate_analysis(
        self,
        request: IsolateAnalysisRequest,
    ) -> IsolateAnalysisSuccess | PluginFailure:
        """Run one plugin analysis with immutable handles and staged output.

        Args:
            request: Operation-discriminated plugin analysis boundary
                request.

        Returns:
            The staged analysis result on success, otherwise a structured
            plugins failure.
        """
        ...


@runtime_checkable
class RenderResultPanelsCapability(Protocol):
    """Capability protocol for sandboxed plugin result panel description."""

    async def render_result_panels(
        self,
        request: RenderResultPanelsRequest,
    ) -> RenderResultPanelsSuccess | PluginFailure:
        """Describe or resolve sandboxed plugin result panels.

        Args:
            request: Operation-discriminated plugin result panel request.

        Returns:
            The matching panel descriptors on success, otherwise a
            structured plugins failure.
        """
        ...


@runtime_checkable
class MaintainCompatibilityCapability(Protocol):
    """Capability protocol for plugin API compatibility publication and checks."""

    async def maintain_compatibility(
        self,
        request: MaintainCompatibilityRequest,
    ) -> MaintainCompatibilitySuccess | PluginFailure:
        """Publish plugin API compatibility or check one plugin version.

        Args:
            request: Operation-discriminated plugin compatibility request.

        Returns:
            The published compatibility declaration or the check verdict on
            success, otherwise a structured plugins failure.
        """
        ...
