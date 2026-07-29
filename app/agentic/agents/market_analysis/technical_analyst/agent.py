"""Provider-neutral Technical Analyst agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`,
gathers canonical evidence through governed tool calls, and delegates
interpretation to the injected `AdkRuntime`.

The division of authority is the point: **every binding in the output pack
comes from a deterministic tool, not from the model.** Instrument, venue,
timeframe, session, observation window, indicator versions, and quality status
are taken from what Data and Indicators returned. The model supplies only
claims, confirmations, invalidations, leakage notes, uncertainty, and
conflicts. A model cannot therefore misreport which indicator definition was
used, which is what `FR-AGENTIC-031` and `FR-AGENTIC-032` require.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.market_analysis.technical_analyst.schemas import (
    TechnicalEvidencePack,
    build_technical_evidence_pack,
)
from app.agentic.agents.market_analysis.technical_analyst.tools import (
    INDICATOR_TOOL,
    MARKET_DATA_TOOL,
    QUALITY_TOOL,
    SESSION_TOOL,
    call_evidence_tool,
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
from app.utils import derive_stable_id, get_logger, parse_utc_timestamp, utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from app.agentic.agents.market_analysis.technical_analyst.tools import (
        TechnicalEvidencePort,
    )
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.governance.models import FirmMandate, RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "technical_analyst"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_NODE_ID = "analyze_technical_context"

_ACCEPTED_QUALITY = frozenset({"passed", "warned", "calendar_unverified"})


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
    """Build the reproducible lineage for one technical reading.

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
    """Build the bounded consumption record for one technical reading.

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


def _refuse(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    tool_calls: int = 0,
    outcome: ModelOutcome | None = None,
) -> AgentResult[TechnicalEvidencePack]:
    """Build one typed refusal carrying provenance and usage.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        reasons: Ordered enumerated refusal codes.
        detail: Bounded advisory detail.
        at_time: Refusal time.
        tool_calls: Governed tool calls attempted.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Technical analyst refusing task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"tech:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


def _gather_evidence(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: TechnicalEvidencePort,
    task: AgentTask,
    instrument: str,
    timeframe: str,
    indicators: tuple[str, ...],
    request_scope: Mapping[str, str],
    principal_id: str,
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> tuple[dict[str, Mapping[str, str]], str | None, int]:
    """Gather every canonical evidence section through governed tool calls.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected receiver-domain evidence port.
        task: Owning governed task.
        instrument: Canonical instrument identity.
        timeframe: Canonical timeframe.
        indicators: Requested registered indicator names.
        request_scope: Scope declared for these calls.
        principal_id: Authenticated requesting principal.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.

    Returns:
        The gathered sections, the first denial reason if any, and the number
        of tool calls attempted.
    """
    plan = (
        (
            MARKET_DATA_TOOL,
            "market",
            lambda: port.fetch_market_evidence(
                instrument,
                timeframe,
            ),
        ),
        (QUALITY_TOOL, "quality", lambda: port.fetch_quality_evidence(instrument)),
        (SESSION_TOOL, "session", lambda: port.fetch_session_evidence(instrument)),
        (
            INDICATOR_TOOL,
            "indicators",
            lambda: port.fetch_indicator_versions(
                indicators,
            ),
        ),
    )
    gathered: dict[str, Mapping[str, str]] = {}
    attempted = 0
    for tool_name, section, receiver_call in plan:
        tool = tool_policies.get(tool_name)
        if tool is None:
            return gathered, "tool_not_registered_by_mandate", attempted
        attempted += 1
        result = call_evidence_tool(
            mandate,
            policy,
            tool,
            principal_id,
            task.task_id,
            request_scope,
            receiver_call,
            at_time,
            nonce_store=nonce_store,
            audit_store=audit_store,
            calls_used=attempted - 1,
        )
        if not result.allowed or result.payload is None:
            return gathered, result.denial_reason or "tool_denied", attempted
        gathered[section] = result.payload
    return gathered, None, attempted


def analyze_technical_context(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: TechnicalEvidencePort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    instrument: str,
    timeframe: str,
    indicators: tuple[str, ...],
    principal_id: str = "agent-technical",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[TechnicalEvidencePack]:
    """Interpret canonical Data and Indicators evidence for one instrument.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected receiver-domain evidence port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        instrument: Canonical instrument identity.
        timeframe: Canonical timeframe.
        indicators: Requested registered indicator names.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a bound technical evidence pack, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info(
        "Technical analyst starting for %s %s on task %s",
        instrument,
        timeframe,
        task.task_id,
    )

    if not indicators:
        return _refuse(
            task,
            manifest,
            profile,
            ("INDICATORS_NOT_REQUESTED",),
            "A technical reading must name the registered indicators it uses.",
            now,
        )

    gathered, denial, attempted = _gather_evidence(
        mandate,
        policy,
        tool_policies,
        port,
        task,
        instrument,
        timeframe,
        indicators,
        scope,
        principal_id,
        now,
        nonce_store,
        audit_store,
    )
    if denial is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("EVIDENCE_TOOL_DENIED",),
            f"A governed evidence tool was denied: {denial}.",
            now,
            attempted,
        )

    quality_status = gathered["quality"].get("status", "failed")
    if quality_status not in _ACCEPTED_QUALITY:
        return _refuse(
            task,
            manifest,
            profile,
            ("DATA_QUALITY_FAILED",),
            "The canonical quality evidence reports a failure.",
            now,
            attempted,
        )

    versions = gathered["indicators"]
    missing = sorted(set(indicators) - set(versions))
    if missing:
        return _refuse(
            task,
            manifest,
            profile,
            ("INDICATOR_VERSION_UNAVAILABLE",),
            "A requested indicator has no registered version.",
            now,
            attempted,
        )

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"tech:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # Bindings are trusted structured context: they came from
            # deterministic tools, not from any model.
            "trusted_context": {
                "instrument": instrument,
                "timeframe": timeframe,
                "venue": gathered["market"].get("venue", "unknown"),
                "session": gathered["session"].get("session", "unknown"),
                "quality_status": quality_status,
                **{f"indicator:{name}": version for name, version in versions.items()},
            },
            "untrusted_evidence": {
                **{f"market:{k}": v for k, v in gathered["market"].items()},
                **{f"quality:{k}": v for k, v in gathered["quality"].items()},
                **{f"session:{k}": v for k, v in gathered["session"].items()},
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The analyst declined to interpret the supplied evidence.",
            now,
            attempted,
            outcome,
        )

    pack = build_technical_evidence_pack(
        {
            "pack_id": derive_stable_id("id", f"tech-pack:{task.task_id}"),
            "task_id": task.task_id,
            # Every binding below is deterministic evidence, never model output.
            "instrument": instrument,
            "venue": gathered["market"].get("venue", "unknown"),
            "timeframe": timeframe,
            "session": gathered["session"].get("session", "unknown"),
            "observation_start": parse_utc_timestamp(
                gathered["market"]["window_start"],
            ),
            "observation_end": parse_utc_timestamp(gathered["market"]["window_end"]),
            "indicator_versions": dict(versions),
            "data_quality_status": quality_status,
            "data_quality_ref": gathered["quality"].get("report_ref", "unknown"),
            "market_evidence_ref": gathered["market"].get("dataset_ref", "unknown"),
            # Only the interpretation itself comes from the model.
            "claims": _section(outcome.output, "claim:"),
            "confirmations": _section(outcome.output, "confirmation:"),
            "invalidations": _section(outcome.output, "invalidation:"),
            "leakage_notes": _section(outcome.output, "leakage:"),
            "uncertainty": outcome.output.get(
                "uncertainty",
                "The analyst reported no explicit uncertainty basis.",
            ),
            "conflicts": _lines(outcome.output.get("conflicts")),
        },
    )
    logger.info(
        "Technical analyst produced %d bound claims for task %s",
        len(pack.claims),
        task.task_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"tech:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": pack,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, attempted),
        },
    )


def _section(output: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Extract one claim-keyed section from structured model output.

    Args:
        output: Structured model output.
        prefix: Section key prefix identifying the statement kind.

    Returns:
        Claim identifier to statement for that section.
    """
    return {
        key.removeprefix(prefix): value
        for key, value in output.items()
        if key.startswith(prefix)
    }


def _lines(value: str | None) -> tuple[str, ...]:
    """Split one newline-delimited output field into bounded statements.

    Args:
        value: Candidate newline-delimited field.

    Returns:
        Ordered non-empty statements.
    """
    if not value:
        return ()
    return tuple(line.strip() for line in value.split("\n") if line.strip())
