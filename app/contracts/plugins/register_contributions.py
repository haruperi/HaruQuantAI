"""Public contract for registering and disposing plugin contributions.

Provides the ``RegisterContributionsCapability`` protocol, ``ContributionDisposer``
handle protocol, and versioned metadata models for typed contribution registration,
exact generation tracking, conflict rejection, and deterministic exposure.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.contracts.plugins.errors import (
    PluginContractTestError,
    PluginContributionError,
)
from app.contracts.plugins.models import (
    ContributionRegistrationResult,
    ContributionTestResult,
    PluginContributionDescriptor,
    PluginManifest,
    PluginType,
)
from app.contracts.plugins.ports import (
    RegisterContributionsCapability,
)


@runtime_checkable
class ContributionDisposer(Protocol):
    """Disposer handle for a specific generation of plugin contributions."""

    def __call__(self) -> int:
        """Dispose the bound generation when called directly as a callable."""
        ...

    def dispose(self) -> int:
        """Dispose the bound generation explicitly."""
        ...


__all__ = [
    "REGISTER_CONTRIBUTIONS_CAPABILITY",
    "ContributionDisposer",
    "ContributionRegistrationResult",
    "ContributionTestResult",
    "PluginContractTestError",
    "PluginContributionDescriptor",
    "PluginContributionError",
    "PluginManifest",
    "PluginType",
    "RegisterContributionsCapability",
]
