"""Provider-neutral Portfolio and Risk Advisor agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates narrative to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. Evidence
is current: every read carries its observation instant, and evidence older than
the declared freshness bound refuses before any model call (`FR-AGENTIC-055`).
Risk coverage is exact: all eight kinds, validated by set equality
(`FR-AGENTIC-056`). And mandate scope comes from Risk, not from the model, so a
proposal cannot quietly widen the asset class or currency it was bounded by.

Nothing here approves anything. This feature emits non-binding advice; Portfolio
and Risk apply their complete normal controls to any request submitted to them,
and the submission itself belongs to `FEAT-AGT-22`. No module in this package
imports Portfolio, Risk, Analytics, or Data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    REQUIRED_RISK_KINDS,
    AllocationProposal,
    RiskAdvisory,
    build_allocation_proposal,
    build_risk_advisory,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (
    ACCOUNT_STATE_TOOL,
    ALLOCATION_EVIDENCE_TOOL,
    COMMON_MODE_TOOL,
    CORRELATION_TOOL,
    FIRM_MANDATE_TOOL,
    OBSERVED_AT_KEY,
    call_advisory_tool,
    verify_mandate,
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
    from collections.abc import Callable, Mapping

    from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (  # noqa: E501
        PortfolioRiskEvidencePort,
    )
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.deliberation.models import DeliberationRecord
    from app.agentic.governance.models import FirmMandate, RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "portfolio_risk_advisor"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_ADVISE_NODE_ID = "advise_portfolio"
_CRITIQUE_NODE_ID = "critique_risk"

_WEIGHT_PREFIX = "weight:"
_ASSESSMENT_PREFIX = "risk:"

# The advisory validity window when the caller declares none. Deliberately
# short: the evidence behind an allocation view moves within a session.
DEFAULT_VALIDITY_SECONDS = 3_600


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
    """Build the reproducible lineage for one advisory operation.

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
    tool_calls: int,
) -> object:
    """Build the bounded consumption record for one advisory operation.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.
        tool_calls: Governed tool calls attempted.

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
            "tool_calls": tool_calls,
            "cost": Decimal(0) if outcome is None else outcome.cost,
            "compute_seconds": Decimal(0),
            "storage_bytes": 0,
            "search_trials": 0,
        },
    )


def _refuse[T](
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    kind: str,
    tool_calls: int = 0,
    outcome: ModelOutcome | None = None,
) -> AgentResult[T]:
    """Build one typed refusal carrying provenance and usage.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        reasons: Ordered enumerated refusal codes.
        detail: Bounded advisory detail.
        at_time: Refusal time.
        kind: Operation label distinguishing the two public use cases.
        tool_calls: Governed tool calls attempted.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Portfolio risk advisor refusing %s for task %s: %s",
        kind,
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"{kind}:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


class _Evidence:
    """Advisory evidence gathered from the port before any judgement.

    Attributes:
        refusal: Enumerated reason and detail when gathering failed.
        readings: Tool identity to the receiver's returned evidence.
        observed_at: Tool identity to the observation instant read from it.
        tool_calls: Governed tool calls attempted.
    """

    __slots__ = ("observed_at", "readings", "refusal", "tool_calls")

    def __init__(
        self,
        refusal: tuple[str, str] | None,
        readings: Mapping[str, Mapping[str, str]],
        observed_at: Mapping[str, str],
        tool_calls: int,
    ) -> None:
        """Store the gathered evidence.

        Args:
            refusal: Enumerated reason and detail, or None.
            readings: Tool identity to receiver evidence.
            observed_at: Tool identity to observation instant.
            tool_calls: Governed tool calls attempted.
        """
        self.refusal = refusal
        self.readings = readings
        self.observed_at = observed_at
        self.tool_calls = tool_calls


def _bind_reader(
    reader: Callable[[str], Mapping[str, str]],
    portfolio_id: str,
) -> Callable[[], Mapping[str, object]]:
    """Bind one evidence reader to a portfolio identity.

    Args:
        reader: Receiver operation taking a portfolio identity.
        portfolio_id: Portfolio under advisement.

    Returns:
        A zero-argument callable performing the read.
    """

    def read() -> Mapping[str, object]:
        """Perform the bound evidence read.

        Returns:
            The receiver's evidence.
        """
        return reader(portfolio_id)

    return read


def _gather(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: PortfolioRiskEvidencePort,
    portfolio_id: str,
    principal_id: str,
    task_id: str,
    scope: Mapping[str, str],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> _Evidence:
    """Read every required piece of advisory evidence through the tool path.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected advisory-evidence port.
        portfolio_id: Portfolio under advisement.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        scope: Scope declared for the tool calls.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.

    Returns:
        The gathered evidence, carrying a refusal when it could not complete.
    """
    empty: Mapping[str, Mapping[str, str]] = {}
    readers = (
        (ALLOCATION_EVIDENCE_TOOL, port.get_allocation_evidence),
        (COMMON_MODE_TOOL, port.get_common_mode_exposure),
        (CORRELATION_TOOL, port.get_cross_account_correlation),
        (ACCOUNT_STATE_TOOL, port.get_account_state),
        (FIRM_MANDATE_TOOL, port.get_firm_mandate),
    )
    missing = tuple(name for name, _ in readers if name not in tool_policies)
    if missing:
        return _Evidence(
            (
                "ADVISORY_TOOL_DENIED",
                f"Required advisory tools are not registered: {', '.join(missing)}.",
            ),
            empty,
            {},
            0,
        )

    gathered: dict[str, Mapping[str, str]] = {}
    observed: dict[str, str] = {}
    attempted = 0
    for name, reader in readers:
        attempted += 1
        outcome = call_advisory_tool(
            mandate,
            policy,
            tool_policies[name],
            principal_id,
            task_id,
            scope,
            _bind_reader(reader, portfolio_id),
            at_time,
            nonce_store=nonce_store,
            audit_store=audit_store,
            calls_used=attempted - 1,
        )
        if not outcome.allowed or not outcome.payload:
            return _Evidence(
                (
                    "ADVISORY_TOOL_DENIED",
                    f"{name} returned no evidence: {outcome.denial_reason}.",
                ),
                empty,
                {},
                attempted,
            )
        payload = {key: str(value) for key, value in outcome.payload.items()}
        stamp = payload.get(OBSERVED_AT_KEY, "")
        if not stamp:
            return _Evidence(
                (
                    "EVIDENCE_UNDATED",
                    f"{name} returned evidence without an observation time.",
                ),
                empty,
                {},
                attempted,
            )
        gathered[name] = payload
        observed[name] = stamp

    return _Evidence(None, gathered, observed, attempted)


def _stale_readings(
    observed_at: Mapping[str, str],
    at_time: datetime,
    max_age_seconds: int,
) -> tuple[str, ...]:
    """Return the evidence reads older than the declared freshness bound.

    An unreadable instant counts as stale. Evidence whose age cannot be
    established is not fresh evidence.

    Args:
        observed_at: Tool identity to observation instant.
        at_time: Instant to judge freshness at.
        max_age_seconds: Maximum permitted evidence age.

    Returns:
        Ordered tool identities whose evidence is too old.
    """
    stale: list[str] = []
    for name, stamp in sorted(observed_at.items()):
        try:
            observed = datetime.fromisoformat(stamp)
        except ValueError:
            stale.append(name)
            continue
        if observed.tzinfo is None:
            stale.append(name)
            continue
        if (at_time - observed).total_seconds() > max_age_seconds:
            stale.append(name)
    return tuple(stale)


def _precheck(
    evidence: _Evidence,
    at_time: datetime,
    max_age_seconds: int,
) -> tuple[str, str] | None:
    """Report why gathered evidence cannot support a proposal.

    Kept apart from `advise_portfolio` so the two pre-model conditions are one
    branch there rather than two, and so both are stated in one place.

    Args:
        evidence: Gathered advisory evidence.
        at_time: Instant to judge freshness at.
        max_age_seconds: Maximum permitted evidence age.

    Returns:
        An enumerated reason and detail, or None when the evidence holds.
    """
    stale = _stale_readings(evidence.observed_at, at_time, max_age_seconds)
    if stale:
        return (
            "EVIDENCE_STALE",
            (
                "Evidence older than the declared freshness bound of "
                f"{max_age_seconds}s: {', '.join(stale)}."
            ),
        )
    mandate_failure = verify_mandate(evidence.readings[FIRM_MANDATE_TOOL])
    if mandate_failure is not None:
        return ("MANDATE_SCOPE_UNAVAILABLE", mandate_failure)
    return None


def _section(output: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Extract one prefixed section from a model output.

    Args:
        output: Model output mapping.
        prefix: Section prefix to select.

    Returns:
        The section entries keyed without their prefix.
    """
    return {
        key.removeprefix(prefix): value
        for key, value in sorted(output.items())
        if key.startswith(prefix)
    }


def _lines(value: str | None) -> tuple[str, ...]:
    """Split one bounded newline-delimited model field.

    Args:
        value: Candidate field value.

    Returns:
        Ordered non-empty trimmed lines.
    """
    if not value:
        return ()
    return tuple(line.strip() for line in value.splitlines() if line.strip())


def advise_portfolio(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: PortfolioRiskEvidencePort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    portfolio_id: str,
    max_evidence_age_seconds: int,
    validity_seconds: int = DEFAULT_VALIDITY_SECONDS,
    principal_id: str = "agent-portfolio-risk-advisor",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[AllocationProposal]:
    """Produce one non-binding allocation proposal from current evidence.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected advisory-evidence port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        portfolio_id: Portfolio under advisement.
        max_evidence_age_seconds: Maximum permitted evidence age.
        validity_seconds: How long the proposal remains current.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a non-binding proposal, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Portfolio risk advisor advising portfolio %s", portfolio_id)

    if validity_seconds <= 0:
        return _refuse(
            task,
            manifest,
            profile,
            ("ADVICE_VALIDITY_INVALID",),
            "A proposal must remain valid for a positive interval.",
            now,
            "advise",
        )

    evidence = _gather(
        mandate,
        policy,
        tool_policies,
        port,
        portfolio_id,
        principal_id,
        task.task_id,
        scope,
        now,
        nonce_store,
        audit_store,
    )
    failure = evidence.refusal
    if failure is None:
        failure = _precheck(evidence, now, max_evidence_age_seconds)
    if failure is not None:
        reason, detail = failure
        return _refuse(
            task,
            manifest,
            profile,
            (reason,),
            detail,
            now,
            "advise",
            evidence.tool_calls,
        )

    mandate_evidence = evidence.readings[FIRM_MANDATE_TOOL]
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"advise:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "portfolio_id": portfolio_id,
                "mandate_id": mandate_evidence["mandate_id"],
                "mandate_version": mandate_evidence["mandate_version"],
                "asset_class": mandate_evidence["asset_class"],
                "base_currency": mandate_evidence["base_currency"],
                "max_evidence_age_seconds": str(max_evidence_age_seconds),
            },
            "untrusted_evidence": {
                f"{name}:{key}": value
                for name, reading in sorted(evidence.readings.items())
                for key, value in sorted(reading.items())
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_ADVISE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The advisor declined to describe the allocation.",
            now,
            "advise",
            evidence.tool_calls,
            outcome,
        )

    try:
        proposal = build_allocation_proposal(
            {
                "proposal_id": derive_stable_id("id", f"advise:{task.task_id}"),
                "task_id": task.task_id,
                "portfolio_id": portfolio_id,
                # Scope comes from Risk, never from the model, so a proposal
                # cannot quietly widen the mandate it was bounded by.
                "mandate_id": mandate_evidence["mandate_id"],
                "mandate_version": mandate_evidence["mandate_version"],
                "asset_class": mandate_evidence["asset_class"],
                "base_currency": mandate_evidence["base_currency"],
                "relative_weights": _section(outcome.output, _WEIGHT_PREFIX),
                "rationale": outcome.output.get("rationale", ""),
                "constraints_respected": _lines(
                    outcome.output.get("constraints_respected"),
                ),
                "evidence_refs": tuple(sorted(evidence.readings)),
                "evidence_observed_at": dict(evidence.observed_at),
                "limitations": _lines(outcome.output.get("limitations")),
                "issued_at": now.isoformat(),
                "expires_at": _expiry(now, validity_seconds),
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("PROPOSAL_NOT_ADVISORY",),
            str(error),
            now,
            "advise",
            evidence.tool_calls,
            outcome,
        )

    logger.info(
        "Portfolio risk advisor issued proposal %s expiring at %s",
        proposal.proposal_id,
        proposal.expires_at,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"advise:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": proposal,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, evidence.tool_calls),
        },
    )


def _expiry(issued_at: datetime, validity_seconds: int) -> str:
    """Return the expiry instant of one proposal.

    Args:
        issued_at: Issue instant.
        validity_seconds: How long the proposal remains current.

    Returns:
        The ISO-8601 expiry instant.
    """
    return (issued_at + timedelta(seconds=validity_seconds)).isoformat()


def critique_risk(
    registry: RoleRegistry,
    task: AgentTask,
    runtime: AdkRuntime,
    profile: ModelProfile,
    proposal: AllocationProposal,
    deliberation: DeliberationRecord | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[RiskAdvisory]:
    """Critique one allocation proposal across every required risk kind.

    The critique reads the proposal as untrusted evidence. It emits no
    approval, and there is no field on `RiskAdvisory` that could carry one.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        proposal: Non-binding proposal under critique.
        deliberation: Optional council record whose dissent is preserved.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a risk advisory, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info(
        "Portfolio risk advisor critiquing proposal %s",
        proposal.proposal_id,
    )

    # Critiquing an expired proposal produces advice about a portfolio state
    # that no longer holds, which is worse than declining to advise.
    if proposal.is_expired(now):
        return _refuse(
            task,
            manifest,
            profile,
            ("PROPOSAL_EXPIRED",),
            f"The proposal expired at {proposal.expires_at}.",
            now,
            "critique",
        )

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"critique:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "proposal_hash": proposal.proposal_hash,
                "portfolio_id": proposal.portfolio_id,
                "mandate_id": proposal.mandate_id,
                "asset_class": proposal.asset_class,
                "required_risk_kinds": ",".join(sorted(REQUIRED_RISK_KINDS)),
            },
            "untrusted_evidence": {
                **{
                    f"weight:{key}": value
                    for key, value in sorted(proposal.relative_weights.items())
                },
                "rationale": proposal.rationale,
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_CRITIQUE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The critic declined to critique the proposal.",
            now,
            "critique",
            outcome=outcome,
        )

    # Dissent comes from the deliberation record, not from the model. A
    # synthesis that quietly drops a minority position is misrepresenting the
    # discussion it came from, so the record is the authority on what was said.
    dissent = _preserved_dissent(deliberation)

    try:
        advisory = build_risk_advisory(
            {
                "advisory_id": derive_stable_id("id", f"critique:{task.task_id}"),
                "task_id": task.task_id,
                "proposal_id": proposal.proposal_id,
                "proposal_hash": proposal.proposal_hash,
                "portfolio_id": proposal.portfolio_id,
                "assessments": _section(outcome.output, _ASSESSMENT_PREFIX),
                "unresolved_risks": _lines(outcome.output.get("unresolved_risks")),
                "retained_dissent": dissent,
                "evidence_refs": proposal.evidence_refs,
                "issued_at": now.isoformat(),
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("RISK_COVERAGE_INCOMPLETE",),
            str(error),
            now,
            "critique",
            outcome=outcome,
        )

    logger.info(
        "Portfolio risk advisor recorded %d unresolved risks for proposal %s",
        len(advisory.unresolved_risks),
        proposal.proposal_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"critique:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": advisory,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, 0),
        },
    )


def _preserved_dissent(record: DeliberationRecord | None) -> tuple[str, ...]:
    """Return the minority positions a council left unresolved.

    Args:
        record: Council record, when a deliberation preceded this critique.

    Returns:
        Ordered preserved dissent statements.
    """
    if record is None:
        return ()
    return tuple(entry.statement for entry in record.dissent if entry.unresolved)
