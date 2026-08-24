"""Error types for the Plugins domain."""

from __future__ import annotations


class PluginError(Exception):
    """Base exception for all plugins domain errors."""


class PluginManifestError(PluginError):
    """Raised when a plugin manifest is malformed, invalid, or incompatible."""


class PluginPackageValidationError(PluginError):
    """Raised when a plugin package fails structural or hash verification."""


class PluginSignatureError(PluginError):
    """Raised when a plugin signature cannot be verified or is invalid."""


class PluginContributionError(PluginError):
    """Raised when registering or validating a plugin contribution fails."""


class PluginContractTestError(PluginContributionError):
    """Raised when a contribution fails its type-specific contract test."""
