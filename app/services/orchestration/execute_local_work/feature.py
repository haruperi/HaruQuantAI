"""Lifecycle for spawn-safe local work."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.orchestration.capabilities import LOCAL_WORKERS_CAPABILITY, MANAGE_JOBS_CAPABILITY, RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY
from app.services.orchestration.execute_local_work.config import ExecuteLocalWorkConfig, from_dict
from app.services.orchestration.execute_local_work.execute_local_work import ExecuteLocalWorkService
from app.services.orchestration.execute_local_work.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ExecuteLocalWorkFeature:
    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        parsed = config if isinstance(config, ExecuteLocalWorkConfig) else from_dict(config if isinstance(config, dict) or config is None else None)
        context.require(ARTIFACTS_CAPABILITY)
        service = ExecuteLocalWorkService(context.require(MANAGE_JOBS_CAPABILITY), context.require(RESERVE_RESOURCES_CAPABILITY), parsed.max_input_bytes, parsed.cancellation_grace_seconds)
        context.register_callback(service.close); context.provide(LOCAL_WORKERS_CAPABILITY, service)


def feature() -> ExecuteLocalWorkFeature:
    return ExecuteLocalWorkFeature()
