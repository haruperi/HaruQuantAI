"""Lifecycle for the job/resource/worker translation gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.interfaces.capabilities import OPERATE_JOBS_CAPABILITY
from app.contracts.orchestration.capabilities import (
    LOCAL_WORKERS_CAPABILITY,
    MANAGE_JOBS_CAPABILITY,
    RESERVE_RESOURCES_CAPABILITY,
)
from app.services.interfaces.operate_jobs.config import OperateJobsConfig, from_dict
from app.services.interfaces.operate_jobs.gateway import JobsGateway
from app.services.interfaces.operate_jobs.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class OperateJobsFeature:
    """Mount one translation-only jobs gateway."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve exact owner capabilities and publish the interface."""
        if isinstance(config, OperateJobsConfig):
            parsed = config
        elif config is None or isinstance(config, dict):
            parsed = from_dict(config)
        else:
            raise TypeError("operate-jobs config must be a mapping or OperateJobsConfig")
        del parsed
        gateway = JobsGateway(
            context.require(MANAGE_JOBS_CAPABILITY),
            context.require(RESERVE_RESOURCES_CAPABILITY),
            context.require(LOCAL_WORKERS_CAPABILITY),
        )
        context.register_callback(gateway.close)
        context.provide(OPERATE_JOBS_CAPABILITY, gateway)


def feature() -> OperateJobsFeature:
    """Return a new feature adapter."""
    return OperateJobsFeature()
