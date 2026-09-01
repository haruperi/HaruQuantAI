"""Feature lifecycle mount implementation for Distributed Worker Pool."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import (
    DISTRIBUTE_WORKERS_CAPABILITY,
)
from app.services.workspace.distributed_worker_pool.config import (
    DistributedWorkerPoolConfig,
)
from app.services.workspace.distributed_worker_pool.distributed_worker_pool import (
    DistributedWorkerPoolService,
)
from app.services.workspace.distributed_worker_pool.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DistributedWorkerPoolFeature:
    """Composable feature package providing Distributed Worker Pool capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: DistributedWorkerPoolService | None = None

    @property
    def service(self) -> DistributedWorkerPoolService | None:
        """Return the underlying service instance if mounted.

        Returns:
            DistributedWorkerPoolService instance or None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the distribute workers capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        self._service = DistributedWorkerPoolService(
            config=DistributedWorkerPoolConfig(),
        )
        context.provide(DISTRIBUTE_WORKERS_CAPABILITY, self._service)


def feature() -> DistributedWorkerPoolFeature:
    """Factory function for discovery via entry points.

    Returns:
        New DistributedWorkerPoolFeature instance.
    """
    return DistributedWorkerPoolFeature()
