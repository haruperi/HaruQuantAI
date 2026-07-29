"""Provider-neutral Quantitative Analyst agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`,
grounds every estimator in the Analytics metric catalog through governed tool
calls, and delegates interpretation to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. Estimator
definitions and sample floors are taken from the deterministic catalog, never
from model output (`FR-AGENTIC-034`). The disclosure fields — sample,
multiple-testing exposure, dataset and configuration hashes — come from the
supplied evidence and the caller (`FR-AGENTIC-035`). And four ineligibility
conditions refuse **before** the model is reached, so there is no opportunity
to impute a value (`FR-AGENTIC-036`).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.market_analysis.quantitative_analyst.schemas import (
    QuantitativeEvidencePack,
    build_quantitative_evidence_pack,
)
from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
    METRIC_CATALOG_TOOL,
    SAMPLE_FLOOR_TOOL,
    call_calculation_tool,
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
    from datetime import datetime

    from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
        QuantitativeEvidencePort,
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

ROLE_ID = "quantitative_analyst"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_NODE_ID = "analyze_quantitative_evidence"

# Leakage severities that make every downstream number untrustworthy.
_BLOCKING_LEAKAGE = frozenset({"high", "critical"})


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
    """Build the reproducible lineage for one quantitative reading.

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
    """Build the bounded consumption record for one quantitative reading.

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
) -> AgentResult[QuantitativeEvidencePack]:
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
        "Quantitative analyst refusing task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"quant:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


def _has_non_finite(statistics: Mapping[str, float]) -> bool:
    """Report whether any supplied statistic is non-finite.

    A `NaN` or infinite statistic is a result about the computation, never a
    gap for the model to fill.

    Args:
        statistics: Supplied numeric statistics.

    Returns:
        True when any value is not finite.
    """
    return any(not isfinite(value) for value in statistics.values())


def _alignment_failure(evidence: Mapping[str, Mapping[str, str]]) -> str | None:
    """Report whether supplied evidence disagrees on dataset or configuration.

    Args:
        evidence: Evidence reference to bounded evidence content.

    Returns:
        The disagreeing field name, or None when every source aligns.
    """
    for field in ("dataset_hash", "configuration_hash"):
        values = {source[field] for source in evidence.values() if field in source}
        if len(values) > 1:
            return field
    return None


def _ineligibility(
    evidence: Mapping[str, Mapping[str, str]],
    statistics: Mapping[str, float],
    sample_size: int,
    minimum_sample: int,
    leakage_severity: str,
) -> tuple[str, str] | None:
    """Determine whether the supplied evidence can be analysed at all.

    Each condition refuses before the model is reached, so there is no
    opportunity to impute, interpolate, or reconcile.

    Args:
        evidence: Evidence reference to bounded evidence content.
        statistics: Supplied numeric statistics.
        sample_size: Observation count backing the evidence.
        minimum_sample: Catalogued minimum for the estimator class.
        leakage_severity: Reported leakage severity.

    Returns:
        The enumerated reason and detail, or None when eligible.
    """
    if not evidence:
        return ("EVIDENCE_ABSENT", "No versioned evidence was supplied.")
    if _has_non_finite(statistics):
        return (
            "NON_FINITE_INPUT",
            "A supplied statistic is not finite and must not be imputed.",
        )
    if sample_size < minimum_sample:
        return (
            "INSUFFICIENT_SAMPLE",
            f"Sample {sample_size} is below the catalogued minimum {minimum_sample}.",
        )
    misaligned = _alignment_failure(evidence)
    if misaligned is not None:
        return (
            "EVIDENCE_NOT_ALIGNED",
            f"Supplied evidence disagrees on {misaligned} and cannot be compared.",
        )
    if leakage_severity.lower() in _BLOCKING_LEAKAGE:
        return (
            "LEAKAGE_UNSAFE",
            f"Leakage evidence reports {leakage_severity} severity.",
        )
    return None


def _definition_fetch(
    port: QuantitativeEvidencePort,
    metric: str,
) -> Callable[[], Mapping[str, object]]:
    """Bind one metric name to a zero-argument catalog lookup.

    Args:
        port: Injected receiver-domain evidence port.
        metric: Catalogued metric name.

    Returns:
        A zero-argument callable performing the lookup.
    """

    def fetch() -> Mapping[str, object]:
        """Perform the bound catalog lookup.

        Returns:
            The metric's registered definition, empty when uncatalogued.
        """
        return port.fetch_metric_definition(metric)

    return fetch


@dataclass(frozen=True, slots=True)
class _CatalogGrounding:
    """Deterministic grounding gathered before any model call.

    Attributes:
        definitions: Registered definition per catalogued metric name.
        minimum_sample: Catalogued sample floor for the estimator class.
        tool_calls: Governed tool calls attempted.
        failure: Enumerated reason and detail when grounding failed.
    """

    definitions: Mapping[str, Mapping[str, str]]
    minimum_sample: int
    tool_calls: int
    failure: tuple[str, str] | None


def _ground_estimators(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: QuantitativeEvidencePort,
    principal_id: str,
    task_id: str,
    scope: Mapping[str, str],
    metrics: tuple[str, ...],
    evidence_class: str,
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> _CatalogGrounding:
    """Fetch estimator definitions and the sample floor through governed tools.

    Both come from the deterministic Analytics catalog, never from the model
    (`FR-AGENTIC-034`).

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected receiver-domain evidence port.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        scope: Scope declared for the tool calls.
        metrics: Catalogued metric names under analysis.
        evidence_class: Minimum-sample class for the estimators used.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.

    Returns:
        The gathered grounding, carrying a failure when it could not be
        completed.
    """
    attempted = 0
    definitions: dict[str, Mapping[str, str]] = {}
    catalog_tool = tool_policies.get(METRIC_CATALOG_TOOL)
    floor_tool = tool_policies.get(SAMPLE_FLOOR_TOOL)
    if catalog_tool is None or floor_tool is None:
        return _CatalogGrounding(
            definitions,
            0,
            attempted,
            ("EVIDENCE_TOOL_DENIED", "A required catalog tool is not registered."),
        )

    for metric in metrics:
        attempted += 1
        result = call_calculation_tool(
            mandate,
            policy,
            catalog_tool,
            principal_id,
            task_id,
            scope,
            _definition_fetch(port, metric),
            at_time,
            nonce_store=nonce_store,
            audit_store=audit_store,
            calls_used=attempted - 1,
        )
        if not result.allowed or result.payload is None:
            return _CatalogGrounding(
                definitions,
                0,
                attempted,
                (
                    "EVIDENCE_TOOL_DENIED",
                    f"A governed tool was denied: {result.denial_reason}.",
                ),
            )
        if not result.payload:
            return _CatalogGrounding(
                definitions,
                0,
                attempted,
                (
                    "ESTIMATOR_NOT_CATALOGUED",
                    f"Metric {metric} has no registered definition.",
                ),
            )
        definitions[metric] = result.payload

    attempted += 1
    floors = call_calculation_tool(
        mandate,
        policy,
        floor_tool,
        principal_id,
        task_id,
        scope,
        port.fetch_minimum_samples,
        at_time,
        nonce_store=nonce_store,
        audit_store=audit_store,
        calls_used=attempted - 1,
    )
    if not floors.allowed or floors.payload is None:
        return _CatalogGrounding(
            definitions,
            0,
            attempted,
            (
                "EVIDENCE_TOOL_DENIED",
                f"A governed tool was denied: {floors.denial_reason}.",
            ),
        )
    return _CatalogGrounding(
        definitions,
        int(floors.payload.get(evidence_class, "0")),
        attempted,
        None,
    )


def analyze_quantitative_evidence(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: QuantitativeEvidencePort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    evidence: Mapping[str, Mapping[str, str]],
    metrics: tuple[str, ...],
    statistics: Mapping[str, float],
    sample_size: int,
    multiple_testing_exposure: int,
    leakage_severity: str = "none",
    validation_status: str = "unvalidated",
    evidence_class: str = "statistical",
    principal_id: str = "agent-quantitative",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[QuantitativeEvidencePack]:
    """Analyse versioned Research and Analytics evidence.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected receiver-domain evidence port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        evidence: Evidence reference to bounded evidence content.
        metrics: Catalogued metric names under analysis.
        statistics: Supplied numeric statistics, checked for finiteness.
        sample_size: Observation count backing the evidence.
        multiple_testing_exposure: Hypotheses tested to reach this reading.
        leakage_severity: Reported leakage severity.
        validation_status: Whether a null or random-label control was run.
        evidence_class: Minimum-sample class for the estimators used.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a disclosed evidence pack, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Quantitative analyst starting for task %s", task.task_id)

    if not metrics:
        return _refuse(
            task,
            manifest,
            profile,
            ("METRICS_NOT_REQUESTED",),
            "A quantitative reading must name the catalogued metrics it uses.",
            now,
        )

    # Estimator definitions and the sample floor come from the deterministic
    # catalog, never from the model.
    grounding = _ground_estimators(
        mandate,
        policy,
        tool_policies,
        port,
        principal_id,
        task.task_id,
        scope,
        metrics,
        evidence_class,
        now,
        nonce_store,
        audit_store,
    )
    attempted = grounding.tool_calls
    definitions = grounding.definitions
    if grounding.failure is not None:
        reason, detail = grounding.failure
        return _refuse(task, manifest, profile, (reason,), detail, now, attempted)

    ineligible = _ineligibility(
        evidence,
        statistics,
        sample_size,
        grounding.minimum_sample,
        leakage_severity,
    )
    if ineligible is not None:
        reason, detail = ineligible
        return _refuse(task, manifest, profile, (reason,), detail, now, attempted)

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"quant:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # Catalogued definitions and disclosure facts are trusted context:
            # they came from deterministic sources, not from any model.
            "trusted_context": {
                "sample_size": str(sample_size),
                "multiple_testing_exposure": str(multiple_testing_exposure),
                "minimum_sample": str(grounding.minimum_sample),
                "leakage_severity": leakage_severity,
                "validation_status": validation_status,
                **{
                    f"estimator:{metric}": definition.get("formula", "unknown")
                    for metric, definition in definitions.items()
                },
            },
            "untrusted_evidence": {
                f"{ref}:{key}": value
                for ref, source in sorted(evidence.items())
                for key, value in sorted(source.items())
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

    # The analyst attributes each finding to a metric; the catalog supplies the
    # definition. An attribution the catalog does not recognize is refused,
    # never carried through as an authored estimator.
    estimators, unknown = _resolve_finding_estimators(
        _section(outcome.output, "estimator:"),
        definitions,
    )
    if unknown is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("ESTIMATOR_NOT_CATALOGUED",),
            f"A finding was attributed to uncatalogued estimator {unknown}.",
            now,
            attempted,
            outcome,
        )

    first = next(iter(sorted(evidence)))
    pack = build_quantitative_evidence_pack(
        {
            "pack_id": derive_stable_id("id", f"quant-pack:{task.task_id}"),
            "task_id": task.task_id,
            # Disclosure comes from deterministic evidence and the caller.
            "dataset_hash": evidence[first].get("dataset_hash", "unknown"),
            "configuration_hash": evidence[first].get("configuration_hash", "unknown"),
            "split_label": evidence[first].get("split", "unknown"),
            "sample_size": str(sample_size),
            "multiple_testing_exposure": str(multiple_testing_exposure),
            "estimators": estimators,
            "findings": _section(outcome.output, "finding:"),
            "uncertainty": _section(outcome.output, "uncertainty:"),
            "assumptions": _lines(outcome.output.get("assumptions")),
            "limitations": _lines(outcome.output.get("limitations")),
            "leakage_status": leakage_severity,
            "validation_status": validation_status,
            "conflicts": _lines(outcome.output.get("conflicts")),
        },
    )
    logger.info(
        "Quantitative analyst produced %d disclosed findings for task %s",
        len(pack.findings),
        task.task_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"quant:{task.task_id}:ok"),
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
    """Extract one keyed section from structured model output.

    Args:
        output: Structured model output.
        prefix: Section key prefix.

    Returns:
        Identifier to statement for that section.
    """
    return {
        key.removeprefix(prefix): value
        for key, value in output.items()
        if key.startswith(prefix)
    }


def _resolve_finding_estimators(
    attributions: Mapping[str, str],
    definitions: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, str], str | None]:
    """Replace each finding's metric attribution with its catalogued formula.

    The model states which metric a finding came from; only the catalog says
    what that metric is (`FR-AGENTIC-034`).

    Args:
        attributions: Finding identifier to model-supplied metric name.
        definitions: Registered definition per catalogued metric name.

    Returns:
        The catalogued estimator per finding, and the first unrecognized metric
        name when one was attributed.
    """
    resolved: dict[str, str] = {}
    for finding, metric in sorted(attributions.items()):
        definition = definitions.get(metric)
        if definition is None:
            return ({}, metric)
        resolved[finding] = definition.get("formula", "unknown")
    return (resolved, None)


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
