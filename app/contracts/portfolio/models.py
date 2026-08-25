"""Strict Pydantic v2 wire records for the ratified Portfolio v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# These reference records are annotation-only for readers but Pydantic
# resolves them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import InstrumentRef  # noqa: TC001
from app.contracts.common.models import (
    ContentHash,
    CurrencyCode,
    DecimalValue,
    JsonObject,
    Money,
    Rounding,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)
from app.contracts.data.models import AlignmentPolicy  # noqa: TC001
from app.contracts.research.models import ResearchBudget  # noqa: TC001

# Constrained local string alias reused across portfolio records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: plugin stable IDs are external-origin identifiers owned
# by the Plugins namespace (portfolio README §21.4 reference); the ratified
# pattern is mirrored here because the plugins namespace exposes no strict
# wire alias to import.
type PluginStableId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$"),
]
# Constrained local integer alias for count fields.
type NonNegativeInt = Annotated[int, Field(ge=0)]

# Closed allocation enums from the ratified Portfolio v1 public records.
type AllocationMethod = Literal[
    "FIXED_WEIGHT",
    "FIXED_NOTIONAL",
    "VOLATILITY_SCALED",
    "CUSTOM",
]
type AllocationNormalization = Literal["NONE", "L1_BUDGET", "CAPITAL"]
type ExposureLimitKind = Literal[
    "GROSS",
    "NET",
    "PER_INSTRUMENT",
    "PER_CURRENCY",
    "PER_MARKET",
    "PER_STRATEGY",
    "CONCURRENT_POSITIONS",
]
type SharedInstrumentPolicy = Literal["NET", "INDEPENDENT", "REJECT"]
type ObjectiveDirection = Literal["MINIMIZE", "MAXIMIZE"]
type ParetoStatus = Literal["DOMINATED", "NON_DOMINATED", "UNRANKED"]
type MetricBasis = Literal[
    "AGGREGATE_EQUITY",
    "CONSTITUENT_RETURNS",
    "ALLOCATED_CAPITAL",
    "EXPOSURE_ADJUSTED_CAPITAL",
]
type MetricUnit = Literal["MONEY", "PERCENT", "PIPS", "RATIO", "COUNT"]
type PortfolioMergeMode = Literal[
    "SIMULATED_PORTFOLIO",
    "PARALLEL_COMPOUND",
    "FUZZY_ENSEMBLE",
]


class ExposureLimit(WireModel):
    """One declared exposure limit kind with its bound and optional scope.

    Nested record of ``Allocation`` (R4) and ``PortfolioConstraintSet`` (R5).
    """

    kind: ExposureLimitKind
    limit: DecimalValue
    instrument: InstrumentRef | None = None
    currency: CurrencyCode | None = None


class RebalancePolicy(WireModel):
    """Declared rebalance schedule, trigger, bands, costs, and timing.

    Nested record of ``Allocation`` (R4).
    """

    schedule: NonEmptyStr
    trigger: JsonObject
    tolerance_bands: DecimalValue | None = None
    turnover_cost_policy: JsonObject
    execution_timing: NonEmptyStr
    unresolved_order_policy: NonEmptyStr

    @model_validator(mode="after")
    def validate_tolerance_bands(self) -> RebalancePolicy:
        """Reject tolerance bands outside the unit interval.

        Returns:
            The validated rebalance policy.

        Raises:
            ValueError: ``tolerance_bands`` is not within [0, 1].
        """
        if self.tolerance_bands is not None and not (
            Decimal(0) <= Decimal(self.tolerance_bands) <= Decimal(1)
        ):
            raise ValueError("tolerance_bands must be within [0, 1]")
        return self


class Allocation(WireModel):
    """One capital allocation policy, incomplete during composition (R4).

    An incomplete allocation is completed before the portfolio version is
    admitted; allocation fixtures reconcile requested and allocated capital
    exactly. A ``custom_policy`` carries the §21.4 plugin method identity
    when ``method`` is ``CUSTOM``.
    """

    allocation_id: Uuid7
    method: AllocationMethod
    custom_policy: JsonObject = Field(default_factory=dict)
    normalization: AllocationNormalization
    rounding: Rounding
    rebalance: RebalancePolicy | None = None
    exposure_limits: tuple[ExposureLimit, ...] = ()
    shared_instrument_policy: SharedInstrumentPolicy = "REJECT"
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioRef(WireModel):
    """Reference to one portfolio identity (R1)."""

    portfolio_id: Uuid7
    schema_version: Literal[1] = 1


class PortfolioMember(WireModel):
    """One constituent strategy version of a portfolio version (R3).

    Admission validates date overlap, result compatibility, required
    currencies, duplicate exposure, and constituent availability.
    """

    member_id: Uuid7
    strategy_version_id: Uuid7
    result_id: Uuid7 | None = None
    data_manifest_id: Uuid7 | None = None
    weight: DecimalValue | None = None
    sizing_rule: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_weight(self) -> PortfolioMember:
        """Reject fractional weights outside the unit interval.

        Returns:
            The validated portfolio member.

        Raises:
            ValueError: ``weight`` is not within [0, 1].
        """
        if self.weight is not None and not (
            Decimal(0) <= Decimal(self.weight) <= Decimal(1)
        ):
            raise ValueError("weight must be within [0, 1]")
        return self


class PortfolioConstraintSet(WireModel):
    """One declared portfolio constraint set (R5).

    Breaches are prevented or resolved deterministically by the owning
    feature; the record only freezes the declared limits.
    """

    constraint_set_id: Uuid7
    exposure_limits: tuple[ExposureLimit, ...] = ()
    custom_constraints: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioVersion(WireModel):
    """One immutable version of a portfolio and its policies (R2).

    Saving a portfolio creates an immutable version with a canonical hash;
    invalid portfolios are rejected before simulation and promotion of
    automatic-search results preserves ``search_lineage``.
    """

    portfolio_id: Uuid7
    version: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=160)
    members: tuple[PortfolioMember, ...] = ()
    allocation: Allocation
    constraints: PortfolioConstraintSet | None = None
    currency_policy: JsonObject
    capital: Money
    valid_from: UtcTimestamp
    valid_to: UtcTimestamp | None = None
    search_lineage: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class CorrelationRequest(WireModel):
    """One versioned correlation input policy for a candidate set (R6)."""

    request_id: Uuid7
    candidate_set_hash: ContentHash
    member_ids: tuple[Uuid7, ...] = Field(min_length=1)
    return_definition: NonEmptyStr
    frequency: NonEmptyStr
    alignment_policy: AlignmentPolicy
    overlap_policy: NonEmptyStr
    minimum_observations: int = Field(ge=1)
    method: NonEmptyStr
    method_version: int = Field(ge=1)
    schema_version: Literal[1] = 1


class CorrelationMatrix(WireModel):
    """One immutable correlation matrix artifact (R7).

    Changing any constituent or policy produces a different identity; the
    matrix values live in the referenced artifact, not on this record.
    """

    matrix_id: Uuid7
    request: CorrelationRequest
    candidate_set_hash: ContentHash
    settings_hash: ContentHash
    observation_counts: dict[NonEmptyStr, NonNegativeInt]
    matrix_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioSimulationRequest(WireModel):
    """One aggregate simulation request for a portfolio version (R8).

    Aggregate simulation merges constituent cash flows and exposures on a
    canonical event timeline without future information; the conversion
    policy declares fail, carry, or explicit fallback per missing rate and
    conversion uses only rates visible at each event timestamp.
    """

    request_id: Uuid7
    portfolio_version_id: Uuid7
    conversion_policy: JsonObject
    from_at: UtcTimestamp | None = None
    to_at: UtcTimestamp | None = None
    idempotency_key: NonEmptyStr
    schema_version: Literal[1] = 1


class PortfolioResult(WireModel):
    """One aggregate portfolio simulation result (R9).

    Aggregate totals reconcile to constituents; ``.sqxpf`` export preserves
    identities, policies, metrics, and artifacts and reproduces the
    canonical portfolio hash on round-trip.
    """

    result_id: Uuid7
    portfolio_version_id: Uuid7
    manifest_id: Uuid7
    aggregate_trades_artifact_id: Uuid7
    cashflow_artifact_id: Uuid7
    equity_drawdown_artifact_id: Uuid7
    exposure_timeline_artifact_id: Uuid7
    constituent_attribution_artifact_id: Uuid7
    turnover: JsonObject
    correlation_matrix_id: Uuid7 | None = None
    constraint_events_artifact_id: Uuid7 | None = None
    daily_returns_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ObjectiveSpec(WireModel):
    """One declared objective of a portfolio search objective vector.

    Nested record of ``PortfolioSearchPlan`` (R10). Multi-objective search
    stays Pareto and never silently scalarizes objectives.
    """

    metric: NonEmptyStr
    direction: ObjectiveDirection
    weight: DecimalValue | None = None

    @model_validator(mode="after")
    def validate_weight(self) -> ObjectiveSpec:
        """Reject nonpositive objective weights.

        Returns:
            The validated objective specification.

        Raises:
            ValueError: ``weight`` is not greater than zero.
        """
        if self.weight is not None and Decimal(self.weight) <= 0:
            raise ValueError("weight must be positive")
        return self


class PortfolioSearchPlan(WireModel):
    """One deterministic automatic portfolio search plan (R10).

    Identical inputs select the same portfolio or the same Pareto set
    ordering; the tie-breaker resolves ties deterministically.
    """

    plan_id: Uuid7
    candidate_set: tuple[Uuid7, ...]
    objective_vector: tuple[ObjectiveSpec, ...] = Field(min_length=1)
    constraints: PortfolioConstraintSet
    search_method: NonEmptyStr
    method_version: int = Field(ge=1)
    budget: ResearchBudget
    seeds: tuple[NonEmptyStr, ...]
    tie_breaker: NonEmptyStr
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioCandidate(WireModel):
    """One evaluated candidate of a portfolio search run (R11).

    Checkpoints persist the frontier, population, evaluated candidates,
    cache keys, budget counters, and RNG state; resume equals uninterrupted
    execution.
    """

    candidate_id: Uuid7
    run_id: Uuid7
    weights: dict[NonEmptyStr, DecimalValue]
    result_id: Uuid7 | None = None
    objective_values: dict[NonEmptyStr, DecimalValue] = Field(default_factory=dict)
    is_feasible: bool = True
    rank: int | None = Field(default=None, ge=1)
    pareto_status: ParetoStatus = "UNRANKED"
    schema_version: Literal[1] = 1


class PortfolioRiskReport(WireModel):
    """One calculated portfolio risk report (R12)."""

    report_id: Uuid7
    portfolio_version_id: Uuid7
    result_id: Uuid7
    daily_expected_return: DecimalValue
    daily_volatility: DecimalValue
    var_confidence: DecimalValue
    var_horizon_days: int = Field(ge=1)
    parametric_var: Money
    expected_shortfall: Money
    cvar_method: NonEmptyStr
    sharpe: DecimalValue
    risk_free_rate: DecimalValue
    risk_free_version: int = Field(ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_var_confidence(self) -> PortfolioRiskReport:
        """Reject confidence levels outside the exclusive unit interval.

        Returns:
            The validated portfolio risk report.

        Raises:
            ValueError: ``var_confidence`` is not within (0, 1).
        """
        if not (Decimal(0) < Decimal(self.var_confidence) < Decimal(1)):
            raise ValueError("var_confidence must be within (0, 1)")
        return self


class PortfolioMetricDefinition(WireModel):
    """One versioned portfolio metric definition (R13).

    Metric metadata removes basis ambiguity between aggregate equity,
    constituent returns, and allocated capital views.
    """

    metric_id: NonEmptyStr
    version: int = Field(ge=1)
    basis: MetricBasis
    formula_ref: NonEmptyStr
    unit: MetricUnit
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class MarkowitzOptimizationRequest(WireModel):
    """One Markowitz optimization request over aligned daily returns (R14)."""

    request_id: Uuid7
    aligned_daily_returns_artifact_id: Uuid7
    expected_return_vector: JsonObject
    sample_covariance_artifact_id: Uuid7
    weight_constraints: JsonObject
    method_version: int = Field(ge=1)
    simulation_count: int | None = Field(default=None, ge=1)
    frontier_points: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1


class FrontierPoint(WireModel):
    """One point of an efficient frontier.

    Nested record of ``EfficientFrontier`` (R15).
    """

    expected_return: DecimalValue
    volatility: DecimalValue
    weights: dict[NonEmptyStr, DecimalValue]


class EfficientFrontier(WireModel):
    """One immutable portfolio optimization artifact (R15)."""

    frontier_id: Uuid7
    request_id: Uuid7
    points: tuple[FrontierPoint, ...] = ()
    maximum_sharpe_weights: dict[NonEmptyStr, DecimalValue] | None = None
    minimum_risk_weights: dict[NonEmptyStr, DecimalValue] | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioMergePlan(WireModel):
    """One portfolio merge plan (R16).

    ``PARALLEL_COMPOUND`` and ``FUZZY_ENSEMBLE`` implement the Experimental
    §21.9 rules; gating is enforced by the owning feature.
    """

    plan_id: Uuid7
    mode: PortfolioMergeMode
    source_strategy_version_ids: tuple[Uuid7, ...] = Field(min_length=1)
    signal_aggregation: JsonObject
    conflict_resolution: NonEmptyStr
    capital_sharing: JsonObject
    order_identity_policy: NonEmptyStr
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioSplitPlan(WireModel):
    """One portfolio split plan (R17).

    Split creates independently versioned constituents preserving the
    allocation snapshot and lineage.
    """

    plan_id: Uuid7
    compound_strategy_version_id: Uuid7
    output_strategy_ids: tuple[Uuid7, ...] = Field(min_length=1)
    allocation_snapshot: Allocation
    lineage: JsonObject
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioMethodDescriptor(WireModel):
    """One §21.4 research-method portfolio plugin descriptor (R18).

    Experimental plugin algorithms only; complete schemas, determinism, and
    conformance vectors are required before stable enablement.
    """

    method_id: NonEmptyStr
    version: int = Field(ge=1)
    plugin_id: PluginStableId
    input_schema: JsonObject
    output_schema: JsonObject
    resource_bounds: JsonObject
    seed_streams: tuple[NonEmptyStr, ...] = ()
    conformance_vectors: tuple[Uuid7, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ComposePortfoliosRequest(WireModel):
    """Operation-discriminated portfolio composition request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "ADD_MEMBER",
        "REMOVE_MEMBER",
        "EDIT_ALLOCATION",
        "EDIT_CONSTRAINTS",
        "VALIDATE",
        "VERSION",
        "PROMOTE",
    ]
    schema_version: Literal[1] = 1


class ComposePortfoliosSuccess(WireModel):
    """Successful portfolio composition operation result."""

    request_id: Uuid7
    version: PortfolioVersion | None = None
    findings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AnalyzeCorrelationRequest(WireModel):
    """Operation-discriminated correlation analysis request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REQUEST", "COMPUTE"]
    schema_version: Literal[1] = 1


class AnalyzeCorrelationSuccess(WireModel):
    """Successful correlation analysis operation result."""

    request_id: Uuid7
    matrix: CorrelationMatrix | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class SimulatePortfoliosRequest(WireModel):
    """Operation-discriminated aggregate simulation request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["SIMULATE", "CONVERT"]
    schema_version: Literal[1] = 1


class SimulatePortfoliosSuccess(WireModel):
    """Successful aggregate simulation operation result."""

    request_id: Uuid7
    result: PortfolioResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class SearchPortfoliosRequest(WireModel):
    """Operation-discriminated portfolio search request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "SEARCH", "CHECKPOINT", "RESUME"]
    schema_version: Literal[1] = 1


class SearchPortfoliosSuccess(WireModel):
    """Successful portfolio search operation result."""

    request_id: Uuid7
    plan: PortfolioSearchPlan | None = None
    candidates: tuple[PortfolioCandidate, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AnalyzePortfolioRiskRequest(WireModel):
    """Operation-discriminated portfolio risk request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REPORT", "DEFINE_METRIC"]
    schema_version: Literal[1] = 1


class AnalyzePortfolioRiskSuccess(WireModel):
    """Successful portfolio risk operation result."""

    request_id: Uuid7
    report: PortfolioRiskReport | None = None
    metric: PortfolioMetricDefinition | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class OptimizeMarkowitzRequest(WireModel):
    """Operation-discriminated Markowitz optimization request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["OPTIMIZE"]
    schema_version: Literal[1] = 1


class OptimizeMarkowitzSuccess(WireModel):
    """Successful Markowitz optimization operation result."""

    request_id: Uuid7
    frontier: EfficientFrontier | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class MergePortfoliosRequest(WireModel):
    """Operation-discriminated portfolio merge and split request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN_MERGE", "PLAN_SPLIT", "EXECUTE"]
    schema_version: Literal[1] = 1


class MergePortfoliosSuccess(WireModel):
    """Successful portfolio merge and split operation result."""

    request_id: Uuid7
    merge_plan: PortfolioMergePlan | None = None
    split_plan: PortfolioSplitPlan | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExtendPortfolioMethodsRequest(WireModel):
    """Operation-discriminated portfolio method extension request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record. ``REGISTER_METHOD``
    is Experimental gated.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REGISTER_METHOD"]
    schema_version: Literal[1] = 1


class ExtendPortfolioMethodsSuccess(WireModel):
    """Successful portfolio method extension operation result."""

    request_id: Uuid7
    method: PortfolioMethodDescriptor | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# PEP 695 ``type`` aliases are not classes and cannot be registered in
# WIRE_MODELS; every concrete wire record is registered by its ratified
# record name, including the nested records spelled inside the R4, R10,
# and R15 table rows.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "PortfolioRef": PortfolioRef,
    "PortfolioVersion": PortfolioVersion,
    "PortfolioMember": PortfolioMember,
    "Allocation": Allocation,
    "ExposureLimit": ExposureLimit,
    "RebalancePolicy": RebalancePolicy,
    "PortfolioConstraintSet": PortfolioConstraintSet,
    "CorrelationRequest": CorrelationRequest,
    "CorrelationMatrix": CorrelationMatrix,
    "PortfolioSimulationRequest": PortfolioSimulationRequest,
    "PortfolioResult": PortfolioResult,
    "PortfolioSearchPlan": PortfolioSearchPlan,
    "ObjectiveSpec": ObjectiveSpec,
    "PortfolioCandidate": PortfolioCandidate,
    "PortfolioRiskReport": PortfolioRiskReport,
    "PortfolioMetricDefinition": PortfolioMetricDefinition,
    "MarkowitzOptimizationRequest": MarkowitzOptimizationRequest,
    "EfficientFrontier": EfficientFrontier,
    "FrontierPoint": FrontierPoint,
    "PortfolioMergePlan": PortfolioMergePlan,
    "PortfolioSplitPlan": PortfolioSplitPlan,
    "PortfolioMethodDescriptor": PortfolioMethodDescriptor,
    "ComposePortfoliosRequest": ComposePortfoliosRequest,
    "ComposePortfoliosSuccess": ComposePortfoliosSuccess,
    "AnalyzeCorrelationRequest": AnalyzeCorrelationRequest,
    "AnalyzeCorrelationSuccess": AnalyzeCorrelationSuccess,
    "SimulatePortfoliosRequest": SimulatePortfoliosRequest,
    "SimulatePortfoliosSuccess": SimulatePortfoliosSuccess,
    "SearchPortfoliosRequest": SearchPortfoliosRequest,
    "SearchPortfoliosSuccess": SearchPortfoliosSuccess,
    "AnalyzePortfolioRiskRequest": AnalyzePortfolioRiskRequest,
    "AnalyzePortfolioRiskSuccess": AnalyzePortfolioRiskSuccess,
    "OptimizeMarkowitzRequest": OptimizeMarkowitzRequest,
    "OptimizeMarkowitzSuccess": OptimizeMarkowitzSuccess,
    "MergePortfoliosRequest": MergePortfoliosRequest,
    "MergePortfoliosSuccess": MergePortfoliosSuccess,
    "ExtendPortfolioMethodsRequest": ExtendPortfolioMethodsRequest,
    "ExtendPortfolioMethodsSuccess": ExtendPortfolioMethodsSuccess,
}
