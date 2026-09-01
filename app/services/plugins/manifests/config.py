"""Configuration parser for the Plugin Manifests feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {"max_package_size_bytes", "max_file_count", "strict_signatures"}
)


@dataclass(frozen=True, slots=True)
class PluginManifestsConfig:
    """Strict immutable configuration for plugin manifest and package validation."""

    max_package_size_bytes: int = 50 * 1024 * 1024
    max_file_count: int = 1000
    strict_signatures: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PluginManifestsConfig:
        """Parse and validate configuration dictionary.

        Args:
            data: Raw configuration mapping or None.

        Returns:
            Validated PluginManifestsConfig instance.

        Raises:
            ValueError: If unknown keys or invalid value ranges are provided.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Plugin Manifests configuration keys: "
                + ", ".join(sorted(unknown))
            )

        max_size = int(data.get("max_package_size_bytes", 50 * 1024 * 1024))
        if max_size <= 0:
            raise ValueError("max_package_size_bytes must be positive")

        max_files = int(data.get("max_file_count", 1000))
        if max_files <= 0:
            raise ValueError("max_file_count must be positive")

        strict_sigs = bool(data.get("strict_signatures", False))

        return cls(
            max_package_size_bytes=max_size,
            max_file_count=max_files,
            strict_signatures=strict_sigs,
        )
