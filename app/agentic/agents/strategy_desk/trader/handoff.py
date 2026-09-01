"""Mapping and submission of an untrusted proposal to receiver-owned intake.

`WF-AGT-008` step 2 names `strategy.validate_strategy_ref()` and
`strategy.build_trade_intent()`. Neither can take an Agentic proposal:
`build_trade_intent` requires a `StrategyDecision` and a
`StrategyExecutionContext`, which are deterministic evaluation state this
domain does not have and must not fabricate. Strategy's `FEAT-STR-11` shipped
the intake this handoff was meant for, and that is what is used here.

Two properties make `FR-AGENTIC-059`'s "no privileged route" structural rather
than promised. The receiver's own factory builds the request, so Agentic cannot
get its shape wrong or omit a field the receiver checks. And the request's
identity and idempotency key are **derived by the receiver** from a content
digest — `create_strategy_proposal_evaluation_request` refuses a caller that
supplies either — so a proposal cannot arrive pre-stamped with an identity that
might collide with, or impersonate, another.

The evaluation itself stays behind an injected port. `evaluate_strategy_proposal`
needs a hash-bound `SignalEvaluator`, a strategy config, point-in-time
indicators, and an execution context: a full Strategy composition that belongs
to a composition root, not to an agent package.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.agents.strategy_desk.trader.schemas import (
    TradeProposalReceipt,
    build_trade_proposal_receipt,
)
from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.kernel.time import utc_now
from app.services.strategy import create_strategy_proposal_evaluation_request

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.agentic.agents.strategy_desk.trader.schemas import TradeProposal

logger = get_logger(__name__)

# Fields the receiver derives for itself. Supplying either is refused by
# `create_strategy_proposal_evaluation_request`, and naming them here states
# why this module never sets them.
RECEIVER_DERIVED_FIELDS: tuple[str, ...] = (
    "evaluation_request_id",
    "idempotency_key",
)

# What a receiver result must carry for a receipt to be built from it.
REQUIRED_RESULT_FIELDS: tuple[str, ...] = (
    "evaluation_request_id",
    "source_content_hash",
    "source_proposal_id",
    "status",
)


@runtime_checkable
class ProposalIntakePort(Protocol):
    """Receiver-owned intake for one untrusted external proposal."""

    def submit(self, request: object) -> Mapping[str, object]:
        """Submit one proposal-evaluation request and return what came back.

        Args:
            request: Receiver-owned `StrategyProposalEvaluationRequest`.

        Returns:
            The receiver's own result fields, unaltered.
        """
        ...


def build_evaluation_request(
    proposal: TradeProposal,
    principal_id: str,
    request_id: str,
    workflow_id: str,
    correlation_id: str,
) -> object:
    """Map one trade proposal onto the receiver's own request contract.

    Nothing is invented. Every field comes from the proposal or from the task
    lineage, and the two derived identities are left to the receiver.

    Args:
        proposal: Non-executable proposal to submit.
        principal_id: Authenticated requesting principal.
        request_id: Trace identifier of the outer request.
        workflow_id: Trace identifier of the orchestrating workflow.
        correlation_id: Trace identifier of the whole flow.

    Returns:
        A validated receiver-owned proposal-evaluation request.

    Raises:
        ValueError: If the receiver rejects the mapped request.
    """
    logger.info(
        "Mapping trade proposal %s onto the Strategy proposal intake",
        proposal.proposal_id,
    )
    return create_strategy_proposal_evaluation_request(
        principal_id=principal_id,
        source_proposal_id=proposal.proposal_id,
        source_task_id=proposal.task_id,
        source_content_hash=proposal.content_hash,
        strategy_id=proposal.strategy_id,
        strategy_version=proposal.strategy_version,
        instrument=proposal.instrument,
        requested_direction=proposal.direction,
        horizon_seconds=proposal.horizon_seconds,
        thesis_evidence_refs=proposal.evidence_refs,
        invalidation_evidence_refs=proposal.invalidation,
        evaluation_scope=proposal.evaluation_scope,
        requested_at=_instant(proposal.issued_at),
        expires_at=_instant(proposal.expires_at),
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )


def verify_result(result: Mapping[str, object]) -> str | None:
    """Report whether a receiver result can be read as a receipt at all.

    Args:
        result: Receiver-returned result fields.

    Returns:
        The failing condition, or None when the result is complete.
    """
    missing = tuple(field for field in REQUIRED_RESULT_FIELDS if not result.get(field))
    if missing:
        return f"the receiver result omits: {', '.join(missing)}"
    return None


def verify_binding(
    proposal: TradeProposal,
    result: Mapping[str, object],
) -> str | None:
    """Report whether a receiver result actually answers this proposal.

    A result is bound to the proposal it evaluated by identity and content
    digest. Accepting one that names a different proposal, or the same
    proposal at different content, would let a receipt describe something
    other than what was submitted.

    Args:
        proposal: Proposal that was submitted.
        result: Receiver-returned result fields.

    Returns:
        The failing condition, or None when the result is bound.
    """
    if str(result["source_proposal_id"]) != proposal.proposal_id:
        return (
            f"the result answers proposal {result['source_proposal_id']}, "
            f"not {proposal.proposal_id}"
        )
    if str(result["source_content_hash"]) != proposal.content_hash:
        return "the result was produced for different proposal content"
    return None


def submit_trade_proposal(
    proposal: TradeProposal,
    port: ProposalIntakePort,
    principal_id: str,
    request_id: str,
    workflow_id: str,
    correlation_id: str,
    at_time: datetime | None = None,
) -> TradeProposalReceipt:
    """Submit one proposal to the receiver and record what it said.

    The receipt carries the receiver's own status and reason codes verbatim.
    When the receiver produced a canonical intent, only its identity is
    recorded; the intent is Strategy's object and its contents are not copied.

    Args:
        proposal: Non-executable proposal to submit.
        port: Injected receiver-owned intake.
        principal_id: Authenticated requesting principal.
        request_id: Trace identifier of the outer request.
        workflow_id: Trace identifier of the orchestrating workflow.
        correlation_id: Trace identifier of the whole flow.
        at_time: Optional receipt time; current UTC when omitted.

    Returns:
        A validated immutable receipt.

    Raises:
        ValueError: If the receiver rejects the mapped request, or returns a
            result that is incomplete or not bound to this proposal.
    """
    now = at_time if at_time is not None else utc_now()
    if proposal.is_expired(now):
        message = (
            f"the proposal expired at {proposal.expires_at} and is not submittable"
        )
        raise ValueError(message)

    request = build_evaluation_request(
        proposal,
        principal_id,
        request_id,
        workflow_id,
        correlation_id,
    )
    result = port.submit(request)

    failure = verify_result(result) or verify_binding(proposal, result)
    if failure is not None:
        raise ValueError(failure)

    intent_ref = result.get("trade_intent_ref")
    receipt = build_trade_proposal_receipt(
        {
            "receipt_id": derive_stable_id(
                "id",
                f"receipt:{proposal.proposal_id}",
            ),
            "task_id": proposal.task_id,
            "proposal_id": proposal.proposal_id,
            "proposal_content_hash": proposal.content_hash,
            "evaluation_request_id": str(result["evaluation_request_id"]),
            # The receiver's own words. Agentic does not reinterpret an
            # outcome, and there is no status here that means "filled".
            "status": str(result["status"]),
            "reason_codes": _codes(result.get("reason_codes")),
            "intent_produced": intent_ref is not None,
            "intent_ref": None if intent_ref is None else str(intent_ref),
            "signals_evaluated": _count(result.get("signals_evaluated")),
            "audit_event_ref": _optional(result.get("audit_event_ref")),
            "received_at": now.isoformat(),
        },
    )
    logger.info(
        "Trade proposal %s received status %s from the receiver",
        proposal.proposal_id,
        receipt.status,
    )
    return receipt


def _codes(value: object) -> tuple[str, ...]:
    """Return the receiver's reason codes as bounded text.

    Args:
        value: Candidate codes.

    Returns:
        Ordered codes, empty when the receiver returned none.
    """
    if not isinstance(value, tuple | list):
        return ()
    return tuple(str(code) for code in value)


def _count(value: object) -> int:
    """Return the receiver's evaluated-signal count.

    Args:
        value: Candidate count.

    Returns:
        The count, zero when absent or unreadable.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _optional(value: object) -> str | None:
    """Return one optional receiver reference as text.

    Args:
        value: Candidate value.

    Returns:
        The value as text, or None when absent.
    """
    return None if value is None else str(value)


def _instant(value: str) -> datetime:
    """Parse one aware UTC instant the receiver requires as a datetime.

    Args:
        value: ISO-8601 instant carried by the proposal.

    Returns:
        The parsed aware instant.
    """
    return datetime.fromisoformat(value)
