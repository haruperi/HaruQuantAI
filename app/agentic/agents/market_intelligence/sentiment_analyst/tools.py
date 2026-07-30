"""Governed, injection-filtered text-evidence bindings.

`FR-AGENTIC-028` requires governed news and social sources carrying source
trust, deduplication, revision, manipulation, and availability metadata.
Research's `FEAT-RES-13` already produces exactly that: `SentimentSourceEvidence`
carries `trust_evidence`, `manipulation_evidence`, `injection_evidence`,
`revisions`, `source_coverage`, and `available_by`. This module reads what
Research projected and measures nothing.

The port returns **projections**. `research.project_intelligence_evidence`
produces a detached bounded mapping with no source payload and no action
field, marked `advisory_only`, which is the shape untrusted text should reach
an agent in.

The canonical §4.10 dependency column lists the Research public contracts as a
local dependency. Nothing here imports them: building the evidence also needs a
Data `ResearchSourceQuery`, so a concrete binding would pull two receiver
domains into an agent package. An approved composition root binds the port to
`research.assess_intelligence_applicability` and
`research.build_sentiment_source_evidence` instead, and a test asserts this
package names neither receiver.

Authorization runs before invocation through the shared `call_governed_tool`
wrapper owned by `FEAT-AGT-05`; this module supplies only the audit sink.
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

# Registered tool identities this role may request. Every one is read-only.
APPLICABILITY_TOOL = "research.assess_intelligence_applicability"
SENTIMENT_EVIDENCE_TOOL = "research.build_sentiment_source_evidence"

# The one deterministic measurement version Research recognizes. Declaring it
# here means a caller asking for an unknown version is refused before the
# receiver is reached rather than after.
SUPPORTED_MEASUREMENT_VERSION = "lexicon-v1"

# `FR-AGENTIC-028`'s metadata list. A projection missing any of it is not
# governed source evidence, whatever else it carries.
REQUIRED_PROJECTION_FIELDS: tuple[str, ...] = (
    "asset_scope",
    "canonical_hash",
    "document_references",
    "polarity",
)


@runtime_checkable
class SentimentEvidencePort(Protocol):
    """Read-only access to Research point-in-time sentiment evidence."""

    def assess_applicability(
        self,
        asset_class: str,
        model: str,
    ) -> Mapping[str, str]:
        """Return whether the sentiment model applies to an asset class.

        Args:
            asset_class: Normalized instrument asset class.
            model: Requested evidence model.

        Returns:
            Bounded applicability status and reasons.
        """
        ...

    def get_sentiment_projection(
        self,
        instrument: str,
        asset_class: str,
        measurement_version: str,
        decision_time: str,
    ) -> Mapping[str, str]:
        """Return the projected sentiment evidence for one instrument.

        Args:
            instrument: Instrument under analysis.
            asset_class: Normalized instrument asset class.
            measurement_version: Deterministic measurement version.
            decision_time: Point in time the evidence must be available by.

        Returns:
            Bounded detached projection carrying no source payload.
        """
        ...


def verify_projection(projection: Mapping[str, str]) -> str | None:
    """Report whether a projection can support a pack at all.

    Args:
        projection: Receiver-returned projection fields.

    Returns:
        The failing condition, or None when the projection is complete.
    """
    missing = tuple(
        field for field in REQUIRED_PROJECTION_FIELDS if not projection.get(field)
    )
    if missing:
        return f"the sentiment projection omits: {', '.join(missing)}"
    return None


def verify_measurement_version(version: str) -> str | None:
    """Report whether a measurement version is one Research recognizes.

    Args:
        version: Requested deterministic measurement version.

    Returns:
        The failing condition, or None when the version is supported.
    """
    if version != SUPPORTED_MEASUREMENT_VERSION:
        return (
            f"{version!r} is not a recognized measurement version; Research "
            f"recognizes {SUPPORTED_MEASUREMENT_VERSION!r}"
        )
    return None


def call_intelligence_tool(
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
    """Authorize and perform one governed text-evidence call.

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
        store_memory(
            audit_store,
            "audit",
            task_id,
            policy.role_id,
            {
                "tool": tool_name,
                "outcome": outcome,
                "call": str(calls_used + 1),
                "span": "tool",
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


class _SentimentEvidencePort:
    """Binds the owner-public Research sentiment evidence surface.

    Constructed only by an approved composition root. Every call is a
    read-only lookup; no polarity is measured and no source is fetched here.
    """

    def __init__(self, evidence: object) -> None:
        """Store the injected intelligence-evidence facade.

        Args:
            evidence: Owner-public Research intelligence facade.
        """
        self._evidence = evidence

    def assess_applicability(
        self,
        asset_class: str,
        model: str,
    ) -> Mapping[str, str]:
        """Return whether the sentiment model applies to an asset class.

        Args:
            asset_class: Normalized instrument asset class.
            model: Requested evidence model.

        Returns:
            Bounded applicability status and reasons, unaltered.
        """
        return self._evidence.assess_applicability(asset_class, model)  # type: ignore[attr-defined,no-any-return]

    def get_sentiment_projection(
        self,
        instrument: str,
        asset_class: str,
        measurement_version: str,
        decision_time: str,
    ) -> Mapping[str, str]:
        """Return the projected sentiment evidence for one instrument.

        Args:
            instrument: Instrument under analysis.
            asset_class: Normalized instrument asset class.
            measurement_version: Deterministic measurement version.
            decision_time: Point in time the evidence must be available by.

        Returns:
            Bounded detached projection, unaltered.
        """
        return self._evidence.get_sentiment_projection(  # type: ignore[attr-defined,no-any-return]
            instrument,
            asset_class,
            measurement_version,
            decision_time,
        )


def build_sentiment_evidence_port(evidence: object) -> SentimentEvidencePort:
    """Build the port bound to owner-public Research intelligence evidence.

    Args:
        evidence: Owner-public Research intelligence facade.

    Returns:
        A port satisfying `SentimentEvidencePort`.
    """
    logger.debug("Building the sentiment-analyst evidence port")
    return _SentimentEvidencePort(evidence)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered read-only tool names.
    """
    return (APPLICABILITY_TOOL, SENTIMENT_EVIDENCE_TOOL)
