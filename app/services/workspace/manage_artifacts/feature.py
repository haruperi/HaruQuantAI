"""Feature lifecycle for immutable artifact custody."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY, PERSISTENCE_CAPABILITY
from app.services.workspace.manage_artifacts.config import ManageArtifactsConfig, from_dict
from app.services.workspace.manage_artifacts.manage_artifacts import ManageArtifactsService
from app.services.workspace.manage_artifacts.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ManageArtifactsFeature:
    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: ManageArtifactsService | None = None

    async def mount(self, context: FeatureContext, config: object) -> None:
        if config is None or isinstance(config, dict):
            from_dict(config)
        elif not isinstance(config, ManageArtifactsConfig):
            raise TypeError("manage-artifacts configuration must be a mapping, ManageArtifactsConfig, or None")
        service = ManageArtifactsService(context.require(PERSISTENCE_CAPABILITY), context.require(RESERVE_RESOURCES_CAPABILITY))
        context.register_callback(service.close)
        context.provide(ARTIFACTS_CAPABILITY, service)
        self._service = service


def feature() -> ManageArtifactsFeature:
    return ManageArtifactsFeature()
