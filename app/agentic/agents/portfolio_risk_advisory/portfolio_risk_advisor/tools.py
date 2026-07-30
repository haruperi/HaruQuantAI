"""Governed portfolio, risk, and account evidence bindings for the advisor.

`FR-AGENTIC-055` requires current Analytics, Portfolio, Risk, and account-scope
evidence. Every one of those is a fact an owning domain holds — not a fact a
model may assert — so all five reads traverse the governed authorization path.

The receiver signatures this port stands in front of are deliberately not
reproduced here. `assess_common_mode_exposure` wants `Decimal` maps of
loss-at-stop by account, `get_account_state_snapshot` wants a connected broker
adapter, and `build_portfolio_allocation_evidence` wants an analytics run
config and simulation results. Agentic constructing any of those would be
Agentic authoring receiver inputs, so the port returns bounded string mappings
and an approved composition root binds it to the real operations.

This module computes no exposure, no correlation, and no risk number. It reads
what the receivers returned, and the coordinator reads it.

Authorization runs before invocation through the shared `call_governed_tool`
wrapper owned by `FEAT-AGT-05`; this module supplies only the audit sink, so
`permissions/` stays free of a `context_memory/` dependency.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.context_memory.repository import store_memory
from app.agentic.permissions.authorization import ToolCallOutcome, call_governed_tool
from app.utils import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)

# Registered tool identities this role may request. Every one is read-only;
# there is no registrable operation here that mutates a portfolio or a limit.
ALLOCATION_EVIDENCE_TOOL = "analytics.build_portfolio_allocation_evidence"
COMMON_MODE_TOOL = "portfolio.assess_common_mode_exposure"
CORRELATION_TOOL = "portfolio.measure_cross_account_correlation"
ACCOUNT_STATE_TOOL = "data.get_account_state_snapshot"
FIRM_MANDATE_TOOL = "risk.load_firm_mandate"

# The key every evidence read carries so freshness can be established without
# trusting the model's account of how old the evidence was.
OBSERVED_AT_KEY = "observed_at"

# Fields the mandate evidence must carry for scope to be checkable.
REQUIRED_MANDATE_FIELDS: tuple[str, ...] = (
    "asset_class",
    "base_currency",
    "mandate_id",
    "mandate_version",
)


@runtime_checkable
class PortfolioRiskEvidencePort(Protocol):
    """Read-only access to owner-public portfolio, risk, and account evidence."""

    def get_allocation_evidence(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Analytics non-binding allocation evidence.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded allocation evidence references and observations.
        """
        ...

    def get_common_mode_exposure(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Portfolio common-mode exposure assessment.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded shared-scenario and dependency observations.
        """
        ...

    def get_cross_account_correlation(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Portfolio cross-account correlation measurement.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded correlation observations.
        """
        ...

    def get_account_state(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Data account-state snapshot.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded account-scope observations.
        """
        ...

    def get_firm_mandate(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Risk-owned firm mandate scope.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded mandate identity and scope.
        """
        ...


def verify_mandate(mandate_evidence: Mapping[str, str]) -> str | None:
    """Report whether the mandate evidence can bound a proposal at all.

    Args:
        mandate_evidence: Receiver-returned mandate fields.

    Returns:
        The failing condition, or None when the mandate is complete.
    """
    missing = tuple(
        field for field in REQUIRED_MANDATE_FIELDS if not mandate_evidence.get(field)
    )
    if missing:
        return f"the firm mandate omits: {', '.join(missing)}"
    return None


def call_advisory_tool(
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
    """Authorize and perform one governed advisory-evidence call.

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


class _PortfolioRiskEvidencePort:
    """Binds the owner-public portfolio, risk, and account evidence surface.

    Constructed only by an approved composition root. Every call is a read-only
    lookup; no allocation is constructed and no risk number is computed here.
    """

    def __init__(self, evidence: object) -> None:
        """Store the injected advisory-evidence facade.

        Args:
            evidence: Owner-public advisory evidence facade.
        """
        self._evidence = evidence

    def get_allocation_evidence(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Analytics non-binding allocation evidence.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded allocation evidence, unaltered.
        """
        return self._evidence.get_allocation_evidence(portfolio_id)  # type: ignore[attr-defined,no-any-return]

    def get_common_mode_exposure(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Portfolio common-mode exposure assessment.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded exposure observations, unaltered.
        """
        return self._evidence.get_common_mode_exposure(portfolio_id)  # type: ignore[attr-defined,no-any-return]

    def get_cross_account_correlation(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Portfolio cross-account correlation measurement.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded correlation observations, unaltered.
        """
        return self._evidence.get_cross_account_correlation(portfolio_id)  # type: ignore[attr-defined,no-any-return]

    def get_account_state(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Data account-state snapshot.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded account observations, unaltered.
        """
        return self._evidence.get_account_state(portfolio_id)  # type: ignore[attr-defined,no-any-return]

    def get_firm_mandate(self, portfolio_id: str) -> Mapping[str, str]:
        """Return the Risk-owned firm mandate scope.

        Args:
            portfolio_id: Portfolio under advisement.

        Returns:
            Bounded mandate identity and scope, unaltered.
        """
        return self._evidence.get_firm_mandate(portfolio_id)  # type: ignore[attr-defined,no-any-return]


def build_portfolio_risk_evidence_port(evidence: object) -> PortfolioRiskEvidencePort:
    """Build the port bound to owner-public portfolio and risk evidence.

    Args:
        evidence: Owner-public advisory evidence facade.

    Returns:
        A port satisfying `PortfolioRiskEvidencePort`.
    """
    logger.debug("Building the portfolio-risk-advisor evidence port")
    return _PortfolioRiskEvidencePort(evidence)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered read-only tool names.
    """
    return (
        ACCOUNT_STATE_TOOL,
        ALLOCATION_EVIDENCE_TOOL,
        COMMON_MODE_TOOL,
        CORRELATION_TOOL,
        FIRM_MANDATE_TOOL,
    )


__all__: tuple[str, ...] = (
    "ACCOUNT_STATE_TOOL",
    "ALLOCATION_EVIDENCE_TOOL",
    "COMMON_MODE_TOOL",
    "CORRELATION_TOOL",
    "FIRM_MANDATE_TOOL",
    "OBSERVED_AT_KEY",
    "REQUIRED_MANDATE_FIELDS",
    "PortfolioRiskEvidencePort",
    "ToolCallOutcome",
    "build_portfolio_risk_evidence_port",
    "call_advisory_tool",
    "get_registered_tool_names",
    "verify_mandate",
)
