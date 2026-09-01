"""Bounded evidence-backed deliberation that preserves dissent.

Independent briefs are collected before any participant sees a peer
conclusion: the brief invocation is built from the assembled context alone, so
peer exposure is structurally impossible rather than merely discouraged.

Caps come from the versioned limits profile and the plan. A model may decline
to use its allowance; nothing in this module lets it raise one. Stop
conditions are deterministic — more discussion is never an automatic remedy
for uncertainty.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.agentic._limits import resolve_limits_profile
from app.agentic.context_memory.repository import store_memory
from app.agentic.contracts.models import build_agent_message
from app.agentic.deliberation.models import (
    Counterclaim,
    DeliberationPlan,
    DeliberationRecord,
    DissentRecord,
    derive_record_hash,
)
from app.agentic.governance.registry import list_enabled_roles, resolve_role_manifest
from app.agentic.runtime.models import build_model_invocation
from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.kernel.time import utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.agentic.context_memory.models import ContextBundle
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentMessage, AgentTask
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelProfile

logger = get_logger(__name__)

_BRIEF_NODE = "collect_briefs"

# A dedicated synthesizer is only assigned once the council is large enough for
# the proposer and the synthesizer to be different roles.
_MIN_PARTICIPANTS_FOR_SYNTHESIZER = 2


def _select_participants(
    registry: RoleRegistry,
    requested_roles: tuple[str, ...],
    max_participants: int,
) -> tuple[str, ...]:
    """Select participants deterministically from enabled roles only.

    A request naming a disabled or unregistered role does not fail the run; the
    role is simply not selected. Selection is then truncated to the cap in a
    stable order, so an inflated request cannot widen the council.

    Args:
        registry: Validated role registry.
        requested_roles: Roles the caller or planner proposed.
        max_participants: Deterministic participant cap.

    Returns:
        Ordered selected role identities.
    """
    enabled = set(list_enabled_roles(registry))
    selected = tuple(sorted(role for role in set(requested_roles) if role in enabled))
    dropped = sorted(set(requested_roles) - enabled)
    if dropped:
        logger.warning(
            "Excluding %d requested roles that are not enabled: %s",
            len(dropped),
            ", ".join(dropped),
        )
    return selected[:max_participants]


def _assign_stances(participants: tuple[str, ...]) -> Mapping[str, str]:
    """Assign per-task challenge stances deterministically.

    Stances are task-local assignments, not standing beliefs, and no role
    serves as both sole proposer and sole synthesizer.

    Args:
        participants: Ordered selected role identities.

    Returns:
        Stance by role identity.
    """
    if not participants:
        return {}
    stances: dict[str, str] = {participants[0]: "proposer"}
    for index, role in enumerate(participants[1:], start=1):
        is_last = index == len(participants) - 1
        if is_last and len(participants) > _MIN_PARTICIPANTS_FOR_SYNTHESIZER:
            stances[role] = "synthesizer"
        elif index % 2 == 1:
            stances[role] = "adversarial_challenger"
        else:
            stances[role] = "constructive_challenger"
    return stances


def _build_plan(
    task: AgentTask,
    participants: tuple[str, ...],
    limits_profile_id: str,
    at_time: datetime,
) -> DeliberationPlan:
    """Build the deterministic plan the deliberation runs under.

    Args:
        task: Bounded governed task.
        participants: Ordered selected role identities.
        limits_profile_id: Versioned limits profile identity.
        at_time: Plan creation time.

    Returns:
        The validated deliberation plan.
    """
    limits = resolve_limits_profile(limits_profile_id)
    return DeliberationPlan(
        plan_id=derive_stable_id("id", f"plan:{task.task_id}"),
        task_id=task.task_id,
        objective=task.objective,
        topology="independent_briefs_then_bounded_challenge",
        participants=participants,
        stances=_assign_stances(participants),
        max_participants=limits.max_participants,
        max_rounds=limits.max_rounds,
        max_fan_out=limits.max_fan_out,
        deadline_at=task.deadline_at,
        budgets=dict(task.budgets),
        limits_profile_id=limits_profile_id,
        created_at=at_time,
    )


def _message(
    task: AgentTask,
    role_id: str,
    role_version: str,
    recipient: str,
    message_type: str,
    round_index: int,
    content: Mapping[str, str],
) -> AgentMessage:
    """Build one typed deliberation message.

    Args:
        task: Owning governed task.
        role_id: Sending role identity.
        role_version: Sending role version.
        recipient: Recipient role identity.
        message_type: Registered message type.
        round_index: Zero-based round.
        content: Bounded typed content.

    Returns:
        A validated immutable message.
    """
    return build_agent_message(
        {
            "message_id": derive_stable_id(
                "id",
                f"msg:{task.task_id}:{role_id}:{message_type}:{round_index}",
            ),
            "task_id": task.task_id,
            "sender_role_id": role_id,
            "sender_role_version": role_version,
            "recipient_role_id": recipient,
            "message_type": message_type,
            "round_index": round_index,
            "content": dict(content),
            "evidence_refs": (),
            "created_at": task.created_at,
            "request_id": task.request_id,
            "workflow_id": task.workflow_id,
            "correlation_id": task.correlation_id,
            "causation_id": task.causation_id,
        },
    )


def _collect_independent_briefs(
    registry: RoleRegistry,
    task: AgentTask,
    plan: DeliberationPlan,
    context: ContextBundle,
    runtime: AdkRuntime,
    profile: ModelProfile,
) -> tuple[tuple[AgentMessage, ...], tuple[str, ...]]:
    """Collect one independent brief per participant before peer exposure.

    Each invocation is built from the assembled context only. No peer output
    is available to construct it, so the independence property is structural.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        plan: Deterministic deliberation plan.
        context: Assembled bounded context.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.

    Returns:
        The ordered briefs and the ordered roles that refused.
    """
    briefs: list[AgentMessage] = []
    refusals: list[str] = []
    evidence = {claim.claim_id: claim.statement for claim in context.untrusted_evidence}
    for role_id in plan.participants:
        manifest = resolve_role_manifest(registry, role_id)
        invocation = build_model_invocation(
            {
                "invocation_id": derive_stable_id(
                    "id", f"brief:{task.task_id}:{role_id}"
                ),
                "task_id": task.task_id,
                "role_id": role_id,
                "composite_instruction_hash": manifest.composite_instruction_hash,
                "trusted_context": dict(context.trusted_context),
                "untrusted_evidence": evidence,
                "max_output_tokens": min(profile.max_output_tokens, 2_000),
                "seed": None,
            },
        )
        outcome = runtime.execute_node(_BRIEF_NODE, profile, invocation)
        if outcome.status != "ok" or outcome.output is None:
            logger.info("Role %s refused during independent briefs", role_id)
            refusals.append(role_id)
            continue
        briefs.append(
            _message(
                task,
                role_id,
                manifest.version,
                plan.participants[0],
                "brief",
                0,
                dict(outcome.output),
            ),
        )
    return tuple(briefs), tuple(refusals)


def _run_challenge_rounds(
    registry: RoleRegistry,
    task: AgentTask,
    plan: DeliberationPlan,
    briefs: tuple[AgentMessage, ...],
) -> tuple[tuple[Counterclaim, ...], int]:
    """Run bounded rebuttal rounds over the collected briefs.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        plan: Deterministic deliberation plan.
        briefs: Independent briefs collected in phase one.

    Returns:
        The ordered counterclaims and the number of rounds consumed.
    """
    challengers = tuple(
        role
        for role, stance in sorted(plan.stances.items())
        if stance in {"adversarial_challenger", "constructive_challenger"}
    )
    if not challengers or not briefs:
        return (), 0

    counterclaims: list[Counterclaim] = []
    rounds = 0
    for round_index in range(plan.max_rounds):
        rounds = round_index + 1
        for challenger in challengers[: plan.max_fan_out]:
            manifest = resolve_role_manifest(registry, challenger)
            target = briefs[0]
            counterclaims.append(
                Counterclaim(
                    counterclaim_id=derive_stable_id(
                        "id",
                        f"cc:{task.task_id}:{challenger}:{round_index}",
                    ),
                    task_id=task.task_id,
                    round_index=round_index,
                    challenger_role_id=challenger,
                    stance=plan.stances[challenger],  # type: ignore[arg-type]
                    targets_claim_id=target.message_id,
                    statement=(
                        f"Role {challenger} version {manifest.version} challenges the "
                        "proposer brief and requests deterministic confirmation."
                    ),
                    evidence_refs=(),
                    resolved=False,
                ),
            )
    return tuple(counterclaims), rounds


def _preserve_dissent(
    task: AgentTask,
    counterclaims: tuple[Counterclaim, ...],
) -> tuple[DissentRecord, ...]:
    """Convert every unresolved challenge into preserved dissent.

    Synthesis never discards a credible unresolved counterclaim; it is
    recorded so the operator sees the disagreement.

    Args:
        task: Bounded governed task.
        counterclaims: Challenges raised during deliberation.

    Returns:
        The ordered preserved dissent records.
    """
    return tuple(
        DissentRecord(
            dissent_id=derive_stable_id(
                "id",
                f"dissent:{task.task_id}:{item.counterclaim_id}",
            ),
            task_id=task.task_id,
            dissenting_role_id=item.challenger_role_id,
            statement=item.statement,
            basis="conflicting_evidence",
            targets_claim_id=item.targets_claim_id,
            unresolved=True,
        )
        for item in counterclaims
        if not item.resolved
    )


def _terminal_reason(
    participants: tuple[str, ...],
    briefs: tuple[AgentMessage, ...],
    dissent: tuple[DissentRecord, ...],
    rounds_used: int,
    plan: DeliberationPlan,
    now: datetime,
) -> str:
    """Determine the deterministic stop reason.

    Args:
        participants: Selected participants.
        briefs: Collected independent briefs.
        dissent: Preserved dissent.
        rounds_used: Rounds consumed.
        plan: Deterministic plan.
        now: Completion time.

    Returns:
        The enumerated terminal reason.
    """
    if not participants:
        return "no_eligible_participants"
    if not briefs:
        return "insufficient_evidence"
    if now >= plan.deadline_at:
        return "deadline_exceeded"
    if any(item.unresolved for item in dissent):
        return "material_unresolved_conflict"
    if rounds_used >= plan.max_rounds and dissent:
        return "max_rounds_reached"
    return "objective_complete"


def run_deliberation(
    registry: RoleRegistry,
    task: AgentTask,
    context: ContextBundle,
    runtime: AdkRuntime,
    profile: ModelProfile,
    requested_roles: tuple[str, ...],
    limits_profile_id: str = "agentic-limits-sandbox-v1",
    memory_store: AgenticMemoryStore | None = None,
    at_time: datetime | None = None,
) -> DeliberationRecord:
    """Run one bounded evidence-backed deliberation.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        context: Assembled bounded eligible context.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        requested_roles: Roles the caller or planner proposed.
        limits_profile_id: Versioned limits profile supplying the caps.
        memory_store: Optional governed audit store for the record.
        at_time: Optional completion time; current UTC when omitted.

    Returns:
        The immutable deliberation record, including any preserved dissent.
    """
    now = at_time if at_time is not None else utc_now()
    limits = resolve_limits_profile(limits_profile_id)
    participants = _select_participants(
        registry,
        requested_roles,
        limits.max_participants,
    )
    plan = _build_plan(task, participants, limits_profile_id, now)
    logger.info(
        "Running deliberation for task %s with %d participants and %d max rounds",
        task.task_id,
        len(participants),
        plan.max_rounds,
    )

    briefs, refusals = _collect_independent_briefs(
        registry,
        task,
        plan,
        context,
        runtime,
        profile,
    )
    counterclaims, rounds_used = _run_challenge_rounds(registry, task, plan, briefs)
    dissent = _preserve_dissent(task, counterclaims)
    reason = _terminal_reason(participants, briefs, dissent, rounds_used, plan, now)

    synthesis: str | None = None
    if reason != "insufficient_evidence" and briefs:
        synthesis = (
            f"{len(briefs)} independent briefs were collected before peer exposure; "
            f"{len(counterclaims)} challenges were raised and {len(dissent)} remain "
            "unresolved. This synthesis is advisory evidence only."
        )
    messages = tuple(briefs)
    record_material = {
        "plan": plan.model_dump(mode="json"),
        "messages": [message.model_dump(mode="json") for message in messages],
        "counterclaims": [item.model_dump(mode="json") for item in counterclaims],
        "dissent": [item.model_dump(mode="json") for item in dissent],
        "synthesis": synthesis,
        "terminal_reason": reason,
    }

    persisted = False
    if memory_store is not None:
        store_memory(
            memory_store,
            "audit",
            task.task_id,
            plan.participants[0] if plan.participants else "firm_coordinator",
            {"terminal_reason": reason, "synthesis": synthesis or "none"},
            {"environment": "sandbox"},
            "audit-730d",
            at_time=now,
        )
        persisted = True

    logger.info(
        "Deliberation for task %s ended: %s (%d dissent preserved)",
        task.task_id,
        reason,
        len(dissent),
    )
    return DeliberationRecord(
        record_id=derive_stable_id("id", f"deliberation:{task.task_id}"),
        task_id=task.task_id,
        plan=plan,
        messages=messages,
        counterclaims=counterclaims,
        dissent=dissent,
        synthesis=synthesis,
        # Consensus requires briefs and no unresolved dissent. It is a
        # description of agreement and confers no authorization whatsoever.
        consensus_reached=bool(briefs) and not dissent,
        rounds_used=rounds_used,
        participants_used=len(briefs),
        refusals=refusals,
        terminal_reason=reason,  # type: ignore[arg-type]
        persisted=persisted,
        created_at=now,
        content_hash=derive_record_hash(record_material),
    )
