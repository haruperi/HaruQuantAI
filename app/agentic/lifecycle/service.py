"""Deterministic promotion assessment and governed artefact transitions.

Two operations, and neither invokes a model. Promotion is a decision procedure
over evidence other features produced; there is nothing here for a model to
judge, and adding one would create a place where a model could argue its way
past a gate.

`assess_promotion` runs the five `FR-AGENTIC-053` gates in the order the
requirement states them and returns what they concluded. A failed gate is a
result, not an exception: the assessment records every failure and names the
first as the termination reason, so the caller sees the whole picture rather
than only the gate that happened to run first.

`transition_artifact` writes one append-only record through the injected
ledger. It records that an artefact reached a state; it does not cause the
state. In particular `registered` is the receiver's fact — Strategy alone
registers a strategy version — and this module never calls a receiver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.agentic.lifecycle.models import (
    approval_refusal,
    build_lifecycle_record,
    build_promotion_assessment,
    is_terminal_state,
    missing_provenance,
    validate_transition,
)
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.agents.engineering.coder.schemas import CodeArtifact
    from app.agentic.agents.experimentation.experiment_designer.schemas import (
        ExperimentVerdict,
    )
    from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
        SweepVerdict,
    )
    from app.agentic.agents.operations.evaluation_manager.schemas import CritiqueMemo
    from app.agentic.lifecycle.models import (
        ApprovingPrincipal,
        ArtifactState,
        LifecycleRecord,
        PromotionAssessment,
        PromotionEvidencePacket,
        TerminationReason,
    )
    from app.agentic.lifecycle.repository import AgenticLifecycleStore

logger = get_logger(__name__)

# Evidence measured outside the data that selected the artefact. A promotion
# resting on neither is resting on its own selection.
_OUT_OF_SAMPLE_CLASSES: frozenset[str] = frozenset({"holdout", "validation"})

# Gate order follows `FR-AGENTIC-053`'s own wording, so the first failure this
# reports is the first the requirement names.
_GATE_ORDER: tuple[tuple[str, TerminationReason], ...] = (
    ("leakage", "leakage_detected"),
    ("holdout", "holdout_reused"),
    ("search_budget", "search_budget_exhausted"),
    ("provenance", "provenance_incomplete"),
    ("approval", "approval_absent"),
)


def _leakage_failure(experiment_verdict: ExperimentVerdict) -> str | None:
    """Report whether the experiment evidence is selection-contaminated.

    An experiment whose runs are all `discovery` or `null_data` measured the
    artefact on the data that chose it. That is the form of leakage a packet
    can establish from evidence it holds; lookahead inside generated code is
    the simulator's and `FEAT-AGT-16`'s problem, not detectable here.

    Args:
        experiment_verdict: Pre-registered experiment outcome.

    Returns:
        A failure message, or None when out-of-sample evidence exists.
    """
    classes = set(experiment_verdict.evidence_classes.values())
    if classes & _OUT_OF_SAMPLE_CLASSES:
        return None
    observed = ", ".join(sorted(classes)) or "nothing"
    return (
        "the experiment carries no validation or holdout evidence, so the "
        f"result was measured on the data that selected it; observed: {observed}"
    )


def _holdout_failure(
    experiment_verdict: ExperimentVerdict,
    sweep_verdict: SweepVerdict,
) -> str | None:
    """Report whether a thesis's single holdout look was spent twice.

    Args:
        experiment_verdict: Pre-registered experiment outcome.
        sweep_verdict: Bounded search outcome.

    Returns:
        A failure message, or None when holdout was spent at most once.
    """
    if experiment_verdict.holdout_consumed and sweep_verdict.holdout_consumed:
        return (
            "holdout was consumed by both the experiment and the sweep; a "
            "thesis has one look and this packet reports two"
        )
    return None


def _search_budget_failure(sweep_verdict: SweepVerdict, ceiling: int) -> str | None:
    """Report whether cumulative search exceeded its declared ceiling.

    Args:
        sweep_verdict: Bounded search outcome.
        ceiling: Declared cumulative search budget for the thesis.

    Returns:
        A failure message, or None when the budget holds.
    """
    if sweep_verdict.lifetime_trials > ceiling:
        return (
            f"cumulative search reached {sweep_verdict.lifetime_trials} trials "
            f"against a declared ceiling of {ceiling}"
        )
    return None


def _provenance_failure(artifact: CodeArtifact) -> str | None:
    """Report whether the artefact's authorship record is incomplete.

    Args:
        artifact: Staged artefact under assessment.

    Returns:
        A failure message, or None when provenance is complete.
    """
    missing = missing_provenance(artifact)
    if missing:
        return f"the artefact is missing provenance: {', '.join(missing)}"
    if artifact.promotion_status != "ready":
        return f"the artefact is not promotable as staged: {artifact.promotion_status}"
    return None


def assess_promotion(
    artifact: CodeArtifact,
    experiment_verdict: ExperimentVerdict,
    sweep_verdict: SweepVerdict,
    critique: CritiqueMemo,
    task_id: str,
    lifetime_trial_ceiling: int,
    environment: str,
    approver: ApprovingPrincipal | None = None,
    packet_hash: str | None = None,
    at_time: datetime | None = None,
) -> PromotionAssessment:
    """Run the deterministic promotion gates over assembled evidence.

    Every gate reads evidence the packet already carries. Nothing here asks a
    model, and nothing here consults a receiver.

    Args:
        artifact: Staged artefact under assessment.
        experiment_verdict: Pre-registered experiment outcome.
        sweep_verdict: Bounded search outcome.
        critique: Adversarial critique of the candidate.
        task_id: Owning task identity.
        lifetime_trial_ceiling: Declared cumulative search budget.
        environment: Environment the promotion targets.
        approver: Authenticated approving principal, when one approved.
        packet_hash: Assembly digest of the packet, when one was assembled.
        at_time: Optional assessment time; current UTC when omitted.

    Returns:
        What the gates concluded, promotable or terminated.
    """
    now = at_time if at_time is not None else utc_now()
    logger.info("Assessing promotion for artefact %s", artifact.artifact_hash)

    failures: dict[str, str] = {
        "leakage": _leakage_failure(experiment_verdict) or "",
        "holdout": _holdout_failure(experiment_verdict, sweep_verdict) or "",
        "search_budget": _search_budget_failure(sweep_verdict, lifetime_trial_ceiling)
        or "",
        "provenance": _provenance_failure(artifact) or "",
        "approval": approval_refusal(approver, environment) or "",
    }

    failed_gates: list[str] = []
    reason: TerminationReason | None = None
    for gate, termination in _GATE_ORDER:
        detail = failures[gate]
        if not detail:
            continue
        failed_gates.append(f"{gate}: {detail}")
        if reason is None:
            reason = termination

    if reason is not None:
        logger.info(
            "Promotion terminated as research_only for artefact %s: %s",
            artifact.artifact_hash,
            reason,
        )

    return build_promotion_assessment(
        {
            "assessment_id": derive_stable_id(
                "id",
                f"promotion:{task_id}:{artifact.artifact_hash}",
            ),
            "task_id": task_id,
            "artifact_hash": artifact.artifact_hash,
            "packet_hash": packet_hash,
            "promotable": reason is None,
            "termination_reason": reason,
            "failed_gates": tuple(failed_gates),
            # Blocking concerns survive a passing assessment. A promotion that
            # clears every gate while a critic's concern stands is a fact the
            # record should carry, not one it should drop.
            "unresolved_concerns": critique.blocking_concerns,
            "assessed_at": now.isoformat(),
        },
    )


def transition_artifact(
    store: AgenticLifecycleStore,
    artifact_hash: str,
    artifact_id: str,
    state: ArtifactState,
    actor_id: str,
    rationale: str,
    packet: PromotionEvidencePacket | None = None,
    termination_reason: TerminationReason | None = None,
    unresolved_concerns: tuple[str, ...] = (),
    at_time: datetime | None = None,
) -> LifecycleRecord:
    """Append one governed artefact transition to the append-only ledger.

    The current state comes from the ledger, never from the caller, so a caller
    cannot declare an artefact `approved` by asserting it was `evaluated`.

    Args:
        store: Injected durable lifecycle ledger.
        artifact_hash: Digest of the exact artefact.
        artifact_id: Artefact identity, for operator readability.
        state: State to record.
        actor_id: Principal or process recording the transition.
        rationale: Why the transition is being recorded.
        packet: Packet justifying the transition, when one applies.
        termination_reason: Why promotion terminated, for `research_only`.
        unresolved_concerns: Concerns preserved alongside the transition.
        at_time: Optional record time; current UTC when omitted.

    Returns:
        The appended immutable record.

    Raises:
        ValueError: If the transition is not permitted from the recorded state,
            or the packet does not describe this artefact.
    """
    now = at_time if at_time is not None else utc_now()
    current = store.current_state(artifact_hash)
    failure = validate_transition(current, state)
    if failure is not None:
        raise ValueError(failure)
    if packet is not None and packet.artifact.artifact_hash != artifact_hash:
        message = (
            f"the packet describes artefact {packet.artifact.artifact_hash}, "
            f"not {artifact_hash}"
        )
        raise ValueError(message)

    sequence = store.next_sequence(artifact_hash)
    record = build_lifecycle_record(
        {
            "record_id": derive_stable_id(
                "id",
                f"lifecycle:{artifact_hash}:{sequence}",
            ),
            "artifact_hash": artifact_hash,
            "artifact_id": artifact_id,
            "sequence": sequence,
            "previous_state": current,
            "state": state,
            "packet_hash": packet.packet_hash if packet is not None else None,
            "termination_reason": termination_reason,
            "actor_id": actor_id,
            "rationale": rationale,
            "unresolved_concerns": unresolved_concerns,
            "recorded_at": now.isoformat(),
        },
    )
    appended = store.append_record(record)
    if packet is not None:
        store.save_packet(packet)
    logger.info(
        "Artefact %s transitioned %s -> %s at position %d",
        artifact_hash,
        current or "none",
        state,
        sequence,
    )
    return appended


def get_artifact_history(
    store: AgenticLifecycleStore,
    artifact_hash: str,
) -> tuple[LifecycleRecord, ...]:
    """Return one artefact's complete transition history.

    Args:
        store: Injected durable lifecycle ledger.
        artifact_hash: Digest of the exact artefact.

    Returns:
        Ordered transition records, empty when unrecorded.
    """
    return store.list_records(artifact_hash)


def get_artifact_state(
    store: AgenticLifecycleStore,
    artifact_hash: str,
) -> ArtifactState | None:
    """Return one artefact's current recorded state.

    Args:
        store: Injected durable lifecycle ledger.
        artifact_hash: Digest of the exact artefact.

    Returns:
        The most recent state, or None when unrecorded.
    """
    return store.current_state(artifact_hash)


def can_transition(
    store: AgenticLifecycleStore,
    artifact_hash: str,
    state: ArtifactState,
) -> str | None:
    """Report why one artefact may not enter a state.

    Args:
        store: Injected durable lifecycle ledger.
        artifact_hash: Digest of the exact artefact.
        state: State the caller wants to record.

    Returns:
        A refusal message, or None when the transition is permitted.
    """
    return validate_transition(store.current_state(artifact_hash), state)


def is_settled(store: AgenticLifecycleStore, artifact_hash: str) -> bool:
    """Report whether an artefact has reached a state nothing follows.

    Args:
        store: Injected durable lifecycle ledger.
        artifact_hash: Digest of the exact artefact.

    Returns:
        True when the artefact's current state is terminal.
    """
    current = store.current_state(artifact_hash)
    return current is not None and is_terminal_state(current)
