"""Scoped mount adapter for FEAT-WS-MANAGE_ARTIFACTS."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import (
    MANAGE_ARTIFACTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.services.workspace.manage_artifacts.config import (
    ManageArtifactsConfig,
    from_dict,
)
from app.services.workspace.manage_artifacts.manage_artifacts import (
    ManageArtifactsService,
)
from app.services.workspace.manage_artifacts.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec

logger = get_logger(__name__)


class ManageArtifactsFeature:
    """Mount and withdraw one artifact custody provider."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the mount adapter.

        Args:
            spec: Immutable feature specification to mount under.
        """
        self.spec = spec
        self._service: ManageArtifactsService | None = None

    @property
    def service(self) -> ManageArtifactsService | None:
        """Return the mounted custody service, or None while unmounted."""
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the artifact custody provider into one feature scope.

        Args:
            context: Scoped feature context owning capability
                registration and disposal callbacks.
            config: Feature configuration mapping, or a pre-parsed
                :class:`ManageArtifactsConfig`.

        Raises:
            TypeError: If the configuration has an unsupported type.
            ValueError: If the configuration contains unknown keys or
                invalid values.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageArtifactsConfig):
            parsed = config
        else:
            raise TypeError(
                "manage-artifacts configuration must be a mapping or "
                "ManageArtifactsConfig"
            )
        persistence = context.require(PERSISTENCE_CAPABILITY)
        admission = context.optional(RESERVE_RESOURCES_CAPABILITY)
        service = ManageArtifactsService(
            config=parsed,
            persistence=persistence,
            admission=admission,
        )

        def _unmount_callback() -> None:
            service.close()

        context.register_callback(_unmount_callback)
        context.provide(MANAGE_ARTIFACTS_CAPABILITY, service)
        self._service = service
        logger.info(
            "artifact custody feature mounted",
            extra={
                "feature_id": self.spec.feature_id,
                "admission_gated": admission is not None,
            },
        )


def feature() -> ManageArtifactsFeature:
    """Return one artifact custody feature adapter instance.

    Returns:
        Fresh mount adapter for composition discovery.
    """
    return ManageArtifactsFeature()


def create_feature() -> ManageArtifactsFeature:
    """Return one artifact custody feature adapter instance.

    Returns:
        Fresh mount adapter (canonical factory alias).
    """
    return ManageArtifactsFeature()


__all__ = [
    "ManageArtifactsFeature",
    "create_feature",
    "feature",
]
