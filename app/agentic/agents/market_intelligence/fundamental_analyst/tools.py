"""Governed point-in-time fundamental evidence bindings.

`FR-AGENTIC-025` requires licensed point-in-time filings, transcripts, macro,
and issuer evidence with publication and availability lineage. Research's
`FEAT-RES-13` owns that evidence and builds it from Data's `FEAT-DATA-16`
point-in-time documents; this module reads what Research returns, through the
governed authorization path, and computes nothing.

The port returns **projections**, not evidence objects.
`research.project_intelligence_evidence` already produces a detached bounded
mapping carrying no source payload and no action field, marked `advisory_only`.
That is exactly the shape untrusted evidence should reach an agent in, so the
port hands back projections and the coordinator reads them.

The canonical §4.9 dependency column lists the Research public contracts as a
local dependency of this module. Nothing here imports them. Building the
evidence requires a Data `ResearchSourceQuery` as well, so a concrete binding
would pull two receiver domains into an agent package; an approved composition
root binds the port to `research.assess_intelligence_applicability`,
`research.build_fundamental_source_evidence`, and
`research.project_intelligence_evidence` instead. The chain stays
Agentic → Research → Data, and a test asserts this package names neither
receiver.

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

# Registered tool identities this role may request. Every one is read-only.
APPLICABILITY_TOOL = "research.assess_intelligence_applicability"
FUNDAMENTAL_EVIDENCE_TOOL = "research.build_fundamental_source_evidence"

# Fundamental models Research recognizes. `issuer` requires an issuer to
# exist; `macro` does not. The distinction is the receiver's, not ours.
type FundamentalModel = str

# What each fundamental model requires coverage of by default. An issuer model
# needs an issuer document; a macro model needs a macro release. FX has no
# issuer, so the macro default is the ordinary path under an FX mandate.
DEFAULT_REQUIRED_KINDS: Mapping[str, tuple[str, ...]] = {
    "issuer": ("filing",),
    "macro": ("macro",),
}

# Fields a fundamental projection must carry for a pack to be built from it.
REQUIRED_PROJECTION_FIELDS: tuple[str, ...] = (
    "asset_scope",
    "canonical_hash",
    "coverage",
    "document_references",
)


@runtime_checkable
class FundamentalEvidencePort(Protocol):
    """Read-only access to Research point-in-time fundamental evidence."""

    def assess_applicability(
        self,
        asset_class: str,
        model: str,
    ) -> Mapping[str, str]:
        """Return whether one evidence model applies to an asset class.

        Args:
            asset_class: Normalized instrument asset class.
            model: Requested fundamental model.

        Returns:
            Bounded applicability status and reasons.
        """
        ...

    def get_fundamental_projection(
        self,
        instrument: str,
        asset_class: str,
        model: str,
        required_kinds: tuple[str, ...],
        decision_time: str,
    ) -> Mapping[str, str]:
        """Return the projected fundamental evidence for one instrument.

        `required_kinds` reaches Research's own coverage rule: it refuses
        `FUNDAMENTAL_COVERAGE_MISSING` when a declared kind has no eligible
        document. Declaring it is how a reading says what it needs rather than
        accepting whatever happens to exist.

        Args:
            instrument: Instrument under analysis.
            asset_class: Normalized instrument asset class.
            model: Requested fundamental model.
            required_kinds: Source kinds the reading requires coverage of.
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
        return f"the fundamental projection omits: {', '.join(missing)}"
    return None


def parse_coverage(projection: Mapping[str, str]) -> dict[str, int]:
    """Parse the receiver-reported coverage counts.

    Args:
        projection: Receiver-returned projection fields.

    Returns:
        Coverage kind to count; unreadable entries are omitted.
    """
    counts: dict[str, int] = {}
    for item in str(projection.get("coverage", "")).split(","):
        kind, _, count = item.partition("=")
        if kind.strip() and count.strip().isdigit():
            counts[kind.strip()] = int(count.strip())
    return counts


def verify_coverage(
    projection: Mapping[str, str],
    required_kinds: tuple[str, ...],
) -> str | None:
    """Report whether the projection covers every declared required kind.

    Research refuses on its own coverage rule, but the analyst verifies the
    answer rather than assuming the receiver applied the rule it was given: a
    projection that came back without a required kind is not evidence for the
    reading that was asked for.

    Args:
        projection: Receiver-returned projection fields.
        required_kinds: Source kinds the reading requires coverage of.

    Returns:
        The failing condition, or None when every required kind is covered.
    """
    if not required_kinds:
        return "a fundamental reading must declare the coverage it requires"
    coverage = parse_coverage(projection)
    missing = tuple(kind for kind in required_kinds if coverage.get(kind, 0) < 1)
    if missing:
        return (
            "the projection covers no "
            f"{', '.join(missing)} evidence, which this reading requires"
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
    """Authorize and perform one governed intelligence-evidence call.

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


class _FundamentalEvidencePort:
    """Binds the owner-public Research fundamental evidence surface.

    Constructed only by an approved composition root. Every call is a
    read-only lookup; no evidence is authored and no source is fetched here.
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
        """Return whether one evidence model applies to an asset class.

        Args:
            asset_class: Normalized instrument asset class.
            model: Requested fundamental model.

        Returns:
            Bounded applicability status and reasons, unaltered.
        """
        return self._evidence.assess_applicability(asset_class, model)  # type: ignore[attr-defined,no-any-return]

    def get_fundamental_projection(
        self,
        instrument: str,
        asset_class: str,
        model: str,
        required_kinds: tuple[str, ...],
        decision_time: str,
    ) -> Mapping[str, str]:
        """Return the projected fundamental evidence for one instrument.

        Args:
            instrument: Instrument under analysis.
            asset_class: Normalized instrument asset class.
            model: Requested fundamental model.
            required_kinds: Source kinds the reading requires coverage of.
            decision_time: Point in time the evidence must be available by.

        Returns:
            Bounded detached projection, unaltered.
        """
        return self._evidence.get_fundamental_projection(  # type: ignore[attr-defined,no-any-return]
            instrument,
            asset_class,
            model,
            required_kinds,
            decision_time,
        )


def build_fundamental_evidence_port(evidence: object) -> FundamentalEvidencePort:
    """Build the port bound to owner-public Research intelligence evidence.

    Args:
        evidence: Owner-public Research intelligence facade.

    Returns:
        A port satisfying `FundamentalEvidencePort`.
    """
    logger.debug("Building the fundamental-analyst evidence port")
    return _FundamentalEvidencePort(evidence)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered read-only tool names.
    """
    return (APPLICABILITY_TOOL, FUNDAMENTAL_EVIDENCE_TOOL)
