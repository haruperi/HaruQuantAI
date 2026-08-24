"""Feature lifecycle mount implementation for Diagnostic Bundle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import (
    BUILD_DIAGNOSTICS_CAPABILITY,
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.services.workspace.diagnostic_bundle.config import (
    DiagnosticBundleConfig,
)
from app.services.workspace.diagnostic_bundle.diagnostic_bundle import (
    DiagnosticBundleService,
)
from app.services.workspace.diagnostic_bundle.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DiagnosticBundleFeature:
    """Composable feature package providing Diagnostic Bundle capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: DiagnosticBundleService | None = None

    @property
    def service(self) -> DiagnosticBundleService | None:
        """Return the underlying service instance if mounted.

        Returns:
            DiagnosticBundleService instance or None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the build diagnostics capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        manage_workspaces = context.require(MANAGE_WORKSPACES_CAPABILITY)
        configure_runtime = context.require(CONFIGURE_RUNTIME_CAPABILITY)
        secure_local_access = context.optional(SECURE_LOCAL_ACCESS_CAPABILITY)
        self._service = DiagnosticBundleService(
            config=DiagnosticBundleConfig(),
            manage_workspaces=manage_workspaces,
            configure_runtime=configure_runtime,
            secure_local_access=secure_local_access,
        )
        context.provide(BUILD_DIAGNOSTICS_CAPABILITY, self._service)


def feature() -> DiagnosticBundleFeature:
    """Factory function for discovery via entry points.

    Returns:
        New DiagnosticBundleFeature instance.
    """
    return DiagnosticBundleFeature()
