"""Governed evaluation-evidence bindings for the Evaluation Manager.

`FR-AGENTIC-049` requires versioned sets and calibrated graders. Whether a set
exists at a version, and whether its grader is calibrated, are facts the
owner-public evaluation evidence holds — not facts a model may assert. Both are
read through the governed authorization path.

This module authors no evaluation set, runs no grader, and computes no score.
It fetches references and outcomes, and the coordinator reads them.

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

# Registered tool identities this role may request.
EVALUATION_SET_TOOL = "evaluation.list_versioned_sets"
GRADER_CALIBRATION_TOOL = "evaluation.get_grader_calibrations"
GATE_OUTCOME_TOOL = "evaluation.get_gate_outcomes"
BASELINE_TOOL = "evaluation.get_baseline_comparison"

# Fields a baseline comparison must carry for acceptance to be computable.
REQUIRED_COMPARISON_FIELDS: tuple[str, ...] = (
    "baseline_score",
    "candidate_score",
    "cost_delta",
    "metric",
    "uncertainty_halfwidth",
)


@runtime_checkable
class EvaluationEvidencePort(Protocol):
    """Read-only access to owner-public evaluation evidence."""

    def list_versioned_sets(self, role_id: str) -> Mapping[str, str]:
        """Return the versioned evaluation set reference per kind.

        Args:
            role_id: Role under evaluation.

        Returns:
            Set kind to versioned set reference.
        """
        ...

    def get_grader_calibrations(self, role_id: str) -> Mapping[str, str]:
        """Return the grader and calibration references per kind.

        Args:
            role_id: Role under evaluation.

        Returns:
            Prefixed grader and calibration references.
        """
        ...

    def get_gate_outcomes(self, role_id: str) -> Mapping[str, str]:
        """Return the recorded safety and reliability gate outcomes.

        Args:
            role_id: Role under evaluation.

        Returns:
            Gate kind to enumerated outcome.
        """
        ...

    def get_baseline_comparison(self, role_id: str) -> Mapping[str, str]:
        """Return the measured comparison against the simpler baseline.

        Args:
            role_id: Role under evaluation.

        Returns:
            Comparison fields as exact decimal strings.
        """
        ...


def verify_comparison(comparison: Mapping[str, str]) -> str | None:
    """Report whether a baseline comparison can be read at all.

    Args:
        comparison: Receiver-returned comparison fields.

    Returns:
        The failing condition, or None when the comparison is complete.
    """
    missing = tuple(
        field for field in REQUIRED_COMPARISON_FIELDS if not comparison.get(field)
    )
    if missing:
        return f"the baseline comparison omits: {', '.join(missing)}"
    return None


def call_evaluation_tool(
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
    """Authorize and perform one governed evaluation-evidence call.

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


class _EvaluationEvidencePort:
    """Binds the owner-public evaluation evidence surface.

    Constructed only by an approved composition root. Every call is a read-only
    lookup; no evaluation set is authored and no grader is run here.
    """

    def __init__(self, evidence: object) -> None:
        """Store the injected evaluation-evidence facade.

        Args:
            evidence: Owner-public evaluation evidence facade.
        """
        self._evidence = evidence

    def list_versioned_sets(self, role_id: str) -> Mapping[str, str]:
        """Return the versioned evaluation set reference per kind.

        Args:
            role_id: Role under evaluation.

        Returns:
            Set kind to versioned set reference, unaltered.
        """
        return self._evidence.list_versioned_sets(role_id)  # type: ignore[attr-defined,no-any-return]

    def get_grader_calibrations(self, role_id: str) -> Mapping[str, str]:
        """Return the grader and calibration references per kind.

        Args:
            role_id: Role under evaluation.

        Returns:
            Prefixed grader and calibration references, unaltered.
        """
        return self._evidence.get_grader_calibrations(role_id)  # type: ignore[attr-defined,no-any-return]

    def get_gate_outcomes(self, role_id: str) -> Mapping[str, str]:
        """Return the recorded safety and reliability gate outcomes.

        Args:
            role_id: Role under evaluation.

        Returns:
            Gate kind to enumerated outcome, unaltered.
        """
        return self._evidence.get_gate_outcomes(role_id)  # type: ignore[attr-defined,no-any-return]

    def get_baseline_comparison(self, role_id: str) -> Mapping[str, str]:
        """Return the measured comparison against the simpler baseline.

        Args:
            role_id: Role under evaluation.

        Returns:
            Comparison fields, unaltered.
        """
        return self._evidence.get_baseline_comparison(role_id)  # type: ignore[attr-defined,no-any-return]


def build_evaluation_evidence_port(evidence: object) -> EvaluationEvidencePort:
    """Build the port bound to owner-public evaluation evidence.

    Args:
        evidence: Owner-public evaluation evidence facade.

    Returns:
        A port satisfying `EvaluationEvidencePort`.
    """
    logger.debug("Building the evaluation-manager evidence port")
    return _EvaluationEvidencePort(evidence)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (
        BASELINE_TOOL,
        EVALUATION_SET_TOOL,
        GATE_OUTCOME_TOOL,
        GRADER_CALIBRATION_TOOL,
    )
