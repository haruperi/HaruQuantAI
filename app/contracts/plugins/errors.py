"""Error types for the Plugins domain."""

from __future__ import annotations

from typing import Literal

# These wire aliases and base classes are annotation-only for readers but
# Pydantic resolves them at class-creation time, so they must remain runtime
# imports.
from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
    WireModel,
)


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


# Closed plugins failure-code union from the ratified v1 operation rules,
# shared by the five new Plugins capabilities.
type PluginFailureCode = Literal[
    "PLUGIN_VALIDATION_FAILED",
    "PLUGIN_MANIFEST_INVALID",
    "PLUGIN_PACKAGE_INVALID",
    "PLUGIN_SIGNATURE_INVALID",
    "PLUGIN_CONTRIBUTION_INVALID",
    "PLUGIN_CONTRACT_TEST_FAILED",
    "PLUGIN_PERMISSION_DENIED",
    "PLUGIN_SECRET_FORBIDDEN",
    "PLUGIN_INCOMPATIBLE",
    "PLUGIN_LIFECYCLE_CONFLICT",
    "CAPABILITY_UNAVAILABLE",
]


class PluginFailure(WireModel):
    """Structured failure envelope shared by the new Plugins capabilities.

    ``PLUGIN_VALIDATION_FAILED`` covers harness validation failures,
    ``PLUGIN_MANIFEST_INVALID`` and ``PLUGIN_PACKAGE_INVALID`` cover
    malformed or altered manifests and packages, ``PLUGIN_SIGNATURE_INVALID``
    covers unverifiable signatures, ``PLUGIN_CONTRIBUTION_INVALID`` and
    ``PLUGIN_CONTRACT_TEST_FAILED`` cover registration and contract-test
    failures, ``PLUGIN_PERMISSION_DENIED`` covers sandbox denials,
    ``PLUGIN_SECRET_FORBIDDEN`` covers undeclared secret access,
    ``PLUGIN_INCOMPATIBLE`` covers unsupported API ranges,
    ``PLUGIN_LIFECYCLE_CONFLICT`` covers transactional lifecycle conflicts,
    and ``CAPABILITY_UNAVAILABLE`` performs no mutation.
    """

    outcome: Literal["FAILURE"] = "FAILURE"
    request_id: Uuid7
    code: PluginFailureCode
    problem: ProblemDetails
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "PluginFailure": PluginFailure,
}
