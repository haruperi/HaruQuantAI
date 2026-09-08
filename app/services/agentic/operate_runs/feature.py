"""Lifecycle for Agentic operations/readiness."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, OPERATIONS_CAPABILITY
from app.contracts.workspace.capabilities import PERSISTENCE_CAPABILITY
from app.services.agentic.operate_runs.config import OperateRunsConfig, from_dict
from app.services.agentic.operate_runs.manifest import SPEC
from app.services.agentic.operate_runs.operate_runs import OperateRunsService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class OperateRunsFeature:
    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        parsed = from_dict(config if isinstance(config, dict) or config is None else None) if not isinstance(config, OperateRunsConfig) else config
        context.require(MANDATE_CAPABILITY)
        service = OperateRunsService(context.require(PERSISTENCE_CAPABILITY), parsed.max_payload_chars)
        context.register_callback(service.close)
        context.provide(OPERATIONS_CAPABILITY, service)


def feature() -> OperateRunsFeature:
    return OperateRunsFeature()
