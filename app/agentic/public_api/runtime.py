"""Canonical durable composition for the Agentic public API."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.agentic.context_memory.runtime import DurableMemoryStore
from app.agentic.lifecycle.runtime import DurableLifecycleStore
from app.agentic.operations.runtime import DurableOperationsStore
from app.agentic.orchestration.runtime import DurableWorkflowStore
from app.agentic.public_api.dependencies import (
    AgenticDependencies,
    build_agentic_dependencies,
)
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from app.agentic._settings import AgenticSettings
    from app.agentic.governance.models import FirmMandate
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.orchestration.models import WorkflowDefinition
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)


def build_durable_agentic_dependencies(
    settings: AgenticSettings,
    mandate: FirmMandate,
    registry: RoleRegistry,
    definitions: Mapping[str, WorkflowDefinition],
    agent_policies: Mapping[str, AgentPolicy],
    tool_policies: Mapping[str, ToolPolicy],
) -> AgenticDependencies:
    """Build the complete Agentic dependency bundle with durable stores.

    Returns:
        Fully wired Agentic dependencies.
    """
    logger.info("Building durable Agentic public-API dependencies")
    return build_agentic_dependencies(
        settings,
        mandate,
        registry,
        DurableWorkflowStore(),
        DurableMemoryStore(),
        DurableOperationsStore(),
        DurableLifecycleStore(),
        definitions,
        agent_policies,
        tool_policies,
    )


__all__ = ("build_durable_agentic_dependencies",)
