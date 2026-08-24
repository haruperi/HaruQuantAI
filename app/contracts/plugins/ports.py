"""Public capability protocols (ports) for plugin manifests and packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from app.contracts.plugins.models import (
        PluginManifest,
        PluginPackageValidation,
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
