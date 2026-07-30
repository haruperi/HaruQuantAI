"""Explicit typed composition dependencies for the public Agentic API.

`FR-AGENTIC-064` requires explicit dependencies. `AgenticDependencies` is a
frozen record in which every port a public operation could need is a **required
field**: there is no default, no lazy lookup, and no module-level singleton, so
a caller cannot invoke an operator operation against a partially wired firm and
discover the gap at the point where it matters least.

The stores are Protocols the owning features declare. This module binds nothing
and constructs nothing; an approved composition root supplies the concrete
implementations, which is the same arrangement every store in this domain has.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.agentic._settings import AgenticSettings
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.lifecycle.repository import AgenticLifecycleStore
    from app.agentic.operations.repository import AgenticOperationsStore
    from app.agentic.orchestration.models import WorkflowDefinition
    from app.agentic.orchestration.repository import AgenticWorkflowStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)


@runtime_checkable
class AuthenticatedPrincipal(Protocol):
    """The authenticated identity every public operation requires.

    Utils exposes `create_auth_context` but not the `AuthContext` class, so
    this structural Protocol names only the fields the boundary reads. A real
    `utils.auth_context.v1` satisfies it without a deep import. The same shape
    `FEAT-AGT-16` and `FEAT-AGT-18` use, stated once more rather than widened.

    Attributes:
        principal_id: Authenticated identity.
        principal_type: Whether the principal is a user or a service account.
        permissions: Fine-grained permissions the principal holds.
        tenant_or_environment: Environment the context was issued for.
        request_id: Trace identifier of the outer request.
        workflow_id: Trace identifier of the orchestrating workflow.
        correlation_id: Trace identifier tracking the whole flow.
    """

    principal_id: str
    principal_type: str
    permissions: tuple[str, ...]
    tenant_or_environment: str
    request_id: str
    workflow_id: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class AgenticDependencies:
    """Every port and policy the public Agentic operations require.

    Attributes:
        settings: Resolved Agentic settings, including master enablement.
        mandate: Validated signed firm mandate.
        registry: Validated role registry.
        workflow_store: Durable workflow store.
        memory_store: Governed memory and audit store.
        operations_store: Operations, incident, and replay store.
        lifecycle_store: Append-only artefact lifecycle ledger.
        definitions: Registered workflow definition per workflow name.
        agent_policies: Registered agent policy per role.
        tool_policies: Registered tool policy per tool name.
    """

    settings: AgenticSettings
    mandate: FirmMandate
    registry: RoleRegistry
    workflow_store: AgenticWorkflowStore
    memory_store: AgenticMemoryStore
    operations_store: AgenticOperationsStore
    lifecycle_store: AgenticLifecycleStore
    definitions: Mapping[str, WorkflowDefinition]
    agent_policies: Mapping[str, AgentPolicy]
    tool_policies: Mapping[str, ToolPolicy]


def build_agentic_dependencies(
    settings: AgenticSettings,
    mandate: FirmMandate,
    registry: RoleRegistry,
    workflow_store: AgenticWorkflowStore,
    memory_store: AgenticMemoryStore,
    operations_store: AgenticOperationsStore,
    lifecycle_store: AgenticLifecycleStore,
    definitions: Mapping[str, WorkflowDefinition],
    agent_policies: Mapping[str, AgentPolicy],
    tool_policies: Mapping[str, ToolPolicy],
) -> AgenticDependencies:
    """Build the explicit composition record for the public API.

    Every argument is required. Omitting one is a construction error rather
    than a runtime surprise inside an operator call.

    Args:
        settings: Resolved Agentic settings.
        mandate: Validated signed firm mandate.
        registry: Validated role registry.
        workflow_store: Durable workflow store.
        memory_store: Governed memory and audit store.
        operations_store: Operations, incident, and replay store.
        lifecycle_store: Append-only artefact lifecycle ledger.
        definitions: Registered workflow definition per workflow name.
        agent_policies: Registered agent policy per role.
        tool_policies: Registered tool policy per tool name.

    Returns:
        The frozen dependency record.
    """
    logger.debug("Building the Agentic public-API dependency record")
    return AgenticDependencies(
        settings=settings,
        mandate=mandate,
        registry=registry,
        workflow_store=workflow_store,
        memory_store=memory_store,
        operations_store=operations_store,
        lifecycle_store=lifecycle_store,
        definitions=definitions,
        agent_policies=agent_policies,
        tool_policies=tool_policies,
    )
