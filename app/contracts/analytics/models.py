"""Strict Pydantic v2 wire records for the ratified Analytics v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.contracts.common.models import (
    ContentHash,
    DecimalValue,
    Direction,
    JsonObject,
    JsonValue,
    Money,
    PlUnit,
    Rounding,
    Segment,
    UtcTimestamp,
    Uuid7,
    WireModel,
)

# Strategy and Simulator reference records are annotation-only for readers,
# but Pydantic resolves them at class-creation time, so they must remain
# runtime imports.
from app.contracts.simulator.models import RunManifest  # noqa: TC001
from app.contracts.strategy.models import StrategyRef  # noqa: TC001

# Constrained local string aliases reused across analytics records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Databank display names are bounded to 1..160 characters by the ratified
# R2 rule; the bound is a product limit, not a persisted name constraint.
type DatabankName = Annotated[str, StringConstraints(min_length=1, max_length=160)]
# Domain assumption: IANA zone names are limited to zone/path segments made
# of letters, digits, ``+``, ``-``, and ``_``; this is a syntactic wire
# check, not tzdb resolution.
type IanaTimezone = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9+\-_]+(?:/[A-Za-z0-9+\-_]+)*$"),
]


class DatabankRef(WireModel):
    """Reference to one databank identity."""

    databank_id: Uuid7
    schema_version: Literal[1] = 1


class MembershipPolicy(WireModel):
    """Versioned admission policy of one databank.

    Capacity, duplicate scope, rank policy, replacement tie-breaker, and
    optional correlation policy are evaluated inside one transactional
    admission decision; concurrent acceptance never exceeds capacity or
    produces nondeterministic survivors.
    """

    capacity: int | None = Field(ge=1)
    duplicate_scope: Literal["STRATEGY", "RUN", "RESULT_FINGERPRINT"]
    rank_policy: NonEmptyStr
    replacement_tiebreaker: Literal["OLDEST", "LOWEST_RANK", "REJECT"]
    correlation_policy: JsonObject = Field(default_factory=dict)


class DatabankVersion(WireModel):
    """One immutable version of a named project-scoped databank.

    Duplicate names are rejected, rename preserves membership, and a
    concurrent rename/delete yields exactly one success and one version
    conflict; those cross-record rules are enforced by the owning store.
    """

    databank_id: Uuid7
    version: int = Field(ge=1)
    name: DatabankName
    project_id: Uuid7
    capacity: int | None = Field(default=None, ge=1)
    view_id: Uuid7 | None = None
    membership_policy: MembershipPolicy
    row_version: int = Field(default=1, ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DatabankItem(WireModel):
    """One databank membership row referencing an immutable strategy version.

    Insertion is transactional and idempotent (one membership row per
    repeat); copy, move, remove, and rename never mutate strategy versions,
    and referenced strategies, results, artifacts, and lineage are never
    deleted by eviction or removal.
    """

    item_id: Uuid7
    databank_id: Uuid7
    strategy_version_id: Uuid7
    result_id: Uuid7 | None = None
    display_name: str = ""
    accepted_at: UtcTimestamp
    source: NonEmptyStr
    rank: DecimalValue | None = None
    schema_version: Literal[1] = 1


class DatabankDecision(WireModel):
    """One transactional admission decision of a databank.

    ``candidate`` carries the strategy-version or result identity under
    evaluation; a crash or retry yields exactly one membership outcome and
    one decision record.
    """

    decision_id: Uuid7
    databank_id: Uuid7
    sequence: int = Field(ge=0)
    candidate: Uuid7
    stage: NonEmptyStr
    policy_version: int = Field(ge=1)
    observed: JsonObject
    outcome: Literal["ACCEPTED", "REJECTED", "REPLACED", "DUPLICATE"]
    replaced_item_id: Uuid7 | None = None
    decided_at: UtcTimestamp
    schema_version: Literal[1] = 1


class SortSpec(WireModel):
    """One stable sort ordering of a result-query column."""

    column: NonEmptyStr
    ascending: bool = True


class FilterSpec(WireModel):
    """One typed column-filter predicate of a result query."""

    column: NonEmptyStr
    operator: NonEmptyStr
    value: JsonValue


class FormulaColumn(WireModel):
    """One sandboxed formula column of a result query."""

    name: NonEmptyStr
    expression: NonEmptyStr
    unit: NonEmptyStr


class ResultQuery(WireModel):
    """One bounded result-table query with views, formulas, and paging.

    Columns, filter operators, and formula functions are evaluated against
    allowlisted fields with bounded complexity; that runtime policy is
    enforced by the owning feature, not by this wire record.
    """

    query_id: Uuid7
    databank_id: Uuid7 | None = None
    columns: tuple[NonEmptyStr, ...] = ()
    sort: tuple[SortSpec, ...] = ()
    filters: tuple[FilterSpec, ...] = ()
    formulas: tuple[FormulaColumn, ...] = ()
    grouping: tuple[NonEmptyStr, ...] = ()
    cursor: str | None = None
    page_size: int = Field(default=100, ge=1, le=500)
    schema_version: Literal[1] = 1


class SavedResultView(WireModel):
    """One versioned saved view of a result query.

    Reopening reproduces the query even after default column changes;
    pinned segments and display units are versioned independently from
    databank membership.
    """

    view_id: Uuid7
    version: int = Field(ge=1)
    name: NonEmptyStr
    query: ResultQuery
    pinned_segments: tuple[Segment, ...] = ()
    display_units: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ResultPage(WireModel):
    """One bounded page of typed result rows.

    Pages are planned server-side and bounded to 500 rows / 16 MiB per
    Project §15.7; exported full-resolution data is never downsampled.
    """

    page_id: Uuid7
    query_id: Uuid7
    rows: tuple[JsonObject, ...] = ()
    next_cursor: str | None = None
    total_count: int | None = Field(default=None, ge=0)
    schema_version: Literal[1] = 1


class MetricDefinition(WireModel):
    """One versioned catalogue metric formula.

    Phase 1 implements exactly the Project §9 catalogue; no unspecified
    metric aliases another formula, and changing a formula version never
    alters previously committed values.
    """

    metric_id: NonEmptyStr
    version: int = Field(ge=1)
    formula_ref: NonEmptyStr
    input_series: tuple[NonEmptyStr, ...]
    unit: Literal["MONEY", "PERCENT", "PIPS", "RATIO", "COUNT"]
    scope: Literal["RESULT", "SEGMENT", "DIRECTION"]
    rounding: Rounding
    annualization: NonEmptyStr
    minimum_sample: int = Field(default=0, ge=0)
    null_policy: NonEmptyStr
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class MetricValue(WireModel):
    """One committed metric value or its null reason.

    Exactly one of ``value`` and ``null_reason`` is set, and the composite
    key (result, segment, direction, metric definition) is unique per the
    metric-values table anchor.
    """

    result_id: Uuid7
    segment: Segment
    direction: Direction
    metric_id: NonEmptyStr
    metric_version: int = Field(ge=1)
    value: DecimalValue | None = None
    null_reason: NonEmptyStr | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_value_exclusivity(self) -> MetricValue:
        """Reject rows carrying both or neither of value and null_reason.

        Returns:
            The validated metric value.

        Raises:
            ValueError: ``value`` and ``null_reason`` are both set or both
                missing.
        """
        if (self.value is None) == (self.null_reason is None):
            raise ValueError("exactly one of value and null_reason is required")
        return self


class AlignedMetricDelta(WireModel):
    """One aligned metric delta of a result comparison.

    Values and delta are null when the metric cannot be aligned for the
    compared pair; ``null_reason`` explains the missing alignment.
    """

    metric_id: NonEmptyStr
    metric_version: int = Field(ge=1)
    baseline_value: DecimalValue | None
    compared_value: DecimalValue | None
    delta: DecimalValue | None
    null_reason: NonEmptyStr | None = None


class ResultComparison(WireModel):
    """One aligned comparison of two committed results.

    Segments, currencies, metric versions, and sampling align before any
    delta is calculated; incompatible comparisons return a structured
    ``incompatibility_reason`` instead of misleading values.
    """

    comparison_id: Uuid7
    baseline_result_id: Uuid7
    compared_result_id: Uuid7
    aligned_metrics: tuple[AlignedMetricDelta, ...] = ()
    incompatibility_reason: NonEmptyStr | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ChartSpec(WireModel):
    """One bounded chart specification over result series.

    Downsampled curves retain global and bucket min/max without loading
    full artifacts into API memory.
    """

    chart_id: Uuid7
    kind: Literal[
        "EQUITY",
        "BALANCE",
        "DRAWDOWN",
        "VOLATILITY",
        "BENCHMARK",
        "VOLUME",
        "CUSTOM",
    ]
    series_refs: tuple[Uuid7, ...] = ()
    downsampling: Literal["EXTREMA_PRESERVING", "FULL"]
    bounded_points: int = Field(ge=1)
    schema_version: Literal[1] = 1


class TradeAnalysis(WireModel):
    """One immutable temporal trade-analysis artifact of a result.

    One artifact exists per ``analysis_artifacts(result_id, type,
    settings_hash)`` anchor; bucket details live in the referenced bucket
    artifact, not on this record.
    """

    analysis_id: Uuid7
    result_id: Uuid7
    event_basis: NonEmptyStr
    timezone: IanaTimezone
    dimensions: tuple[
        Literal["YEAR", "ENTRY_HOUR", "EXIT_HOUR", "DAY_OF_WEEK", "DAY_OF_MONTH"],
        ...,
    ]
    segment: Segment
    direction: Direction
    metric_ids: tuple[NonEmptyStr, ...]
    empty_bucket_policy: NonEmptyStr
    bucket_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class BenchmarkComparison(WireModel):
    """One immutable benchmark comparison artifact of a result.

    Normalization recomputes only the benchmark initial-capital/allocation
    input; the aligned equity artifact carries the shared series basis.
    """

    comparison_id: Uuid7
    result_id: Uuid7
    benchmark_data_version_id: Uuid7
    holding_method: Literal["BUY_AND_HOLD"]
    eligible_from: UtcTimestamp
    eligible_to: UtcTimestamp
    initial_capital: Money
    normalization: Literal[
        "NONE",
        "ABSOLUTE_DRAWDOWN",
        "PERCENT_DRAWDOWN",
        "MONEY_MANAGEMENT",
        "EXPOSURE",
    ]
    normalization_version: int = Field(ge=1)
    aligned_equity_artifact_id: Uuid7
    metric_ids: tuple[NonEmptyStr, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ResultExchangePackage(WireModel):
    """One versioned ``.sqxr`` interchange package of a committed result.

    Tampering with one member fails verification naming that member;
    external importers normalize through versioned adapters that preserve
    unmapped fields as namespaced attachments.
    """

    package_id: Uuid7
    result_id: Uuid7
    strategy_ref: StrategyRef
    strategy_content_hash: ContentHash
    settings_artifact_id: Uuid7
    orders_artifact_id: Uuid7
    fills_artifact_id: Uuid7
    trades_artifact_id: Uuid7
    equity_artifact_id: Uuid7
    metrics_artifact_id: Uuid7
    journal_index_artifact_id: Uuid7
    selected_only: bool = True
    checksums: dict[NonEmptyStr, ContentHash]
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class BulkSelectionToken(WireModel):
    """One pinned selection snapshot of databank item identities.

    Membership changes during bulk execution do not alter the target set;
    the token expires at ``expires_at``.
    """

    token_id: Uuid7
    databank_id: Uuid7
    item_ids: tuple[Uuid7, ...] = Field(min_length=1)
    pinned_query_hash: ContentHash
    dry_run_impact: JsonObject = Field(default_factory=dict)
    created_at: UtcTimestamp
    expires_at: UtcTimestamp
    schema_version: Literal[1] = 1


class BulkDatabankCommand(WireModel):
    """One idempotent bulk command over a pinned selection token.

    Retrying an interrupted bulk transfer is idempotent; conflicts,
    deduplication, and rejected memberships are recorded in
    ``impact_counts``.
    """

    command_id: Uuid7
    selection_token_id: Uuid7
    action: Literal[
        "COPY", "MOVE", "EXPORT", "DELETE", "TAG", "NOTE", "RETEST", "CUSTOM"
    ]
    target_databank_id: Uuid7 | None = None
    conflict_policy: Literal["REJECT", "KEEP_EXISTING", "CREATE_NEW_VERSION"]
    idempotency_key: NonEmptyStr
    impact_counts: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1


class AnalysisPanelDescriptor(WireModel):
    """One declared custom analysis panel contribution.

    Incompatible panels are disabled with diagnostics while core results
    remain available.
    """

    panel_id: NonEmptyStr
    plugin_id: NonEmptyStr | None = None
    supported_schemas: tuple[NonEmptyStr, ...]
    required_permissions: tuple[NonEmptyStr, ...] = ()
    frontend_bundle_hash: ContentHash
    compatibility_range: NonEmptyStr
    schema_version: Literal[1] = 1


class Tolerances(WireModel):
    """Relative-tolerance bands of one similarity query.

    Each band is an inclusive fraction in the closed interval [0, 1].
    """

    number_of_trades: DecimalValue
    net_profit: DecimalValue
    drawdown: DecimalValue

    @model_validator(mode="after")
    def validate_tolerances(self) -> Tolerances:
        """Reject tolerance bands outside the closed interval [0, 1].

        Returns:
            The validated tolerances.

        Raises:
            ValueError: Any tolerance band is below 0 or above 1.
        """
        bands = (
            ("number_of_trades", self.number_of_trades),
            ("net_profit", self.net_profit),
            ("drawdown", self.drawdown),
        )
        for name, band in bands:
            tolerance = Decimal(band)
            if tolerance < 0 or tolerance > 1:
                raise ValueError(name + " must be within [0, 1]")
        return self


class SimilarityQuery(WireModel):
    """One relative-tolerance result-similarity query.

    Fingerprint matching is independent of semantic AST duplicates: two
    results are similar when their relative deviations stay within the
    declared tolerance bands of one pinned rule version.
    """

    query_id: Uuid7
    databank_id: Uuid7
    reference_result_id: Uuid7
    tolerances: Tolerances
    rule_version: int = Field(ge=1)
    schema_version: Literal[1] = 1


class SimilarityMatch(WireModel):
    """One similarity verdict for a candidate result.

    ``deviations`` reports the relative deviations of the candidate
    fingerprint against the query tolerances.
    """

    query_id: Uuid7
    candidate_result_id: Uuid7
    is_similar: bool
    deviations: JsonObject
    schema_version: Literal[1] = 1


class OperationalJournalArtifact(WireModel):
    """One immutable derived operational-journal artifact.

    Joins immutable Strategy intent/manual plans, Risk decisions, Trading
    operations, annotations, and outcomes using stable identities keyed to
    one source-set and policy hash.
    """

    journal_id: Uuid7
    source_set_hash: ContentHash
    policy_hash: ContentHash
    intent_refs: tuple[Uuid7, ...] = ()
    risk_decision_refs: tuple[Uuid7, ...] = ()
    trading_operation_refs: tuple[Uuid7, ...] = ()
    annotation_refs: tuple[Uuid7, ...] = ()
    time_basis: NonEmptyStr
    output_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class QualificationProfileVersion(WireModel):
    """One versioned operator-qualification policy."""

    profile_id: Uuid7
    version: int = Field(ge=1)
    evidence_kinds: tuple[Literal["TRAINING", "REPLAY", "LIVE"], ...]
    competencies: JsonObject
    thresholds: JsonObject
    validity_days: int = Field(ge=1)
    reviewer_approval_required: bool = True
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class OperatorQualification(WireModel):
    """One operator qualification decision under a pinned profile version.

    Sparse or biased evidence samples surface as ``INSUFFICIENT_EVIDENCE``,
    never as defensible conclusions.
    """

    qualification_id: Uuid7
    principal_id: Uuid7
    profile_id: Uuid7
    profile_version: int = Field(ge=1)
    outcome: Literal[
        "QUALIFIED",
        "CONDITIONAL",
        "NOT_QUALIFIED",
        "INSUFFICIENT_EVIDENCE",
    ]
    evidence_refs: tuple[Uuid7, ...] = ()
    decided_at: UtcTimestamp
    expires_at: UtcTimestamp | None = None
    reviewer_principal_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class DatabankMembershipRequest(WireModel):
    """Operation-discriminated databank membership request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "CREATE",
        "RENAME",
        "DELETE",
        "ADMIT",
        "MODIFY_ITEMS",
        "DEFINE_POLICY",
    ]
    schema_version: Literal[1] = 1


class DatabankMembershipSuccess(WireModel):
    """Successful databank membership operation result."""

    request_id: Uuid7
    databank: DatabankVersion | None = None
    item: DatabankItem | None = None
    decision: DatabankDecision | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class QueryResultsRequest(WireModel):
    """Operation-discriminated result query request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["QUERY", "SAVE_VIEW", "EVALUATE_FORMULA", "BOUND_SERIES"]
    schema_version: Literal[1] = 1


class QueryResultsSuccess(WireModel):
    """Successful result query operation result."""

    request_id: Uuid7
    page: ResultPage | None = None
    view: SavedResultView | None = None
    chart: ChartSpec | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class InterpretResultsRequest(WireModel):
    """Operation-discriminated result interpretation request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "OVERVIEW",
        "LIST_TRADES",
        "METRICS",
        "COMPARE",
        "SHOW_MANIFEST",
    ]
    schema_version: Literal[1] = 1


class InterpretResultsSuccess(WireModel):
    """Successful result interpretation operation result.

    The typed overview spelling carries the applied scope on every result
    so overview, metrics, trades, and charts stay consistently filtered;
    the run manifest remains Simulator-owned.
    """

    request_id: Uuid7
    metric_values: tuple[MetricValue, ...] = ()
    comparison: ResultComparison | None = None
    manifest: RunManifest | None = None
    segment: Segment
    direction: Direction
    pl_unit: PlUnit
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AnalyzeTradesRequest(WireModel):
    """Operation-discriminated trade analysis request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["TIMING_ANALYSIS", "RECONSTRUCT_CHART", "COMPARE_BENCHMARK"]
    schema_version: Literal[1] = 1


class AnalyzeTradesSuccess(WireModel):
    """Successful trade analysis operation result."""

    request_id: Uuid7
    analysis: TradeAnalysis | None = None
    benchmark: BenchmarkComparison | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExchangeResultsRequest(WireModel):
    """Operation-discriminated result interchange request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["EXPORT_ROWS", "PACKAGE", "IMPORT_EXTERNAL"]
    schema_version: Literal[1] = 1


class ExchangeResultsSuccess(WireModel):
    """Successful result interchange operation result."""

    request_id: Uuid7
    package: ResultExchangePackage | None = None
    artifact_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class BulkDatabankRequest(WireModel):
    """Operation-discriminated bulk databank request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PIN_SELECTION", "DRY_RUN", "EXECUTE"]
    schema_version: Literal[1] = 1


class BulkDatabankSuccess(WireModel):
    """Successful bulk databank operation result."""

    request_id: Uuid7
    selection: BulkSelectionToken | None = None
    command: BulkDatabankCommand | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class MatchResultsRequest(WireModel):
    """Operation-discriminated result similarity request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["QUERY_SIMILARITY"]
    schema_version: Literal[1] = 1


class MatchResultsSuccess(WireModel):
    """Successful result similarity operation result."""

    request_id: Uuid7
    matches: tuple[SimilarityMatch, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CustomPanelsRequest(WireModel):
    """Operation-discriminated custom analysis panel request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["RUN_CUSTOM_ANALYSIS", "DECLARE_PANEL"]
    schema_version: Literal[1] = 1


class CustomPanelsSuccess(WireModel):
    """Successful custom analysis panel operation result."""

    request_id: Uuid7
    panel: AnalysisPanelDescriptor | None = None
    output_artifact_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class QualifyOperationsRequest(WireModel):
    """Operation-discriminated operational analysis request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "BUILD_JOURNAL",
        "MEASURE_ADHERENCE",
        "SUMMARIZE_BEHAVIOR",
        "ANALYZE_EMERGENCY",
        "QUALIFY",
        "EXPORT",
    ]
    schema_version: Literal[1] = 1


class QualifyOperationsSuccess(WireModel):
    """Successful operational analysis operation result."""

    request_id: Uuid7
    journal: OperationalJournalArtifact | None = None
    qualification: OperatorQualification | None = None
    profile: QualificationProfileVersion | None = None
    export_artifact_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# The inline nested records spelled inside table rows (MembershipPolicy,
# SortSpec, FilterSpec, FormulaColumn, AlignedMetricDelta, and Tolerances) are
# structural components of the 22 registered public records, not numbered
# public records themselves, so they are not registered in WIRE_MODELS.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "DatabankRef": DatabankRef,
    "DatabankVersion": DatabankVersion,
    "DatabankItem": DatabankItem,
    "DatabankDecision": DatabankDecision,
    "ResultQuery": ResultQuery,
    "SavedResultView": SavedResultView,
    "ResultPage": ResultPage,
    "MetricDefinition": MetricDefinition,
    "MetricValue": MetricValue,
    "ResultComparison": ResultComparison,
    "ChartSpec": ChartSpec,
    "TradeAnalysis": TradeAnalysis,
    "BenchmarkComparison": BenchmarkComparison,
    "ResultExchangePackage": ResultExchangePackage,
    "BulkSelectionToken": BulkSelectionToken,
    "BulkDatabankCommand": BulkDatabankCommand,
    "AnalysisPanelDescriptor": AnalysisPanelDescriptor,
    "SimilarityQuery": SimilarityQuery,
    "SimilarityMatch": SimilarityMatch,
    "OperationalJournalArtifact": OperationalJournalArtifact,
    "QualificationProfileVersion": QualificationProfileVersion,
    "OperatorQualification": OperatorQualification,
    "DatabankMembershipRequest": DatabankMembershipRequest,
    "DatabankMembershipSuccess": DatabankMembershipSuccess,
    "QueryResultsRequest": QueryResultsRequest,
    "QueryResultsSuccess": QueryResultsSuccess,
    "InterpretResultsRequest": InterpretResultsRequest,
    "InterpretResultsSuccess": InterpretResultsSuccess,
    "AnalyzeTradesRequest": AnalyzeTradesRequest,
    "AnalyzeTradesSuccess": AnalyzeTradesSuccess,
    "ExchangeResultsRequest": ExchangeResultsRequest,
    "ExchangeResultsSuccess": ExchangeResultsSuccess,
    "BulkDatabankRequest": BulkDatabankRequest,
    "BulkDatabankSuccess": BulkDatabankSuccess,
    "MatchResultsRequest": MatchResultsRequest,
    "MatchResultsSuccess": MatchResultsSuccess,
    "CustomPanelsRequest": CustomPanelsRequest,
    "CustomPanelsSuccess": CustomPanelsSuccess,
    "QualifyOperationsRequest": QualifyOperationsRequest,
    "QualifyOperationsSuccess": QualifyOperationsSuccess,
}
