"""Provider-neutral Trader agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates narrative to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. The
instrument, strategy identity, direction, horizon, and evaluation scope come
from the caller, so the model contributes the rationale, the invalidation, and
the uncertainty but cannot choose what is being proposed (`FR-AGENTIC-058`).
Evidence references come from the thesis, not from the model, so a proposal
cannot cite something that was never gathered. And the proposal window is
checked against the receiver's own horizon rule before submission, so a
proposal this domain builds cannot fail Strategy on a constraint that could
have been applied here.

This module composes; it does not submit. `handoff.py` owns the receiver
mapping, and nothing in this package names Risk, Trading, or Brokers.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.strategy_desk.trader.schemas import (
    MAX_HORIZON_SECONDS,
    TradeProposal,
    build_trade_proposal,
)
from app.agentic.contracts.models import (
    build_agent_provenance,
    build_agent_result,
    build_budget_usage,
)
from app.agentic.governance.registry import (
    resolve_role_manifest,
    verify_prompt_artifact,
)
from app.agentic.runtime.models import build_model_invocation
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.agentic.agents.strategy_desk.strategy_thesis_analyst.schemas import (
        StrategyThesis,
    )
    from app.agentic.agents.strategy_desk.trader.schemas import (
        EvaluationScope,
        ProposalDirection,
    )
    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.governance.models import RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "trader"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_PROPOSE_NODE_ID = "propose_trade"

# Only a supported thesis is a basis for a trade proposal. `unsupported` and
# `insufficient_evidence` speak for themselves; `contested` is excluded on
# purpose — a thesis whose evidence conflicts is a thesis to resolve, not to
# trade, and proposing on one would bury the conflict `FEAT-AGT-13` preserved.
# The stance comes from the thesis and is not the model's to reinterpret.
PROPOSABLE_STANCES: frozenset[str] = frozenset({"supported"})


def _envelope(task: AgentTask, at_time: datetime) -> dict[str, object]:
    """Return the shared identity, time, and lineage envelope.

    Args:
        task: Owning governed task.
        at_time: Result time.

    Returns:
        The shared contract envelope fields.
    """
    return {
        "created_at": at_time,
        "request_id": task.request_id,
        "workflow_id": task.workflow_id,
        "correlation_id": task.correlation_id,
        "causation_id": task.causation_id,
    }


def _provenance(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    at_time: datetime,
) -> object:
    """Build the reproducible lineage for one proposal.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        at_time: Result time.

    Returns:
        A validated immutable provenance record.
    """
    return build_agent_provenance(
        {
            **_envelope(task, at_time),
            "provenance_id": derive_stable_id("id", f"prov:{task.task_id}:{ROLE_ID}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "role_version": manifest.version,
            "model_profile_id": profile.profile_id,
            "model_provider": profile.provider,
            "model_identifier": profile.model_identifier,
            "base_prompt_hash": manifest.base_prompt_hash,
            "manifest_hash": manifest.manifest_hash,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "tool_refs": manifest.tools,
            "evidence_refs": task.input_refs,
            "mandate_id": "mandate-resolved-at-composition",
            "mandate_version": manifest.version,
            "policy_version": manifest.version,
            "limits_profile_id": manifest.evaluation_set_id,
            "seed": None,
        },
    )


def _usage(
    task: AgentTask,
    at_time: datetime,
    outcome: ModelOutcome | None,
) -> object:
    """Build the bounded consumption record for one proposal.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.

    Returns:
        A validated immutable usage record.
    """
    return build_budget_usage(
        {
            **_envelope(task, at_time),
            "usage_id": derive_stable_id("id", f"usage:{task.task_id}:{ROLE_ID}"),
            "task_id": task.task_id,
            "tokens": 0 if outcome is None else outcome.tokens_used,
            "model_calls": 0 if outcome is None else 1,
            "tool_calls": 0,
            "cost": Decimal(0) if outcome is None else outcome.cost,
            "compute_seconds": Decimal(0),
            "storage_bytes": 0,
            "search_trials": 0,
        },
    )


def _refuse(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    outcome: ModelOutcome | None = None,
) -> AgentResult[TradeProposal]:
    """Build one typed refusal carrying provenance and usage.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        reasons: Ordered enumerated refusal codes.
        detail: Bounded advisory detail.
        at_time: Refusal time.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Trader refusing proposal for task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"propose:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome),
        },
    )


def _lines(value: str | None) -> tuple[str, ...]:
    """Split one bounded newline-delimited model field.

    Args:
        value: Candidate field value.

    Returns:
        Ordered unique non-empty trimmed lines.
    """
    if not value:
        return ()
    seen: dict[str, None] = {}
    for line in value.splitlines():
        trimmed = line.strip()
        if trimmed:
            seen.setdefault(trimmed, None)
    return tuple(seen)


def _precheck(
    thesis: StrategyThesis,
    horizon_seconds: int,
    validity_seconds: int,
) -> tuple[str, str] | None:
    """Report why a thesis cannot become a proposal.

    Kept apart from `propose_trade` so the pre-model conditions are one branch
    there, and so all three are stated in one place.

    Args:
        thesis: Strategy thesis the proposal would rest on.
        horizon_seconds: Declared horizon of the view.
        validity_seconds: How long the proposal remains submittable.

    Returns:
        An enumerated reason and detail, or None when the thesis may proceed.
    """
    if thesis.stance not in PROPOSABLE_STANCES:
        return (
            "THESIS_NOT_PROPOSABLE",
            f"A {thesis.stance!r} thesis is not a basis for a trade proposal.",
        )
    if not thesis.supporting_evidence:
        return (
            "THESIS_EVIDENCE_ABSENT",
            "A trade proposal requires the evidence its thesis rests on.",
        )
    if horizon_seconds <= 0 or horizon_seconds > MAX_HORIZON_SECONDS:
        return (
            "HORIZON_OUT_OF_BOUNDS",
            (
                "A proposal horizon must be positive and no greater than "
                f"{MAX_HORIZON_SECONDS} seconds, the receiver's own bound."
            ),
        )
    if validity_seconds <= 0 or validity_seconds > horizon_seconds:
        return (
            "PROPOSAL_WINDOW_INVALID",
            (
                "A proposal must remain valid for a positive interval no longer "
                "than its declared horizon."
            ),
        )
    return None


def propose_trade(
    registry: RoleRegistry,
    task: AgentTask,
    runtime: AdkRuntime,
    profile: ModelProfile,
    thesis: StrategyThesis,
    strategy_id: str,
    strategy_version: str,
    instrument: str,
    direction: ProposalDirection,
    horizon_seconds: int,
    evaluation_scope: EvaluationScope,
    validity_seconds: int | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[TradeProposal]:
    """Compose one non-executable trade proposal from a strategy thesis.

    What is being proposed — instrument, strategy identity, direction, horizon,
    and evaluation scope — comes from the caller. The model contributes the
    rationale, the invalidation, and the uncertainty, and nothing else.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        thesis: Strategy thesis the proposal rests on.
        strategy_id: Registered strategy the receiver evaluates against.
        strategy_version: Exact registered version.
        instrument: Instrument the view concerns.
        direction: Direction of the view.
        horizon_seconds: How long the view is claimed to hold.
        evaluation_scope: What the proposal asks the receiver to do.
        validity_seconds: How long the proposal stays submittable; the whole
            horizon when omitted.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a non-executable proposal, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    validity = horizon_seconds if validity_seconds is None else validity_seconds
    logger.info(
        "Trader composing a proposal for %s from thesis %s",
        instrument,
        thesis.thesis_id,
    )

    failure = _precheck(thesis, horizon_seconds, validity)
    if failure is not None:
        reason, detail = failure
        return _refuse(task, manifest, profile, (reason,), detail, now)

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"propose:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "thesis_id": thesis.thesis_id,
                "thesis_stance": thesis.stance,
                "instrument": instrument,
                "direction": direction,
                "horizon_seconds": str(horizon_seconds),
                "evaluation_scope": evaluation_scope,
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
            },
            "untrusted_evidence": {
                "thesis_summary": thesis.summary,
                "thesis_uncertainty": thesis.uncertainty,
                **{
                    f"signal:{key}": value
                    for key, value in sorted(thesis.signals.items())
                },
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_PROPOSE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The trader declined to compose a proposal.",
            now,
            outcome,
        )

    try:
        proposal = build_trade_proposal(
            {
                "proposal_id": derive_stable_id("id", f"propose:{task.task_id}"),
                "task_id": task.task_id,
                "thesis_id": thesis.thesis_id,
                # What is proposed comes from the caller; the model describes
                # it and cannot choose it.
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
                "instrument": instrument,
                "direction": direction,
                "horizon_seconds": horizon_seconds,
                "evaluation_scope": evaluation_scope,
                "rationale": outcome.output.get("rationale", ""),
                "invalidation": _lines(outcome.output.get("invalidation")),
                # Evidence comes from the thesis, so a proposal cannot cite
                # something that was never gathered.
                "evidence_refs": thesis.supporting_evidence,
                "uncertainty": outcome.output.get("uncertainty", ""),
                "issued_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=validity)).isoformat(),
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("PROPOSAL_NOT_SUBMITTABLE",),
            str(error),
            now,
            outcome,
        )

    logger.info(
        "Trader composed proposal %s expiring at %s",
        proposal.proposal_id,
        proposal.expires_at,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"propose:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": proposal,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome),
        },
    )


def get_proposal_context(proposal: TradeProposal) -> Mapping[str, str]:
    """Return the bounded operator view of one proposal.

    Args:
        proposal: Composed proposal.

    Returns:
        Bounded readable fields, carrying nothing executable.
    """
    return {
        "proposal_id": proposal.proposal_id,
        "thesis_id": proposal.thesis_id,
        "instrument": proposal.instrument,
        "direction": proposal.direction,
        "horizon_seconds": str(proposal.horizon_seconds),
        "evaluation_scope": proposal.evaluation_scope,
        "expires_at": proposal.expires_at,
    }
