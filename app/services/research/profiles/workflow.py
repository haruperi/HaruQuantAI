"""Deterministic advisory Edge Lab profile orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter_ns
from typing import TYPE_CHECKING, Any, Literal, cast

from app.services.analytics import get_analytics_value_field
from app.services.research.contracts import (
    EdgeLabConfig,
    EdgeResult,
    LeakageReport,
    MarketStructureProfile,
    ResearchReport,
    ResearchWarning,
    UnsupervisedResearchResult,
)
from app.services.research.contracts.errors import (
    RESEARCH_ERROR_CATALOG,
    ConfigurationError,
    ResearchError,
    ValidationError,
)
from app.services.research.data import prepare_research_dataset
from app.services.research.features import build_research_feature_frame
from app.services.research.leakage import (
    enforce_time_split,
    validate_no_lookahead_features,
)
from app.services.research.market_structure import build_market_structure_profile
from app.services.research.metrics import (
    build_core_metric_profile,
    build_default_registry,
)
from app.services.research.modeling import run_unsupervised_research
from app.services.research.profiles.scorecard import build_research_scorecard
from app.services.research.profiles.snapshot import (
    build_research_profile_snapshot,
)
from app.services.research.seasonality import (
    SeasonalityFilters,
    run_seasonality,
    tag_sessions,
)
from app.services.research.statistics import block_bootstrap_ci, permutation_test
from app.services.research.studies import (
    run_eds_mean_reversion,
    run_eds_session,
    run_eds_trend_persistence,
)
from app.utils import (
    build_response_metadata,
    canonical_digest,
    error_response,
    exception_response,
    generate_id,
    get_execution_ms,
    get_logger,
    success_response,
)

type JsonValue = Any
type ResponseMetadata = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]


logger = get_logger(__name__)

if TYPE_CHECKING:
    import pandas as pd

    MarketDataset = Any
    from app.services.research.contracts import (
        CoreMetricProfile,
        PreparedDataset,
        TimeSplitResult,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_IMPLEMENTED_STAGES = frozenset(
    {
        "data",
        "features",
        "leakage",
        "metrics",
        "statistics",
        "studies",
        "seasonality",
        "market_structure",
        "modeling",
        "profiles",
    }
)


def _warning_value(warning: ResearchWarning) -> Mapping[str, JSONValue]:
    """Project one internal warning into bounded report evidence.

    Args:
        warning: Validated Research warning.

    Returns:
        JSON-compatible warning evidence.
    """
    return {
        "code": warning.code,
        "message": warning.message,
        "severity": warning.severity,
        "field_path": warning.field_path,
        "details": warning.details,
    }


def _warning_values(
    warnings: tuple[ResearchWarning, ...] | list[ResearchWarning],
) -> list[JSONValue]:
    """Project structured warnings into report-safe evidence.

    Args:
        warnings: Structured Research warnings.

    Returns:
        Detached JSON-compatible warning mappings.
    """
    return [dict(_warning_value(warning)) for warning in warnings]


def _strings(values: tuple[str, ...]) -> list[JSONValue]:
    """Return invariant-safe JSON string evidence.

    Args:
        values: Immutable strings to project.

    Returns:
        JSON-compatible string list.
    """
    return [str(value) for value in values]


def _edge_value(edge: EdgeResult) -> Mapping[str, JSONValue]:
    """Project one edge result into report evidence.

    Args:
        edge: Validated edge result.

    Returns:
        JSON-compatible edge evidence.
    """
    return {
        "schema_version": edge.schema_version,
        "study": edge.study,
        "statistics": edge.statistics,
        "null_evidence": edge.null_evidence,
        "classification": edge.classification,
        "seed": edge.seed,
        "warnings": _warning_values(edge.warnings),
        "advisory_only": edge.advisory_only,
    }


def _leakage_value(report: LeakageReport) -> Mapping[str, JSONValue]:
    """Project leakage evidence into the registered report contract.

    Args:
        report: Validated leakage result.

    Returns:
        JSON-compatible leakage evidence.
    """
    return {
        "schema_version": "v1",
        "suspected_columns": _strings(report.suspected_columns),
        "severity": report.severity,
        "evidence": report.evidence,
        "recommendation": report.recommendation,
        "allowed_forward_columns": _strings(report.allowed_forward_columns),
        "target_column": report.target_column,
        "source_references": _strings(report.source_references),
    }


def _structure_value(
    profile: MarketStructureProfile,
) -> Mapping[str, JSONValue]:
    """Project one market-structure profile into report evidence.

    Args:
        profile: Validated market-structure profile.

    Returns:
        JSON-compatible market-structure evidence.
    """
    return {
        "schema_version": profile.schema_version,
        "structure": profile.structure,
        "score": profile.score,
        "verdict": profile.verdict,
        "strategy_fit": profile.strategy_fit,
        "warnings": _warning_values(profile.warnings),
    }


def _modeling_value(
    result: UnsupervisedResearchResult,
) -> Mapping[str, JSONValue]:
    """Project one modeling result into report evidence.

    Args:
        result: Validated unsupervised result.

    Returns:
        JSON-compatible modeling evidence.
    """
    return {
        "schema_version": result.schema_version,
        "preprocessing": result.preprocessing,
        "pca": result.pca,
        "clusters": result.clusters,
        "insights": result.insights,
        "seed": result.seed,
        "warnings": _warning_values(result.warnings),
        "advisory_only": result.advisory_only,
    }


def _analysis_frame(
    prepared: PreparedDataset,
    feature_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Combine source observations and derived features without mutation.

    Args:
        prepared: Prepared source observations.
        feature_frame: Derived Research features.

    Returns:
        Detached analysis frame containing source and derived columns.
    """
    duplicate_columns = set(prepared.data) & set(feature_frame)
    safe_features = feature_frame.drop(columns=sorted(duplicate_columns))
    return prepared.data.join(safe_features, how="inner")


def _require_stage[T](
    value: T | None,
    *,
    detail: str,
) -> T:
    """Return one selected-stage prerequisite or fail closed.

    Args:
        value: Optional stage result.
        detail: Symbolic dependency error.

    Returns:
        The narrowed stage result.

    Raises:
        ConfigurationError: If the prerequisite is absent.
    """
    if value is None:
        raise ConfigurationError("RES_STAGE_DEPENDENCY_INVALID", detail)
    return value


def _run_studies(
    analysis: pd.DataFrame,
    split: TimeSplitResult,
    *,
    config: EdgeLabConfig,
) -> tuple[list[EdgeResult], list[ResearchWarning]]:
    """Run the three approved edge studies under one failure policy.

    Args:
        analysis: Leakage-reviewed source and feature frame.
        split: Chronological partitions.
        config: Complete Edge Lab configuration.

    Returns:
        Edge results and structured workflow warnings.

    Raises:
        ValidationError: If a study fails and continuation is disabled.
    """
    tagged, tag_warnings = tag_sessions(analysis, config=config.sessions)
    studies: tuple[tuple[str, Callable[[], EdgeResult]], ...] = (
        (
            "mean_reversion",
            lambda: run_eds_mean_reversion(
                analysis,
                split=split,
                study=config.studies,
                statistics=config.statistics,
                limits=config.limits,
            ),
        ),
        (
            "trend_persistence",
            lambda: run_eds_trend_persistence(
                analysis,
                split=split,
                study=config.studies,
                statistics=config.statistics,
                limits=config.limits,
            ),
        ),
        (
            "session",
            lambda: run_eds_session(
                tagged,
                split=split,
                study=config.studies,
                statistics=config.statistics,
                limits=config.limits,
            ),
        ),
    )
    results: list[EdgeResult] = []
    warnings = list(tag_warnings)
    for name, run in studies:
        try:
            results.append(run())
        except ValidationError:
            if not config.studies.continue_on_study_error:
                raise
            warnings.append(
                ResearchWarning(
                    "STUDY_FAILED",
                    "A selected edge study failed under continue-on-error policy",
                    "warning",
                    f"studies.{name}",
                    {"study": name},
                )
            )
    return results, warnings


@dataclass(slots=True)
class _RunState:
    """Mutable internal state for one bounded orchestration call."""

    config: EdgeLabConfig
    performance: object | None
    prepared: PreparedDataset
    warnings: list[ResearchWarning]
    stages: dict[str, Mapping[str, JSONValue]]
    feature_frame: pd.DataFrame | None = None
    feature_metadata: Mapping[str, JSONValue] | None = None
    analysis: pd.DataFrame | None = None
    split: TimeSplitResult | None = None
    metric_profile: CoreMetricProfile | None = None
    seasonality: Mapping[str, JSONValue] | None = None
    edges: list[EdgeResult] | None = None
    market_structure: MarketStructureProfile | None = None
    modeling: UnsupervisedResearchResult | None = None


def _validate_selection(config: EdgeLabConfig) -> None:
    """Validate workflow-level selected-stage dependencies.

    Args:
        config: Complete Edge Lab configuration.

    Raises:
        ConfigurationError: If a stage is unavailable or lacks a prerequisite.
    """
    selected = set(config.selected_stages)
    if "data" not in selected:
        raise ConfigurationError("RES_STAGE_DEPENDENCY_INVALID", "DATA_STAGE_REQUIRED")
    if selected - _IMPLEMENTED_STAGES:
        raise ConfigurationError("RES_STAGE_UNAVAILABLE", "UNAVAILABLE_SELECTED_STAGE")
    if "leakage" in selected and "features" not in selected:
        raise ConfigurationError(
            "RES_STAGE_DEPENDENCY_INVALID",
            "LEAKAGE_REQUIRES_FEATURES",
        )
    if "studies" in selected and not {"features", "leakage"} <= selected:
        raise ConfigurationError(
            "RES_STAGE_DEPENDENCY_INVALID",
            "STUDIES_REQUIRE_SAFE_FEATURES",
        )


def _build_state(
    dataset: MarketDataset,
    *,
    config: EdgeLabConfig,
    performance: object | None,
) -> _RunState:
    """Prepare immutable input evidence and initialize stage state.

    Args:
        dataset: Canonical Data-owned market evidence.
        config: Complete Edge Lab configuration.
        performance: Optional Analytics report.

    Returns:
        Initialized internal workflow state.
    """
    prepared = prepare_research_dataset(
        dataset,
        cleaning=config.cleaning,
        enrichment=config.enrichment,
        limits=config.limits,
    )
    cleaning_actions: list[JSONValue] = [
        dict(action) for action in prepared.quality.cleaning_actions
    ]
    stages: dict[str, Mapping[str, JSONValue]] = {
        "data": {
            "schema_version": "v1",
            "record_count": len(prepared.data),
            "checks": _strings(prepared.quality.checks),
            "cleaning_actions": cleaning_actions,
        },
    }
    return _RunState(
        config=config,
        performance=performance,
        prepared=prepared,
        warnings=list(prepared.quality.warnings),
        stages=stages,
        edges=[],
    )


def _stage_features(state: _RunState) -> None:
    """Execute feature construction for one workflow state."""
    feature_frame, metadata = build_research_feature_frame(
        state.prepared,
        indicator_results={},
        config=state.config.features,
        limits=state.config.limits,
    )
    state.feature_frame = feature_frame
    state.feature_metadata = metadata
    state.analysis = _analysis_frame(state.prepared, feature_frame)
    state.stages["features"] = {
        "schema_version": "v1",
        "row_count": len(feature_frame),
        "column_count": len(feature_frame.columns),
        "metadata": metadata,
    }


def _stage_leakage(state: _RunState) -> None:
    """Execute leakage inspection and chronological splitting."""
    feature_frame = _require_stage(
        state.feature_frame,
        detail="FEATURE_STAGE_REQUIRED",
    )
    metadata = _require_stage(
        state.feature_metadata,
        detail="FEATURE_METADATA_REQUIRED",
    )
    analysis = _require_stage(state.analysis, detail="ANALYSIS_FRAME_REQUIRED")
    leakage = validate_no_lookahead_features(
        feature_frame,
        feature_metadata=metadata,
        target_column=None,
        allowed_forward_columns=state.config.features.allowed_forward_columns,
    )
    state.split = enforce_time_split(
        analysis,
        train_fraction=0.6,
        validation_fraction=0.2,
    )
    state.stages["leakage"] = _leakage_value(leakage)


def _stage_metrics(state: _RunState) -> None:
    """Execute the canonical seven-family metric profile."""
    profile = build_core_metric_profile(
        state.prepared,
        registry=build_default_registry(),
        limits=state.config.limits,
    )
    state.metric_profile = profile
    state.warnings.extend(profile.warnings)
    state.stages["metrics"] = {
        "schema_version": profile.schema_version,
        "metrics": profile.metrics,
        "warnings": _warning_values(profile.warnings),
    }


def _stage_statistics(state: _RunState) -> None:
    """Execute seeded bootstrap and permutation evidence."""
    returns = (
        state.prepared.data["close"]
        .astype("float64")
        .pct_change()
        .dropna()
        .to_numpy(dtype="float64")
    )
    confidence_interval = block_bootstrap_ci(
        returns,
        statistic=lambda values: float(values.mean()),
        confidence=0.95,
        config=state.config.statistics,
    )
    p_value = permutation_test(
        float(returns.mean()),
        returns,
        alternative="two-sided",
        config=state.config.statistics,
    )
    state.stages["statistics"] = {
        "schema_version": "v1",
        "sample_size": len(returns),
        "mean_confidence_interval": [
            confidence_interval[0],
            confidence_interval[1],
        ],
        "permutation_p_value": p_value,
        "seed": state.config.statistics.seed,
    }


def _stage_studies(state: _RunState) -> None:
    """Execute the three approved edge-study families."""
    analysis = _require_stage(state.analysis, detail="ANALYSIS_FRAME_REQUIRED")
    split = _require_stage(state.split, detail="LEAKAGE_SPLIT_REQUIRED")
    edges, warnings = _run_studies(analysis, split, config=state.config)
    state.edges = edges
    state.warnings.extend(warnings)
    edge_values: list[JSONValue] = [dict(_edge_value(edge)) for edge in edges]
    state.stages["studies"] = {
        "schema_version": "v1",
        "results": edge_values,
        "warnings": _warning_values(warnings),
    }


def _stage_seasonality(state: _RunState) -> None:
    """Execute session-aware seasonality analysis."""
    seasonality = run_seasonality(
        state.prepared,
        sessions=state.config.sessions,
        filters=SeasonalityFilters(),
        limits=state.config.limits,
    )
    state.seasonality = seasonality
    state.stages["seasonality"] = seasonality


def _stage_market_structure(state: _RunState) -> None:
    """Execute canonical market-structure profiling."""
    profile = build_market_structure_profile(
        state.prepared,
        config=state.config.market_structure,
        limits=state.config.limits,
    )
    state.market_structure = profile
    state.warnings.extend(profile.warnings)
    state.stages["market_structure"] = _structure_value(profile)


def _stage_modeling(state: _RunState) -> None:
    """Execute bounded unsupervised modeling."""
    analysis = _require_stage(state.analysis, detail="ANALYSIS_FRAME_REQUIRED")
    result = run_unsupervised_research(
        analysis,
        config=state.config.modeling,
        limits=state.config.limits,
    )
    state.modeling = result
    state.warnings.extend(result.warnings)
    state.stages["modeling"] = _modeling_value(result)


def _stage_profiles(state: _RunState) -> None:
    """Execute scorecard and snapshot assembly."""
    metric_profile = _require_stage(
        state.metric_profile,
        detail="METRIC_PROFILE_REQUIRED",
    )
    scorecard = build_research_scorecard(
        metric_profile=metric_profile,
        seasonality=state.seasonality,
        edges=state.edges or [],
        market_structure=state.market_structure,
        modeling=state.modeling,
        performance=state.performance,
    )
    snapshot = build_research_profile_snapshot(
        stages=state.stages,
        scorecard=scorecard,
        dataset_hash=state.prepared.dataset_hash,
        configuration_hash=state.prepared.configuration_hash,
    )
    state.warnings.extend(scorecard.warnings)
    state.stages["profiles"] = {
        "schema_version": snapshot.schema_version,
        "score": scorecard.final_score,
        "readiness": scorecard.readiness,
        "reasons": _strings(scorecard.reasons),
        "stage_count": len(snapshot.stages),
        "advisory_only": scorecard.advisory_only,
    }


_STAGE_RUNNERS: Mapping[str, Callable[[_RunState], None]] = {
    "features": _stage_features,
    "leakage": _stage_leakage,
    "metrics": _stage_metrics,
    "statistics": _stage_statistics,
    "studies": _stage_studies,
    "seasonality": _stage_seasonality,
    "market_structure": _stage_market_structure,
    "modeling": _stage_modeling,
    "profiles": _stage_profiles,
}


def _validate_hypothesis(hypothesis: str) -> None:
    """Validate the explicit hypothesis at the workflow boundary.

    Args:
        hypothesis: Explicit researcher-supplied hypothesis text.

    Raises:
        ValidationError: If the hypothesis is empty or padded.
    """
    if not hypothesis or hypothesis != hypothesis.strip():
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HYPOTHESIS")


def _validated_edge_lab_config(config: object) -> EdgeLabConfig:
    """Return one validated internal Edge Lab configuration.

    Args:
        config: Opaque package-boundary value.

    Returns:
        Validated internal configuration.

    Raises:
        ValidationError: If the value is not a Research configuration.
    """
    if not isinstance(config, EdgeLabConfig):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_EDGE_LAB_CONFIG")
    return config


def run_edge_lab_profile(
    dataset: MarketDataset,
    *,
    hypothesis: str,
    config: object,
    performance: object | None = None,
) -> StandardResponse[ResearchReport]:
    """Run selected deterministic stages and build an advisory report.

    Args:
        dataset: Canonical Data-owned market evidence.
        hypothesis: Explicit researcher-supplied hypothesis.
        config: Opaque complete bounded Research configuration.
        performance: Optional Analytics evidence supplied by the orchestrator.

    Returns:
        Successful or failed standard response containing an advisory
        ``ResearchReport v1`` directly in ``data``.

    Raises:
        ConfigurationError: If stage selection or dependencies are invalid.
        ValidationError: If the hypothesis, input, or selected stage evidence
            is invalid.
        BaseException: Process interruption and asynchronous cancellation are
            re-raised by the standard response exception boundary.
    """
    start_time = perf_counter_ns()
    request_id = generate_id("req")
    extensions: dict[str, JsonValue] = {"workflow_version": "v1"}

    def _metadata() -> ResponseMetadata:
        """Build response metadata for this bounded workflow call.

        Returns:
            Immutable standard response metadata.
        """
        return build_response_metadata(
            name="research.run_edge_lab_profile",
            domain="research",
            risk_level="low",
            request_id=request_id,
            start_time=start_time,
            read_only=True,
            writes_file=False,
            modifies_database=False,
            places_trade=False,
            requires_network=False,
            extensions=extensions,
        )

    try:
        logger.info("Running bounded Research Edge Lab profile")
        _validate_hypothesis(hypothesis)
        config = _validated_edge_lab_config(config)
        extensions["selected_stages"] = tuple(config.selected_stages)
        _validate_selection(config)
        state = _build_state(
            dataset,
            config=config,
            performance=performance,
        )
        selected = set(config.selected_stages)
        for stage, runner in _STAGE_RUNNERS.items():
            if stage in selected:
                runner(state)

        evidence: dict[str, JSONValue] = {
            "selected_stages": _strings(config.selected_stages),
        }
        evidence.update(state.stages)
        if performance is not None:
            evidence["performance_report_ref"] = str(
                get_analytics_value_field(performance, "report_id")
            )

        report_material = {
            "hypothesis": hypothesis,
            "dataset_hash": state.prepared.dataset_hash,
            "configuration_hash": state.prepared.configuration_hash,
            "selected_stages": _strings(config.selected_stages),
        }
        report_hash = canonical_digest(report_material)
        report = ResearchReport(
            contract_version="v1",
            schema_id="research.report.v1",
            report_id=f"research-report-{report_hash[:24]}",
            hypothesis=hypothesis,
            evidence=evidence,
            seeds={
                "statistics": config.statistics.seed,
                "modeling": config.modeling.seed,
            },
            configuration_hash=state.prepared.configuration_hash,
            dataset_hash=state.prepared.dataset_hash,
            source_references=state.prepared.source_references,
            warnings=tuple(state.warnings),
            generated_at=dataset.available_at,
            dependency_versions={
                "data": dataset.normalization_version,
                "research": "v1",
            },
            duration_ms=get_execution_ms(start_time),
            advisory_only=True,
        )
        return success_response(
            report,
            message="Research Edge Lab profile completed",
            metadata=_metadata(),
        )
    except ResearchError as error:
        return error_response(
            code=error.code,
            details={"detail": error.detail},
            message="Research Edge Lab profile failed",
            metadata=_metadata(),
            catalog=cast("Any", RESEARCH_ERROR_CATALOG),
        )
    except Exception as error:  # noqa: BLE001 - public response boundary.
        return exception_response(
            error,
            message="Research Edge Lab profile failed",
            metadata=_metadata(),
            catalog=cast("Any", RESEARCH_ERROR_CATALOG),
        )


__all__ = ("run_edge_lab_profile",)
