"""Lifecycle adapter for durable job management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.orchestration.capabilities import MANAGE_JOBS_CAPABILITY
from app.services.orchestration.manage_jobs._persistence import JobStore
from app.services.orchestration.manage_jobs.config import ManageJobsConfig, from_dict
from app.services.orchestration.manage_jobs.manage_jobs import ManageJobsService
from app.services.orchestration.manage_jobs.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ManageJobsFeature:
    """Mount one lifecycle-owned job service."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Build and register the configured service.

        Args:
            context: Lifecycle-owned feature context.
            config: Mapping, parsed configuration, or None.

        Raises:
            TypeError: If config has an unsupported type.
            ValueError: If config contains invalid values.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageJobsConfig):
            parsed = config
        else:
            raise TypeError("manage-jobs config must be a mapping or ManageJobsConfig")
        service = ManageJobsService(
            JobStore(parsed.database_path),
            parsed.callback_queue_capacity,
            context.spawn,
        )
        context.register_callback(service.close)
        context.provide(MANAGE_JOBS_CAPABILITY, service)


def feature() -> ManageJobsFeature:
    """Return a new job feature instance.

    Returns:
        New feature adapter.
    """
    return ManageJobsFeature()
