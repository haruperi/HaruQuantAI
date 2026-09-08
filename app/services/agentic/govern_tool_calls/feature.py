"""Lifecycle for Agentic tool governance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, OPERATIONS_CAPABILITY, ROLES_CAPABILITY, TOOL_GOVERNANCE_CAPABILITY
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY, PERSISTENCE_CAPABILITY
from app.services.agentic.govern_tool_calls.config import GovernToolCallsConfig, from_dict
from app.services.agentic.govern_tool_calls.govern_tool_calls import GovernToolCallsService
from app.services.agentic.govern_tool_calls.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class GovernToolCallsFeature:
    spec = SPEC
    async def mount(self, context: FeatureContext, config: object) -> None:
        parsed = config if isinstance(config, GovernToolCallsConfig) else from_dict(config if isinstance(config, dict) or config is None else None)
        context.require(PERSISTENCE_CAPABILITY)
        service = GovernToolCallsService(context.require(MANDATE_CAPABILITY), context.require(ROLES_CAPABILITY), context.require(OPERATIONS_CAPABILITY), context.require(MANAGE_ACCOUNTS_CAPABILITY), context.require(RESERVE_RESOURCES_CAPABILITY), parsed.max_result_bytes)
        context.register_callback(service.close); context.provide(TOOL_GOVERNANCE_CAPABILITY, service)


def feature() -> GovernToolCallsFeature: return GovernToolCallsFeature()
