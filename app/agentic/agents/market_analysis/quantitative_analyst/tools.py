"""Governed calculation and evidence tools for the Quantitative Analyst.

The deterministic grounding for `FR-AGENTIC-034` lives in Analytics: its metric
catalog carries each estimator's formula, unit, sample convention, and minimum
sample. The analyst names a metric; the catalog supplies its definition. No
estimator is ever authored by a model.

Authorization runs before invocation through the shared `call_governed_tool`
wrapper owned by `FEAT-AGT-05`; this module supplies only the audit sink, so
`permissions/` stays free of a `context_memory/` dependency.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.context_memory.repository import store_memory
from app.agentic.permissions.authorization import ToolCallOutcome, call_governed_tool
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)

# Registered tool identities this role may request. Each maps to exactly one
# public receiver operation.
METRIC_CATALOG_TOOL = "analytics.get_metric_definition"
SAMPLE_FLOOR_TOOL = "analytics.get_minimum_sample"
CONTRACT_VERSION_TOOL = "analytics.validate_contract_version"


@runtime_checkable
class QuantitativeEvidencePort(Protocol):
    """Read-only access to the deterministic grounding this role relies on."""

    def fetch_metric_definition(self, metric: str) -> Mapping[str, str]:
        """Return one registered metric definition.

        Args:
            metric: Catalogued metric name.

        Returns:
            The metric's registered definition, empty when uncatalogued.
        """
        ...

    def fetch_minimum_samples(self) -> Mapping[str, str]:
        """Return the registered minimum-sample thresholds by evidence class.

        Returns:
            Evidence class to minimum observation count.
        """
        ...

    def validate_evidence_contract(
        self,
        contract: str,
        version: str,
    ) -> Mapping[str, str]:
        """Validate one evidence contract version with its owning domain.

        Args:
            contract: Namespaced contract identity.
            version: Producer compatibility version.

        Returns:
            The owning domain's classification.
        """
        ...


def call_calculation_tool(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool: ToolPolicy,
    principal_id: str,
    task_id: str,
    request_scope: Mapping[str, str],
    receiver_call: Callable[[], Mapping[str, object]],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    calls_used: int = 0,
) -> ToolCallOutcome:
    """Authorize and perform one governed calculation-grounding call.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool: Registered tool policy.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        request_scope: Scope declared for this call.
        receiver_call: Zero-argument callable invoking the receiver operation.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        calls_used: Tool invocations already consumed by this task.

    Returns:
        The bounded outcome, denied or completed.
    """

    def audit_hook(tool_name: str, outcome: str) -> None:
        """Record one redacted tool-call audit entry.

        Args:
            tool_name: Tool identity invoked.
            outcome: Enumerated call outcome.
        """
        if audit_store is None:
            return
        # The ordinal keeps two calls to the same tool in the same instant
        # distinguishable; without it they would share a content identity.
        store_memory(
            audit_store,
            "audit",
            task_id,
            policy.role_id,
            {
                "tool": tool_name,
                "outcome": outcome,
                "call": str(calls_used + 1),
            },
            {"environment": "sandbox"},
            "audit-730d",
            at_time=at_time,
        )

    return call_governed_tool(
        mandate,
        policy,
        tool,
        principal_id,
        task_id,
        request_scope,
        receiver_call,
        at_time,
        nonce_store=nonce_store,
        audit_hook=audit_hook,
        calls_used=calls_used,
    )


class _AnalyticsCatalogPort:
    """Binds the real Analytics metric catalog and version validator.

    Constructed only by an approved composition root. Every call is a
    read-only lookup through a documented public API; no provider SDK,
    credential, or broker is involved.
    """

    def __init__(self, catalog_reader: object) -> None:
        """Store the injected Analytics facade.

        Args:
            catalog_reader: Analytics package-root facade.
        """
        self._reader = catalog_reader

    def fetch_metric_definition(self, metric: str) -> Mapping[str, str]:
        """Return one registered metric definition.

        Args:
            metric: Catalogued metric name.

        Returns:
            The metric's registered definition, empty when uncatalogued.
        """
        return self._reader.fetch_metric_definition(metric)  # type: ignore[attr-defined,no-any-return]

    def fetch_minimum_samples(self) -> Mapping[str, str]:
        """Return the registered minimum-sample thresholds.

        Returns:
            Evidence class to minimum observation count.
        """
        return self._reader.fetch_minimum_samples()  # type: ignore[attr-defined,no-any-return]

    def validate_evidence_contract(
        self,
        contract: str,
        version: str,
    ) -> Mapping[str, str]:
        """Validate one evidence contract version.

        Args:
            contract: Namespaced contract identity.
            version: Producer compatibility version.

        Returns:
            The owning domain's classification.
        """
        return self._reader.validate_evidence_contract(contract, version)  # type: ignore[attr-defined,no-any-return]


def build_analytics_catalog_port(catalog_reader: object) -> QuantitativeEvidencePort:
    """Build the evidence port bound to Analytics public operations.

    Args:
        catalog_reader: Analytics package-root facade.

    Returns:
        A port satisfying `QuantitativeEvidencePort`.
    """
    logger.debug("Building the quantitative-analyst evidence port")
    return _AnalyticsCatalogPort(catalog_reader)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (CONTRACT_VERSION_TOOL, METRIC_CATALOG_TOOL, SAMPLE_FLOOR_TOOL)
