"""Composition of Research workbench execution behind the API boundary.

The gateway owns none of the science. It resolves the three things Research
deliberately does not own — which canonical dataset a browser request means,
which artifact root and resource ceilings apply, and which runtime context a
background run must re-enter — then delegates once to the registered Research
public workflow and retains the report Research authored.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from app.services.api.workstation.research import presets
from app.services.api.workstation.research.projections import (
    project_report,
    project_warnings,
)
from app.services.api.workstation.research.registry import (
    ResearchRun,
    ResearchWorkbenchRegistry,
)
from app.utils import generate_id, get_logger

if TYPE_CHECKING:
    from app.services.api.workstation.research.schemas import (
        ResearchExpectancyCreateRequest,
        ResearchRunCreateRequest,
    )

logger = get_logger(__name__)

type JsonValue = Any
type AuthContext = Any


@dataclass(slots=True)
class _ResearchRunStore:
    """Research package-root functions injected as one durable store."""

    persist_research_experiment: Callable[..., None]
    load_research_experiments: Callable[..., Sequence[Mapping[str, JsonValue]]]
    persist_research_run: Callable[..., None]
    load_research_runs: Callable[..., Sequence[Mapping[str, JsonValue]]]
    persist_research_run_batch: Callable[..., None]
    load_research_run_batches: Callable[..., Sequence[Mapping[str, JsonValue]]]


@dataclass(frozen=True, slots=True)
class ArtifactAuth:
    """Minimal audit identity a background artifact write requires.

    The request-scoped authentication context does not outlive its request, so
    a run captures exactly the three identifiers Research needs for its audit
    event and nothing else.
    """

    principal_id: str
    request_id: str
    correlation_id: str | None


def capture_artifact_auth(auth: AuthContext) -> ArtifactAuth:
    """Capture the audit identity one background run may persist under.

    Args:
        auth: Request-scoped authenticated principal.

    Returns:
        Detached audit identity safe to retain for the life of a run.
    """
    return ArtifactAuth(
        principal_id=str(auth.principal_id),
        request_id=str(getattr(auth, "request_id", generate_id("req"))),
        correlation_id=getattr(auth, "correlation_id", None),
    )


def build_research_runtime_context(
    state_provider: Callable[[], object],
) -> Callable[[], AbstractContextManager[Any]]:
    """Build a factory re-entering composition-root Data settings on a thread.

    Args:
        state_provider: Late-bound accessor for FastAPI application state. The
            graph is composed before the application object exists, so state is
            resolved when a run actually starts.

    Returns:
        Callable producing the Data runtime context for one background run.
    """

    def factory() -> AbstractContextManager[Any]:
        """Enter the composed Data settings, or nothing when uncomposed.

        Returns:
            Context manager covering one background run.
        """
        from app.services.data import (
            data_provider_connection_resolver_context,
            data_provider_settings_context,
            data_settings_context,
        )

        app_state = state_provider()
        stack = ExitStack()
        settings = getattr(app_state, "api_data_settings", None)
        provider_settings = getattr(app_state, "api_data_provider_settings", None)
        resolver = getattr(app_state, "api_data_provider_connection_resolver", None)
        if settings is not None:
            stack.enter_context(data_settings_context(settings))
        if provider_settings is not None:
            stack.enter_context(data_provider_settings_context(provider_settings))
        if resolver is not None:
            stack.enter_context(data_provider_connection_resolver_context(resolver))
        return stack

    return factory


def _resolve_dataset(
    *,
    symbol: str,
    timeframe: str,
    source_id: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int,
    use_cache: bool,
    request_id: str,
) -> object:
    """Resolve one canonical Data-owned dataset for a browser request.

    Args:
        symbol: Instrument the run analyzes.
        timeframe: Canonical timeframe key.
        source_id: Optional explicit Data provider.
        start: Optional inclusive window start.
        end: Optional inclusive window end.
        limit: Bounded bar count.
        use_cache: Whether Data may serve a cached window.
        request_id: Canonical request identifier.

    Returns:
        Data-owned ``MarketDataset``.

    Raises:
        RuntimeError: If Data reports no dataset for the request.
    """
    from app.services.api.workstation.markets import resolve_runtime_source_id
    from app.services.data import build_market_data_request, get_market_data

    resolved_source = resolve_runtime_source_id(source_id, request_id=request_id)
    response = get_market_data(
        cast(
            "Any",
            build_market_data_request(
                source_id=resolved_source,
                symbol=symbol,
                data_kind="bars",
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                use_cache=use_cache,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            ),
        )
    )
    dataset = getattr(response, "data", None)
    if getattr(response, "status", None) != "success" or dataset is None:
        error = getattr(response, "error", None)
        detail = str(getattr(error, "code", "DATASET_UNAVAILABLE"))
        message = f"RESEARCH_DATASET_UNAVAILABLE:{detail}"
        raise RuntimeError(message)
    return dataset


def _dataset_identity(dataset: object) -> Mapping[str, JsonValue]:
    """Project the Data-owned dataset identity a workbench displays.

    Args:
        dataset: Canonical ``MarketDataset``.

    Returns:
        JSON-safe dataset identity, quality decision, and provenance.
    """
    quality = getattr(dataset, "quality_report", None)
    start = getattr(dataset, "start", None)
    end = getattr(dataset, "end", None)
    available_at = getattr(dataset, "available_at", None)
    return {
        "symbol": str(getattr(dataset, "symbol", "")),
        "timeframe": getattr(dataset, "timeframe", None),
        "data_kind": str(getattr(dataset, "data_kind", "bars")),
        "record_count": int(getattr(dataset, "record_count", 0)),
        "start": start.isoformat() if start is not None else None,
        "end": end.isoformat() if end is not None else None,
        "available_at": (
            available_at.isoformat() if available_at is not None else None
        ),
        "normalization_version": str(getattr(dataset, "normalization_version", "")),
        "cache_status": str(getattr(dataset, "cache_status", "not_used")),
        "precision_policy": str(getattr(dataset, "precision_policy", "")),
        "source_metadata": {
            str(key): str(value)
            for key, value in dict(getattr(dataset, "source_metadata", {})).items()
        },
        "license_metadata": {
            str(key): str(value)
            for key, value in dict(getattr(dataset, "license_metadata", {})).items()
        },
        "quality": (
            {
                "status": str(getattr(quality, "quality_status", "")),
                "decision": str(getattr(quality, "quality_decision", "")),
                "score": str(getattr(quality, "quality_score", "")),
                "record_count": int(getattr(quality, "record_count", 0)),
                "checked_count": int(getattr(quality, "checked_count", 0)),
                "truncated": bool(getattr(quality, "truncated", False)),
            }
            if quality is not None
            else None
        ),
    }


def _bar_preview(dataset: object, *, limit: int = 500) -> list[Mapping[str, JsonValue]]:
    """Project a bounded OHLC preview for the workbench chart.

    Args:
        dataset: Canonical ``MarketDataset``.
        limit: Maximum most-recent records returned.

    Returns:
        Bounded ordered OHLC rows.
    """
    records = tuple(getattr(dataset, "records", ()))[-limit:]
    return [
        {
            "timestamp": record.timestamp.isoformat(),
            "open": str(record.open),
            "high": str(record.high),
            "low": str(record.low),
            "close": str(record.close),
            "volume": str(getattr(record, "volume", "0")),
            "spread": (
                str(record.spread)
                if getattr(record, "spread", None) is not None
                else None
            ),
        }
        for record in records
    ]


def _persist_artifacts(
    report: object,
    *,
    config: object,
    auth: ArtifactAuth,
    run_id: str,
) -> tuple[list[Mapping[str, JsonValue]], list[Mapping[str, JsonValue]]]:
    """Persist the JSON and Markdown report artifacts for one run.

    Args:
        report: Registered ``ResearchReport``.
        config: Resolved Research configuration.
        auth: Captured audit identity.
        run_id: Owning run identity.

    Returns:
        Artifact references and any warnings raised while persisting.
    """
    from pathlib import Path

    from app.services.research import (
        create_research_value,
        render_research_report,
        write_research_artifact,
    )

    typed_config = cast("Any", config)
    artifacts: list[Mapping[str, JsonValue]] = []
    warnings: list[Mapping[str, JsonValue]] = []
    for artifact_format in ("json", "markdown"):
        suffix = "json" if artifact_format == "json" else "md"
        destination = typed_config.artifacts.allowed_root / run_id / f"report.{suffix}"
        write_config = create_research_value(
            "ArtifactWriteConfig",
            allowed_root=Path(typed_config.artifacts.allowed_root),
            format=artifact_format,
            overwrite=True,
        )
        payload = (
            report
            if artifact_format == "json"
            else render_research_report(cast("Any", report), format="markdown")
        )
        try:
            reference = write_research_artifact(
                cast("Any", payload),
                destination,
                config=cast("Any", write_config),
                auth=cast("Any", auth),
                limits=typed_config.limits,
            )
        except Exception as error:  # noqa: BLE001 - artifact failure is advisory.
            logger.warning("Research artifact write failed: %s", type(error).__name__)
            warnings.append(
                {
                    "code": "ARTIFACT_WRITE_FAILED",
                    "message": str(error)[:200],
                    "severity": "warning",
                    "field_path": f"artifacts.{artifact_format}",
                    "details": {"format": artifact_format},
                }
            )
            continue
        artifacts.append(
            {
                "artifact_id": f"{run_id}:{artifact_format}",
                "kind": "report",
                "format": reference.format,
                "relative_path": reference.relative_path.as_posix(),
                "size_bytes": reference.size_bytes,
                "sha256": reference.sha256,
                "atomic": reference.atomic,
                "schema_version": reference.schema_version,
                "audit_event_id": reference.audit_event_id,
            }
        )
    return artifacts, warnings


def build_research_executor(
    *,
    artifact_root_override: object | None = None,
) -> Callable[[ResearchRun, Callable[..., None]], Mapping[str, JsonValue]]:
    """Build the callable one background Research run executes.

    Args:
        artifact_root_override: Optional gateway-owned artifact root used by
            tests. Never caller-supplied.

    Returns:
        Executor receiving one run record and a progress emitter.
    """

    def execute(run: ResearchRun, emit: Callable[..., None]) -> Mapping[str, JsonValue]:
        """Resolve the dataset, delegate to Research, and retain the report.

        Args:
            run: Queued run record carrying its safe request material.
            emit: Ordered progress emitter.

        Returns:
            Result material retained on the run record.

        Raises:
            RuntimeError: If Data cannot supply the requested dataset.
        """
        from app.services.research import run_edge_lab_profile

        material = dict(run.request_material)
        selection = cast("Mapping[str, JsonValue]", material["dataset"])
        request = cast("ResearchRunCreateRequest", material["request"])
        auth = cast("ArtifactAuth", material["auth"])
        request_id = generate_id("req")

        emit("data", "Resolving canonical dataset", symbol=run.symbol)
        dataset = _resolve_dataset(
            symbol=run.symbol,
            timeframe=run.timeframe,
            source_id=cast("str | None", selection.get("source_id")),
            start=cast("datetime | None", selection.get("start")),
            end=cast("datetime | None", selection.get("end")),
            limit=int(cast("int", selection.get("bar_limit", 5_000))),
            use_cache=not run.force_rerun,
            request_id=request_id,
        )
        identity = _dataset_identity(dataset)
        emit(
            "data",
            "Dataset resolved",
            record_count=identity["record_count"],
        )

        config = presets.build_preset_config(
            request,
            symbol=str(identity["symbol"]) or run.symbol,
            selected_stages=run.selected_stages,
            artifact_root=cast("Any", artifact_root_override),
        )
        effective = presets.describe_effective_configuration(config)

        for stage in run.selected_stages:
            emit(stage, f"Stage queued: {stage}")
        emit("research", "Delegating to Research", stages=list(run.selected_stages))

        response = run_edge_lab_profile(
            cast("Any", dataset),
            hypothesis=run.hypothesis,
            config=config,
        )
        if getattr(response, "status", None) != "success" or response.data is None:
            error = getattr(response, "error", None)
            emit("research", "Research reported a failure")
            return {
                "dataset": {
                    "identity": identity,
                    "preview": _bar_preview(dataset),
                },
                "effective_configuration": effective,
                "error": {
                    "code": str(getattr(error, "code", "RESEARCH_RUN_FAILED")),
                    "message": str(getattr(error, "message", "Research run failed")),
                    "details": dict(getattr(error, "details", {}) or {}),
                },
                "artifacts": [],
            }

        report = response.data
        emit("research", "Research report produced", report_id=report.report_id)

        artifacts: list[Mapping[str, JsonValue]] = []
        artifact_warnings: list[Mapping[str, JsonValue]] = []
        if bool(material.get("save_artifacts", True)):
            emit("artifacts", "Persisting report artifacts")
            artifacts, artifact_warnings = _persist_artifacts(
                report, config=config, auth=auth, run_id=run.run_id
            )
        return {
            "report": report,
            "dataset": {
                "identity": identity,
                "preview": _bar_preview(dataset),
            },
            "effective_configuration": effective,
            "artifacts": artifacts,
            "artifact_warnings": artifact_warnings,
        }

    return execute


def build_research_registry(
    runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
) -> ResearchWorkbenchRegistry:
    """Build the gateway-composed Research workbench registry.

    Args:
        runtime_context: Factory for the Data runtime context a background run
            must re-enter.

    Returns:
        Composed workbench registry.
    """
    from app.services.research import (
        load_research_experiments,
        load_research_run_batches,
        load_research_runs,
        persist_research_experiment,
        persist_research_run,
        persist_research_run_batch,
    )

    store = _ResearchRunStore(
        persist_research_experiment=persist_research_experiment,
        load_research_experiments=load_research_experiments,
        persist_research_run=persist_research_run,
        load_research_runs=load_research_runs,
        persist_research_run_batch=persist_research_run_batch,
        load_research_run_batches=load_research_run_batches,
    )
    return ResearchWorkbenchRegistry(
        executor=build_research_executor(),
        runtime_context=runtime_context,
        store=store,
    )


def _expectancy_view(
    profile_id: str | None, strategy_ref: str | None
) -> Mapping[str, JsonValue]:
    """Read the approved expectancy profile Research governs.

    Args:
        profile_id: Optional explicit governance identity.
        strategy_ref: Optional strategy identity covered by a profile.

    Returns:
        Expectancy evidence, or an explicit unavailable state with a reason.
    """
    from app.services.research import (
        load_eligible_expectancy_profile,
        load_expectancy_profile,
    )

    request_id = generate_id("req")
    if profile_id is None and strategy_ref is None:
        return {
            "available": False,
            "reason": "PROFILE_NOT_SELECTED",
            "profile": None,
        }
    try:
        profile = (
            load_expectancy_profile(profile_id=profile_id, request_id=request_id)
            if profile_id is not None
            else load_eligible_expectancy_profile(
                strategy_ref=cast("str", strategy_ref), request_id=request_id
            )
        )
    except Exception as error:  # noqa: BLE001 - read boundary stays explicit.
        logger.warning("Expectancy read failed: %s", type(error).__name__)
        return {
            "available": False,
            "reason": "EXPECTANCY_STORE_UNAVAILABLE",
            "profile": None,
        }
    if profile is None:
        return {"available": False, "reason": "NO_PROFILE_RECORDED", "profile": None}
    return {"available": True, "reason": None, "profile": dict(profile)}


def _drift_view(profile_id: str | None) -> Mapping[str, JsonValue]:
    """Read the latest performance-drift evidence Research recorded.

    Args:
        profile_id: Optional expectancy profile identity.

    Returns:
        Drift evidence, or an explicit unavailable state with a reason.
    """
    from app.services.research import load_latest_performance_drift_evidence

    if profile_id is None:
        return {"available": False, "reason": "PROFILE_NOT_SELECTED", "evidence": None}
    try:
        evidence = load_latest_performance_drift_evidence(
            profile_id=profile_id, request_id=generate_id("req")
        )
    except Exception as error:  # noqa: BLE001 - read boundary stays explicit.
        logger.warning("Drift read failed: %s", type(error).__name__)
        return {
            "available": False,
            "reason": "DRIFT_STORE_UNAVAILABLE",
            "evidence": None,
        }
    if evidence is None:
        return {"available": False, "reason": "NO_EVIDENCE_RECORDED", "evidence": None}
    return {"available": True, "reason": None, "evidence": dict(evidence)}


def _stress_view(scenario_id: str | None) -> Mapping[str, JsonValue]:
    """Read the latest stress-scenario evidence Research recorded.

    Args:
        scenario_id: Optional stress scenario identity.

    Returns:
        Stress evidence, or an explicit unavailable state with a reason.
    """
    from app.services.research import load_latest_stress_scenario_evidence

    if scenario_id is None:
        return {
            "available": False,
            "reason": "SCENARIO_NOT_SELECTED",
            "evidence": None,
        }
    try:
        evidence = load_latest_stress_scenario_evidence(
            scenario_id=scenario_id, request_id=generate_id("req")
        )
    except Exception as error:  # noqa: BLE001 - read boundary stays explicit.
        logger.warning("Stress read failed: %s", type(error).__name__)
        return {
            "available": False,
            "reason": "STRESS_STORE_UNAVAILABLE",
            "evidence": None,
        }
    if evidence is None:
        return {"available": False, "reason": "NO_EVIDENCE_RECORDED", "evidence": None}
    return {"available": True, "reason": None, "evidence": dict(evidence)}


def _parse_decision_time(value: str) -> datetime | None:
    """Parse an aware ISO decision instant and normalize it to UTC.

    Args:
        value: Candidate ISO 8601 timestamp.

    Returns:
        Aware UTC timestamp, or ``None`` when the value is invalid or naive.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except TypeError, ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _intelligence_failure_reason(error: Exception, coverage_reason: str) -> str:
    """Classify an expected coverage gap separately from a source failure.

    Args:
        error: Exception raised by the owner-domain evidence workflow.
        coverage_reason: Closed reason emitted for insufficient eligible records.

    Returns:
        Bounded gateway reason code.
    """
    return (
        coverage_reason
        if coverage_reason in str(error)
        else "INTELLIGENCE_SOURCE_UNAVAILABLE"
    )


def _intelligence_view(  # noqa: C901, PLR0912, PLR0915
    asset_class: str | None,
    symbol: str | None,
    available_at: str | None,
) -> Mapping[str, JsonValue]:
    """Build point-in-time Research intelligence for one instrument.

    Applicability is a deterministic Research decision. When the caller has not
    declared an asset class the gateway reports that explicitly instead of
    guessing one from a symbol string.

    Args:
        asset_class: Optional declared instrument asset class.
        symbol: Canonical dataset symbol used as the source asset scope.
        available_at: Persisted dataset decision instant in ISO 8601 form.

    Returns:
        Applicability evidence per model, or an explicit unavailable state.
    """
    from app.services.data import build_research_source_query
    from app.services.research import (
        assess_intelligence_applicability,
        build_fundamental_source_evidence,
        build_sentiment_source_evidence,
        project_intelligence_evidence,
    )

    if not asset_class:
        return {
            "available": False,
            "reason": "ASSET_CLASS_NOT_DECLARED",
            "applicability": [],
            "fundamental": {},
            "sentiment": {},
        }
    applicability: list[Mapping[str, JsonValue]] = []
    applicability_by_model: dict[str, str] = {}
    for model in ("issuer", "macro", "sentiment"):
        try:
            result = assess_intelligence_applicability(asset_class, model=model)
        except Exception as error:  # noqa: BLE001 - read boundary stays explicit.
            logger.warning("Applicability read failed: %s", type(error).__name__)
            continue
        status = str(getattr(result, "status", "unknown"))
        reasons = tuple(getattr(result, "reasons", ()))
        applicability_by_model[model] = status
        applicability.append(
            {
                "model": model,
                "status": status,
                "asset_class": str(getattr(result, "asset_class", asset_class)),
                "reason": reasons[0] if reasons else None,
            }
        )

    base: dict[str, JsonValue] = {
        "available": False,
        "reason": None,
        "applicability": applicability,
        "fundamental": {},
        "sentiment": {},
        "fundamental_reason": None,
        "sentiment_reason": None,
    }
    if not symbol:
        base["reason"] = "DATASET_SYMBOL_MISSING"
        return base
    if not available_at:
        base["reason"] = "DECISION_TIME_MISSING"
        return base
    decision_time = _parse_decision_time(available_at)
    if decision_time is None:
        base["reason"] = "DECISION_TIME_INVALID"
        return base

    fundamental_model: str | None = None
    fundamental_kinds: tuple[str, ...] = ()
    required_kinds: tuple[str, ...] = ()
    if applicability_by_model.get("macro") == "applicable":
        fundamental_model = "macro"
        fundamental_kinds = ("macro",)
        required_kinds = ("macro",)
    elif applicability_by_model.get("issuer") == "applicable":
        fundamental_model = "issuer"
        fundamental_kinds = ("filing", "statement", "transcript")
    else:
        base["fundamental_reason"] = "FUNDAMENTAL_MODEL_NOT_APPLICABLE"

    if fundamental_model is not None:
        try:
            query = build_research_source_query(
                decision_time=decision_time,
                source_kinds=fundamental_kinds,
                asset_scope=(symbol,),
            )
            fundamental = build_fundamental_source_evidence(
                query,
                asset_class=asset_class,
                model=fundamental_model,
                required_kinds=required_kinds,
            )
            base["fundamental"] = dict(project_intelligence_evidence(fundamental))
        except Exception as error:  # noqa: BLE001 - evidence gap is explicit.
            logger.warning(
                "Fundamental intelligence unavailable: %s", type(error).__name__
            )
            base["fundamental_reason"] = _intelligence_failure_reason(
                error, "FUNDAMENTAL_COVERAGE_MISSING"
            )

    try:
        query = build_research_source_query(
            decision_time=decision_time,
            source_kinds=("news", "social", "alternative", "macro"),
            asset_scope=(symbol,),
        )
        sentiment = build_sentiment_source_evidence(
            query,
            measurement_version="lexicon-v1",
        )
        base["sentiment"] = dict(project_intelligence_evidence(sentiment))
    except Exception as error:  # noqa: BLE001 - evidence gap is explicit.
        logger.warning("Sentiment intelligence unavailable: %s", type(error).__name__)
        base["sentiment_reason"] = _intelligence_failure_reason(
            error, "SENTIMENT_COVERAGE_MISSING"
        )

    base["available"] = bool(base["fundamental"] or base["sentiment"])
    if not base["available"]:
        base["reason"] = "INTELLIGENCE_COVERAGE_MISSING"
    return base


def _transition_expectancy(
    *,
    profile_id: str,
    target_state: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_by: str | None,
    request_id: str,
) -> Mapping[str, JsonValue]:
    """Validate and persist one Research-owned expectancy transition.

    Args:
        profile_id: Stable expectancy profile identity.
        target_state: Requested lifecycle successor.
        reviewer: Authenticated reviewer identity.
        decision: Recorded governance decision.
        reason: Recorded governance rationale.
        superseded_by: Optional successor profile identity.
        request_id: Request trace identity.

    Returns:
        Refreshed Research-owned expectancy view.

    Raises:
        ValueError: If the profile is missing or the transition is invalid.
    """
    from app.services.research import (
        apply_expectancy_transition,
        is_governance_transition_permitted,
        load_expectancy_profile,
        transition_expectancy_governance,
    )

    profile = load_expectancy_profile(profile_id=profile_id, request_id=request_id)
    if profile is None:
        raise ValueError("EXPECTANCY_PROFILE_NOT_FOUND")
    source_state = str(profile["governance_state"])
    if not is_governance_transition_permitted(
        cast("Any", source_state), cast("Any", target_state)
    ):
        raise ValueError("EXPECTANCY_TRANSITION_NOT_PERMITTED")
    transition_expectancy_governance(
        profile,
        target_state=cast("Any", target_state),
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        now_utc=datetime.now(UTC),
        superseded_by=superseded_by,
    )
    apply_expectancy_transition(
        profile_id=profile_id,
        source_state=source_state,
        governance_state=target_state,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        superseded_by=superseded_by or "",
        request_id=request_id,
    )
    refreshed = load_expectancy_profile(profile_id=profile_id, request_id=request_id)
    if refreshed is None:
        raise ValueError("EXPECTANCY_PROFILE_NOT_FOUND")
    return {"available": True, "reason": None, "profile": refreshed}


def _build_expectancy_profile(
    *,
    registry: ResearchWorkbenchRegistry,
    principal_id: str,
    request: ResearchExpectancyCreateRequest,
    reviewer: str,
    request_id: str,
    persist: bool,
) -> Mapping[str, JsonValue]:
    """Build and optionally persist one draft profile bound to a completed run.

    Args:
        registry: Composed Research run registry.
        principal_id: Authenticated owner identity.
        request: Validated operator-supplied measurements.
        reviewer: Principal recorded on persistence.
        request_id: Request trace identity.
        persist: Whether to perform the owner persistence effect.

    Returns:
        Draft Research expectancy profile.

    Raises:
        ValueError: If the run is absent or not completed with a report.
    """
    from app.services.research import (
        build_expectancy_profile,
        persist_expectancy_profile,
    )

    run = registry.get_run(request.run_id, principal_id=principal_id)
    if run is None:
        raise ValueError("RESEARCH_RUN_NOT_FOUND")
    if run.status != "completed" or run.report is None:
        raise ValueError("EXPECTANCY_RUN_NOT_COMPLETED")
    report = project_report(run.report)
    report_id = str(report.get("report_id", ""))
    dataset_hash = str(report.get("dataset_hash", ""))
    if not report_id or not dataset_hash:
        raise ValueError("EXPECTANCY_RUN_EVIDENCE_INCOMPLETE")
    profile = build_expectancy_profile(
        exact_version=request.exact_version,
        hypothesis=run.hypothesis,
        strategy_ref=request.strategy_ref,
        instruments=(run.symbol,),
        regimes=request.regimes,
        sessions=request.sessions,
        sample_from_utc=request.sample_from_utc,
        sample_to_utc=request.sample_to_utc,
        sample_size=request.sample_size,
        out_of_sample_status=request.out_of_sample_status,
        win_rate=request.win_rate,
        avg_win_r=request.avg_win_r,
        avg_loss_r=request.avg_loss_r,
        expected_value_r=request.expected_value_r,
        max_drawdown_r=request.max_drawdown_r,
        min_reward_risk=request.min_reward_risk,
        evidence_ref=f"research-run:{run.run_id}:{report_id}:{dataset_hash}",
        next_review_at_utc=request.next_review_at_utc,
        expires_at_utc=request.expires_at_utc,
    )
    if persist:
        persist_expectancy_profile(
            profile,
            reviewer=reviewer,
            decision="draft_created",
            reason="COMPLETED_RESEARCH_RUN_EVIDENCE",
            request_id=request_id,
        )
    return {"available": True, "reason": None, "profile": profile}


def _build_stress_scenario(
    *,
    scenario_key: str,
    hypothesis: str,
    request_id: str,
    persist: bool,
) -> Mapping[str, JsonValue]:
    """Build and optionally persist one approved reasoned stress scenario.

    Args:
        scenario_key: Approved Research-owned catalogue key.
        hypothesis: Explicit stress objective.
        request_id: Request trace identity.
        persist: Whether to perform the owner persistence effect.

    Returns:
        Built Research stress evidence.
    """
    from app.services.research import (
        build_registered_stress_scenario,
        persist_stress_scenario_evidence,
    )

    evidence = build_registered_stress_scenario(
        scenario_key=scenario_key,
        hypothesis=hypothesis,
        generated_at_utc=datetime.now(UTC),
    )
    if persist:
        persist_stress_scenario_evidence(evidence, request_id=request_id)
    return {"available": True, "reason": None, "evidence": evidence}


def build_research_source(  # noqa: C901
    registry: ResearchWorkbenchRegistry | None,
) -> Callable[..., object]:
    """Build the dispatcher covering every Research workbench operation.

    Args:
        registry: Composed workbench registry, or ``None`` to fail closed.

    Returns:
        Callable dispatching one allowlisted registry or read operation.
    """

    def dispatch(operation: str, **kwargs: object) -> object:  # noqa: C901, PLR0911
        """Execute one Research workbench operation.

        Args:
            operation: Allowlisted operation name.
            **kwargs: Operation-specific keyword arguments.

        Returns:
            Registry or read-model result.

        Raises:
            RuntimeError: If the registry is not composed.
            ValueError: If the operation is unsupported.
        """
        if operation == "presets":
            return presets.list_research_presets()
        if operation == "expectancy":
            return _expectancy_view(
                cast("str | None", kwargs.get("profile_id")),
                cast("str | None", kwargs.get("strategy_ref")),
            )
        if operation == "transition_expectancy":
            return _transition_expectancy(
                profile_id=str(kwargs["profile_id"]),
                target_state=str(kwargs["target_state"]),
                reviewer=str(kwargs["reviewer"]),
                decision=str(kwargs["decision"]),
                reason=str(kwargs["reason"]),
                superseded_by=cast("str | None", kwargs.get("superseded_by")),
                request_id=str(kwargs["request_id"]),
            )
        if operation == "build_expectancy":
            if registry is None:
                raise RuntimeError("RESEARCH_RUNTIME_UNAVAILABLE")
            return _build_expectancy_profile(
                registry=registry,
                principal_id=str(kwargs["principal_id"]),
                request=cast("ResearchExpectancyCreateRequest", kwargs["request"]),
                reviewer=str(kwargs["reviewer"]),
                request_id=str(kwargs["request_id"]),
                persist=bool(kwargs["persist"]),
            )
        if operation == "drift":
            return _drift_view(cast("str | None", kwargs.get("profile_id")))
        if operation == "stress":
            return _stress_view(cast("str | None", kwargs.get("scenario_id")))
        if operation == "build_stress":
            return _build_stress_scenario(
                scenario_key=str(kwargs["scenario_key"]),
                hypothesis=str(kwargs["hypothesis"]),
                request_id=str(kwargs["request_id"]),
                persist=bool(kwargs["persist"]),
            )
        if operation == "intelligence":
            return _intelligence_view(
                cast("str | None", kwargs.get("asset_class")),
                cast("str | None", kwargs.get("symbol")),
                cast("str | None", kwargs.get("available_at")),
            )
        if registry is None:
            raise RuntimeError("RESEARCH_RUNTIME_UNAVAILABLE")
        if operation == "registry":
            return registry
        raise ValueError("unsupported Research workbench operation")

    return dispatch


def project_run_artifacts(run: ResearchRun) -> Sequence[Mapping[str, JsonValue]]:
    """Return the artifact references retained for one run.

    Args:
        run: Run record.

    Returns:
        Artifact references, empty when nothing was persisted.
    """
    return tuple(run.artifacts)


def project_diagnostic_report(run: ResearchRun) -> Mapping[str, JsonValue] | None:
    """Return the registered report for the secondary diagnostic viewer.

    Args:
        run: Run record.

    Returns:
        JSON-safe report, or ``None`` when the run produced none.
    """
    if run.report is None:
        return None
    return project_report(run.report)


def project_artifact_warnings(run: ResearchRun) -> Sequence[Mapping[str, JsonValue]]:
    """Return warnings raised while persisting a run's artifacts.

    Args:
        run: Run record.

    Returns:
        Bounded artifact warnings.
    """
    material = run.request_material.get("artifact_warnings")
    if isinstance(material, Sequence):
        return project_warnings(cast("Sequence[object]", material))
    return ()


__all__ = (
    "ArtifactAuth",
    "build_research_executor",
    "build_research_registry",
    "build_research_runtime_context",
    "build_research_source",
    "capture_artifact_auth",
    "project_artifact_warnings",
    "project_diagnostic_report",
    "project_run_artifacts",
)
