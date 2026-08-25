"""Strict Pydantic v2 wire records for the ratified Research v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# Catalogue reference records are annotation-only for readers, but Pydantic
# resolves them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import (  # noqa: TC001
    BrokerRef,
    InstrumentRef,
    UniverseRef,
)
from app.contracts.common.models import (
    ContentHash,
    DecimalValue,
    Direction,
    JsonObject,
    JsonValue,
    Segment,
    UtcTimestamp,
    Uuid7,
    WireModel,
)

# Data-owned interval record, annotation-only for readers, but Pydantic
# resolves it at class-creation time, so it must remain a runtime import.
from app.contracts.data.models import SeriesInterval  # noqa: TC001

# Strategy-owned AST wire records, annotation-only for readers, but Pydantic
# resolves them at class-creation time, so they must remain runtime imports.
from app.contracts.strategy.models import (  # noqa: TC001
    StrategyAst,
    StrategyValidationReport,
)

# Constrained local string alias reused across research records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Closed research-run lifecycle enum shared by ResearchRunRef and
# ResearchStatus. This is intentionally not the kernel JobState union: research
# runs never expose LEASED/PAUSING/RESUMING job-scheduler internals.
type ResearchRunState = Literal[
    "QUEUED",
    "RUNNING",
    "PAUSED",
    "STOPPING",
    "STOPPED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]

# Closed Monte Carlo perturbation-method enum from the ratified RobustnessPlan.
type MonteCarloMethod = Literal[
    "REORDER",
    "SKIP",
    "PL_PERTURB",
    "TRADE_COST_PERTURB",
    "PARAMETER",
    "DATA",
    "SPREAD",
    "SLIPPAGE",
    "EXECUTION_DELAY",
]


class MarketMatrixCell(WireModel):
    """One pinned market/broker/data-version cell of a retest market matrix."""

    market: InstrumentRef
    broker: BrokerRef | None
    data_version_id: Uuid7


class MonteCarloSpec(WireModel):
    """Seeded Monte Carlo perturbation specification of a robustness plan."""

    methods: tuple[MonteCarloMethod, ...]
    distributions: JsonObject
    seeds: tuple[NonEmptyStr, ...]
    sample_count: int = Field(ge=1)
    percentile_method: NonEmptyStr
    confidence: DecimalValue
    failure_handling: NonEmptyStr
    acceptance_rule: NonEmptyStr

    @model_validator(mode="after")
    def validate_confidence(self) -> MonteCarloSpec:
        """Reject confidence levels outside the exclusive interval (0, 1).

        Returns:
            The validated specification.

        Raises:
            ValueError: ``confidence`` is not strictly between 0 and 1.
        """
        # The ratified rule is the open interval (0, 1): neither a degenerate
        # 0% nor 100% confidence is an admissible Monte Carlo level.
        confidence = Decimal(self.confidence)
        if not Decimal(0) < confidence < Decimal(1):
            raise ValueError("confidence must be within the open interval (0, 1)")
        return self


class SpaceDimension(WireModel):
    """One named dimension of a parameter space."""

    name: NonEmptyStr
    domain: Literal["FIXED", "DISCRETE", "RANGE_STEP", "GRID", "WEIGHTED"]
    values: tuple[JsonValue, ...] = ()
    range_min: DecimalValue | None
    range_max: DecimalValue | None
    step: DecimalValue | None

    @model_validator(mode="after")
    def validate_step(self) -> SpaceDimension:
        """Reject nonpositive range steps.

        Returns:
            The validated dimension.

        Raises:
            ValueError: ``step`` is present and not strictly positive.
        """
        if self.step is not None and Decimal(self.step) <= 0:
            raise ValueError("step must be positive")
        return self


class RobustnessSimulation(WireModel):
    """One ordinal robustness simulation sample or its structured failure."""

    ordinal: int = Field(ge=1)
    method: NonEmptyStr
    sampled_values: JsonObject
    source_stream: NonEmptyStr
    result_id: Uuid7 | None
    failure: NonEmptyStr | None = None


class SequentialStage(WireModel):
    """One sequential optimization stage over one parameter."""

    parameter_name: NonEmptyStr
    objective: NonEmptyStr
    retained_values: int = Field(ge=1)
    stopping_rule: NonEmptyStr
    tie_breaker: NonEmptyStr


class AcceptanceStage(WireModel):
    """One ordered stage of a research acceptance pipeline."""

    stage: NonEmptyStr
    rule: NonEmptyStr
    rule_version: int = Field(ge=1)
    budget: JsonObject
    concurrency: int = Field(ge=1)
    stop_on_failure: bool


class ResearchBudget(WireModel):
    """Bound set enforced by research budget governance.

    Public record R18, defined ahead of the table order because
    ``ResearchManifest`` (R2) embeds it; every bound left ``None`` is
    unbounded, and bound exhaustion is a runtime policy, not a record rule.
    """

    budget_id: Uuid7
    max_candidates: int | None = Field(default=None, ge=1)
    max_evaluations: int | None = Field(default=None, ge=1)
    max_elapsed_seconds: int | None = Field(default=None, ge=1)
    max_cpu_seconds: int | None = Field(default=None, ge=1)
    max_memory_mb: int | None = Field(default=None, ge=1)
    max_artifact_storage_mb: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1


class ResearchRunRef(WireModel):
    """Reference to one controllable research run execution (R1).

    Start/pause/resume/stop/cancel/status commands are idempotent; repeated
    commands create one effective transition. That runtime contract is
    enforced by the owning feature, not by this record.
    """

    run_id: Uuid7
    job_id: Uuid7
    manifest_id: Uuid7
    method: NonEmptyStr
    state: ResearchRunState
    derived_from_run_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class ResearchManifest(WireModel):
    """Immutable pinned inputs of one research execution request (R2).

    Equivalent requests from every entry point produce one manifest
    ``content_hash``; the approved preview hash must match at admission.
    """

    manifest_id: Uuid7
    method: NonEmptyStr
    method_version: int = Field(ge=1)
    # Simulator run-manifest identifiers for member backtests.
    run_manifest_ids: tuple[Uuid7, ...] = ()
    capability_snapshot_id: Uuid7
    inputs: JsonObject
    estimated_resource_use: JsonObject = Field(default_factory=dict)
    seed_set: tuple[NonEmptyStr, ...] = ()
    budgets: ResearchBudget
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ResearchStatus(WireModel):
    """Bounded observational progress snapshot of one research run (R3).

    Failed runs retain the classified error, checkpoint sequence, committed
    partial artifacts, and retry eligibility so failure pages never require
    log parsing.
    """

    run_id: Uuid7
    state: ResearchRunState
    processed_units: int = Field(default=0, ge=0)
    total_units: int | None = Field(default=None, ge=0)
    simulation_time: UtcTimestamp | None = None
    speed_units_per_second: DecimalValue | None = None
    elapsed_seconds: int = Field(default=0, ge=0)
    estimated_remaining_seconds: int | None = Field(default=None, ge=0)
    memory_mb: int | None = Field(default=None, ge=0)
    warnings: tuple[NonEmptyStr, ...] = ()
    accepted_artifact_ids: tuple[Uuid7, ...] = ()
    checkpoint_sequence: int = Field(default=0, ge=0)
    classified_error: NonEmptyStr | None = None
    retry_eligible: bool = False
    committed_partial_artifact_ids: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class RobustnessPlan(WireModel):
    """Pinned retest and robustness execution plan (R4).

    Input membership cannot change mid-run, every candidate yields an
    accepted result or a structured rejection, and simulation ordinal 0
    reproduces the baseline; those are runtime contracts of the owning
    feature.
    """

    plan_id: Uuid7
    strategy_version_ids: tuple[Uuid7, ...] = Field(min_length=1)
    retest_profile_version: int = Field(ge=1)
    precision_upgrade: Literal["NONE", "DECLARED"] = "NONE"
    market_matrix: tuple[MarketMatrixCell, ...] = ()
    aggregation_policy: NonEmptyStr
    monte_carlo: MonteCarloSpec | None = None
    # Strategy-owned ParameterDefinition reference. ParameterDefinition has
    # no UUID identity, so domains reference parameters by name.
    permutation_domains: tuple[str, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class RobustnessResult(WireModel):
    """Aggregated robustness simulation outcomes for one plan (R5)."""

    result_id: Uuid7
    plan_id: Uuid7
    simulations: tuple[RobustnessSimulation, ...] = ()
    percentiles: JsonObject
    divergence_first_event: JsonObject | None = None
    scenario_variants: tuple[Uuid7, ...] = ()
    permutation_coverage: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ParameterSpace(WireModel):
    """Named multi-dimensional optimization parameter space (R6)."""

    space_id: Uuid7
    parameters: tuple[SpaceDimension, ...] = Field(min_length=1)
    cardinality: int | None = Field(default=None, ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class OptimizationPlan(WireModel):
    """Admitted parameter-optimization plan (R7).

    Admission reports the projected evaluation count and storage; over-policy
    domains reject unless budget-limited, duplicate vectors execute at most
    once per compatible manifest, and replay selects the same final vector.
    """

    plan_id: Uuid7
    mode: Literal["SIMPLE", "GRID", "SEQUENTIAL"]
    parameter_space: ParameterSpace
    objective: NonEmptyStr
    objective_version: int = Field(ge=1)
    stages: tuple[SequentialStage, ...] = ()
    projected_evaluations: int = Field(ge=1)
    estimated_storage_mb: int = Field(default=0, ge=0)
    budget_limit: bool = False
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class OptimizationVariant(WireModel):
    """One evaluated parameter vector of an optimization run (R8)."""

    variant_id: Uuid7
    run_id: Uuid7
    combination_index: int = Field(ge=1)
    parameter_vector: JsonObject
    vector_hash: ContentHash
    result_id: Uuid7 | None = None
    objective_values: dict[NonEmptyStr, DecimalValue] = Field(default_factory=dict)
    is_feasible: bool = True
    rank: int | None = Field(default=None, ge=1)
    pareto_status: Literal["DOMINATED", "NON_DOMINATED", "UNRANKED"] = "UNRANKED"
    schema_version: Literal[1] = 1


class OptimizationResult(WireModel):
    """Ranked variants and selection of one optimization run (R9)."""

    result_id: Uuid7
    plan_id: Uuid7
    run_id: Uuid7
    variants: tuple[OptimizationVariant, ...] = ()
    selected_variant_id: Uuid7 | None = None
    evaluated_count: int = Field(ge=0)
    domain_cardinality: int | None = Field(default=None, ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class WalkForwardPlan(WireModel):
    """Walk-forward window scheme and evaluation policy (R10).

    No timestamp overlap violating the scheme and selection-only data
    visibility are runtime contracts enforced while windows execute.
    """

    plan_id: Uuid7
    scheme: Literal["ANCHORED", "ROLLING"]
    window_config: JsonObject
    train_interval: SeriesInterval
    selection_interval: SeriesInterval
    oos_interval: SeriesInterval
    stitch_policy: NonEmptyStr
    matrix: tuple[JsonObject, ...] = ()
    score: NonEmptyStr
    score_version: int = Field(ge=1)
    tie_breaker: NonEmptyStr
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class WalkForwardWindow(WireModel):
    """One train/selection/out-of-sample window of a walk-forward run (R11).

    Every OOS segment links to exactly one selection decision and its inputs;
    failed cells remain visible through ``failed_cell_reason``.
    """

    window_id: Uuid7
    run_id: Uuid7
    ordinal: int = Field(ge=1)
    train_from: UtcTimestamp
    train_to: UtcTimestamp
    selection_from: UtcTimestamp
    selection_to: UtcTimestamp
    oos_from: UtcTimestamp
    oos_to: UtcTimestamp
    is_metrics: JsonObject
    selected_variant_id: Uuid7
    oos_result_id: Uuid7 | None = None
    eligible_days: JsonObject
    failed_cell_reason: NonEmptyStr | None = None
    schema_version: Literal[1] = 1


class WalkForwardResult(WireModel):
    """Stitched walk-forward windows and aggregate metrics (R12)."""

    result_id: Uuid7
    plan_id: Uuid7
    run_id: Uuid7
    windows: tuple[WalkForwardWindow, ...] = ()
    stitched_equity_artifact_id: Uuid7 | None = None
    wf_metrics: dict[NonEmptyStr, DecimalValue | None] = Field(default_factory=dict)
    matrix_ranking: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class BuilderPlan(WireModel):
    """Reproducible Builder strategy-generation search manifest (R13).

    The complete search is reproducible from this one manifest; only
    type-valid strategies satisfying grammar, resource, complexity, and
    required-block constraints are emitted, and semantic duplicates are
    detected by normalized fingerprints with a declared collision policy.
    """

    plan_id: Uuid7
    block_registry_version: int = Field(ge=1)
    block_weights: JsonObject
    # Strategy-owned ParameterDefinition reference. ParameterDefinition has
    # no UUID identity, so domains reference parameters by name.
    parameter_domains: tuple[str, ...]
    # Strategy-owned strategy-template identity; TemplatePlaceholder itself
    # stays owned by app/contracts/strategy/ and is not redefined here.
    template_id: Uuid7 | None
    random_group_version_ids: tuple[Uuid7, ...] = ()
    evolution_policy: Literal["STRICT_GROUPS", "REFERENCE_RELAXED"] | None = None
    direction: Direction
    markets: tuple[MarketMatrixCell, ...]
    engine_profile_id: Uuid7
    filters: JsonObject
    seeds: tuple[NonEmptyStr, ...]
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class StrategyCandidate(WireModel):
    """One generated or evolved strategy candidate with exact lineage (R14)."""

    candidate_id: Uuid7
    run_id: Uuid7
    strategy_version_id: Uuid7
    result_id: Uuid7 | None = None
    fingerprint: ContentHash
    edit_operations: tuple[JsonObject, ...] = ()
    parent_strategy_version_id: Uuid7 | None = None
    atm_only_mutation: bool = False
    schema_version: Literal[1] = 1


class EvolutionPlan(WireModel):
    """Genetic-evolution configuration with checkpointable RNG streams (R15).

    Checkpoints contain generation/island populations, fitness, the duplicate
    index, counters, and every named RNG stream state; resuming after each
    checkpoint reproduces identical evolution.
    """

    plan_id: Uuid7
    population_size: int = Field(ge=1)
    islands: int = Field(ge=1)
    initialization: JsonObject
    fitness: NonEmptyStr
    fitness_version: int = Field(ge=1)
    selection: JsonObject
    crossover: JsonObject
    mutation: JsonObject
    elitism: JsonObject
    migration: JsonObject
    restart: JsonObject
    decimation: JsonObject
    fresh_blood: JsonObject
    termination: JsonObject
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class AcceptancePipeline(WireModel):
    """Ordered acceptance pipeline definition (R16).

    Higher-cost stages receive only candidates allowed by earlier stages.
    """

    pipeline_id: Uuid7
    version: int = Field(ge=1)
    stages: tuple[AcceptanceStage, ...] = Field(min_length=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class AcceptanceDecision(WireModel):
    """One stage outcome of one candidate against one pipeline (R17).

    Rejection totals reconcile exactly with candidate counts in the owning
    store.
    """

    decision_id: Uuid7
    candidate_id: Uuid7
    pipeline_id: Uuid7
    stage: NonEmptyStr
    rule: NonEmptyStr
    rule_version: int = Field(ge=1)
    observed_value: DecimalValue | None
    threshold: DecimalValue | None
    segment: Segment
    direction: Direction
    outcome: Literal["PASSED", "REJECTED"]
    diagnostic_context: JsonObject = Field(default_factory=dict)
    schema_version: Literal[1] = 1


class PromotionDecision(WireModel):
    """Immutable promotion of one candidate into a new strategy version (R19).

    Promotion creates a new immutable strategy version linked to its source
    candidate and result; it never overwrites parents, so lineage stays
    traversable afterwards.
    """

    decision_id: Uuid7
    candidate_id: Uuid7
    selected_result_id: Uuid7
    new_strategy_version_id: Uuid7
    promoted_at: UtcTimestamp
    schema_version: Literal[1] = 1


class StockpickerResearchPlan(WireModel):
    """Point-in-time stockpicker research plan (R20).

    Repeated runs select identical historical constituents.
    """

    plan_id: Uuid7
    universe: UniverseRef
    universe_version: int = Field(ge=1)
    ranking_expression: NonEmptyStr
    rebalance_schedule: NonEmptyStr
    selection_count: int = Field(ge=1)
    allocation_policy: JsonObject
    cost_policy: JsonObject
    validation_partitions: tuple[SeriesInterval, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class AiResearchDraft(WireModel):
    """Redacted AI-drafted strategy proposal (R21, experimental).

    Proposed ASTs pass the same registry/schema validation as the editor and
    are never executable by themselves; AI inputs are minimized and redacted,
    and disabling the adapter leaves all stable workflows functional.
    """

    draft_id: Uuid7
    input_hash: ContentHash
    provider_request_id: NonEmptyStr
    adapter: NonEmptyStr
    model: NonEmptyStr
    redacted_input: JsonObject
    # Strategy-owned StrategyAst and StrategyValidationReport wire objects.
    proposed_ast: StrategyAst | None = None
    validation: StrategyValidationReport | None = None
    proposal_state: Literal["PROPOSED", "VALIDATED", "REJECTED", "APPROVED"]
    schema_version: Literal[1] = 1


class AiImprovementProposal(WireModel):
    """Governed AI improvement proposal over one parent strategy (R22).

    Experimental: proposals may not run, promote, overwrite, or delete
    strategies without an explicit approved research action.
    """

    proposal_id: Uuid7
    draft_id: Uuid7
    parent_strategy_version_id: Uuid7
    edit_operations: tuple[JsonObject, ...] = Field(min_length=1)
    proposal_state: Literal["PROPOSED", "REJECTED", "APPROVED"]
    schema_version: Literal[1] = 1


class NeuralResearchPlan(WireModel):
    """Neural research training/inference artifact plan (R23, experimental)."""

    plan_id: Uuid7
    trainer_artifact_id: Uuid7
    inference_artifact_id: Uuid7 | None = None
    hyperparameters: JsonObject
    seeds: tuple[NonEmptyStr, ...]
    feature_refs: tuple[Uuid7, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PortfolioFitnessScore(WireModel):
    """Portfolio-aware Builder fitness score of one candidate (R24).

    Phase 3 Builder option; only a caller-supplied immutable pinned portfolio
    version is accepted, so Research never depends on Portfolio runtime.
    """

    score_id: Uuid7
    candidate_strategy_version_id: Uuid7
    existing_portfolio_version_id: Uuid7
    snapshot_mode: Literal["SNAPSHOT", "REFERENCE"]
    combined_result_id: Uuid7
    fitness: DecimalValue
    fitness_version: int = Field(ge=1)
    score_components: JsonObject
    schema_version: Literal[1] = 1


class MarketIntelligenceObservation(WireModel):
    """Immutable point-in-time market intelligence study output (R25).

    Consumes only Data-owned point-in-time evidence; descriptive evidence is
    distinguished from executable rules through versioned definitions.
    """

    observation_id: Uuid7
    study_kind: Literal["FUNDAMENTAL", "SENTIMENT", "SEASONALITY", "MARKET_STRUCTURE"]
    source_refs: tuple[Uuid7, ...]
    visibility_time: UtcTimestamp
    revision_policy: NonEmptyStr
    entity_instrument_mapping: JsonObject
    language_model_version: str | None = None
    missingness_policy: NonEmptyStr
    multiple_comparison_correction: str | None = None
    definitions: JsonObject = Field(default_factory=dict)
    outputs_artifact_id: Uuid7
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DriftState(WireModel):
    """Advisory drift classification of one subject at one instant (R26).

    Advisory until a separate acceptance or Risk policy consumes it.
    """

    evaluation_id: Uuid7
    subject: Uuid7
    state: Literal[
        "STABLE",
        "WATCH",
        "DEGRADED",
        "BREACHED",
        "INSUFFICIENT_EVIDENCE",
        "INVALID_COMPARISON",
    ]
    as_of: UtcTimestamp
    schema_version: Literal[1] = 1


class DriftReport(WireModel):
    """Pinned expectancy versus later evidence drift report (R27)."""

    report_id: Uuid7
    subject: Uuid7
    reference_profile_id: Uuid7
    metric: NonEmptyStr
    window: SeriesInterval
    baseline: DecimalValue | None
    observed: DecimalValue | None
    threshold: DecimalValue | None
    uncertainty: DecimalValue | None
    missing_data_policy: NonEmptyStr
    state: DriftState
    lineage: JsonObject
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class RunResearchRequest(WireModel):
    """Operation-discriminated manual research run request.

    The ratified v1 envelope spells only the operation set; per-operation
    request payloads beyond the common fields remain owned by the feature
    admission rules rather than this frozen wire record.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "PREVIEW",
        "START",
        "PAUSE",
        "RESUME",
        "STOP",
        "CANCEL",
        "STATUS",
        "COMMIT",
        "DUPLICATE",
        "SUBMIT_BATCH",
    ]
    schema_version: Literal[1] = 1


class RunResearchSuccess(WireModel):
    """Successful manual research run operation result."""

    request_id: Uuid7
    manifest: ResearchManifest | None = None
    run: ResearchRunRef | None = None
    status: ResearchStatus | None = None
    committed_result_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class TestRobustnessRequest(WireModel):
    """Operation-discriminated retest and robustness request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "PLAN",
        "EXECUTE",
        "SUMMARIZE",
        "RUN_SCENARIO",
        "PERMUTE_SYSTEM",
    ]
    schema_version: Literal[1] = 1


class TestRobustnessSuccess(WireModel):
    """Successful retest and robustness operation result."""

    request_id: Uuid7
    plan: RobustnessPlan | None = None
    result: RobustnessResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class OptimizeParametersRequest(WireModel):
    """Operation-discriminated parameter optimization request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "EXECUTE"]
    schema_version: Literal[1] = 1


class OptimizeParametersSuccess(WireModel):
    """Successful parameter optimization operation result."""

    request_id: Uuid7
    plan: OptimizationPlan | None = None
    result: OptimizationResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ValidateWalkForwardRequest(WireModel):
    """Operation-discriminated walk-forward research request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "EXECUTE", "EVALUATE_MATRIX"]
    schema_version: Literal[1] = 1


class ValidateWalkForwardSuccess(WireModel):
    """Successful walk-forward research operation result."""

    request_id: Uuid7
    plan: WalkForwardPlan | None = None
    result: WalkForwardResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GenerateStrategiesRequest(WireModel):
    """Operation-discriminated Builder generation request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "GENERATE", "CALIBRATE", "DETECT_DUPLICATES"]
    schema_version: Literal[1] = 1


class GenerateStrategiesSuccess(WireModel):
    """Successful Builder generation operation result."""

    request_id: Uuid7
    plan: BuilderPlan | None = None
    candidates: tuple[StrategyCandidate, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class EvolveStrategiesRequest(WireModel):
    """Operation-discriminated Improver and genetic evolution request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "EVOLVE", "CHECKPOINT", "RESUME", "IMPROVE"]
    schema_version: Literal[1] = 1


class EvolveStrategiesSuccess(WireModel):
    """Successful Improver and genetic evolution operation result."""

    request_id: Uuid7
    plan: EvolutionPlan | None = None
    candidates: tuple[StrategyCandidate, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AcceptResearchRequest(WireModel):
    """Operation-discriminated acceptance pipeline request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_PIPELINE", "EVALUATE", "PROMOTE"]
    schema_version: Literal[1] = 1


class AcceptResearchSuccess(WireModel):
    """Successful acceptance pipeline operation result."""

    request_id: Uuid7
    pipeline: AcceptancePipeline | None = None
    decision: AcceptanceDecision | None = None
    promotion: PromotionDecision | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GovernResearchBudgetsRequest(WireModel):
    """Operation-discriminated research budget governance request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE", "CHECK", "ENFORCE"]
    schema_version: Literal[1] = 1


class GovernResearchBudgetsSuccess(WireModel):
    """Successful research budget governance operation result."""

    request_id: Uuid7
    budget: ResearchBudget | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ResearchStockpickersRequest(WireModel):
    """Operation-discriminated stockpicker research request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "EXECUTE"]
    schema_version: Literal[1] = 1


class ResearchStockpickersSuccess(WireModel):
    """Successful stockpicker research operation result."""

    request_id: Uuid7
    plan: StockpickerResearchPlan | None = None
    result_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AssistResearchAiRequest(WireModel):
    """Operation-discriminated AI-assisted research request.

    Experimental gating: an external AI failure never impairs non-AI
    workflows.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DRAFT", "VALIDATE_DRAFT", "PROPOSE_IMPROVEMENT"]
    schema_version: Literal[1] = 1


class AssistResearchAiSuccess(WireModel):
    """Successful AI-assisted research operation result."""

    request_id: Uuid7
    draft: AiResearchDraft | None = None
    proposal: AiImprovementProposal | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ResearchNeuralModelsRequest(WireModel):
    """Operation-discriminated neural research request (experimental)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "TRAIN"]
    schema_version: Literal[1] = 1


class ResearchNeuralModelsSuccess(WireModel):
    """Successful neural research operation result."""

    request_id: Uuid7
    plan: NeuralResearchPlan | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ScorePortfolioFitnessRequest(WireModel):
    """Operation-discriminated portfolio-aware fitness request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["SCORE"]
    schema_version: Literal[1] = 1


class ScorePortfolioFitnessSuccess(WireModel):
    """Successful portfolio-aware fitness operation result."""

    request_id: Uuid7
    score: PortfolioFitnessScore | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class MonitorMarketDriftRequest(WireModel):
    """Operation-discriminated market intelligence and drift request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["OBSERVE", "EVALUATE_DRIFT"]
    schema_version: Literal[1] = 1


class MonitorMarketDriftSuccess(WireModel):
    """Successful market intelligence and drift operation result."""

    request_id: Uuid7
    observation: MarketIntelligenceObservation | None = None
    report: DriftReport | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# The inline nested records spelled inside table rows (MarketMatrixCell,
# MonteCarloSpec, SpaceDimension, RobustnessSimulation,
# SequentialStage, and AcceptanceStage) are structural components of the 27
# registered public records, not numbered public records themselves, so they
# are not registered in WIRE_MODELS.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "ResearchRunRef": ResearchRunRef,
    "ResearchManifest": ResearchManifest,
    "ResearchStatus": ResearchStatus,
    "RobustnessPlan": RobustnessPlan,
    "RobustnessResult": RobustnessResult,
    "ParameterSpace": ParameterSpace,
    "OptimizationPlan": OptimizationPlan,
    "OptimizationVariant": OptimizationVariant,
    "OptimizationResult": OptimizationResult,
    "WalkForwardPlan": WalkForwardPlan,
    "WalkForwardWindow": WalkForwardWindow,
    "WalkForwardResult": WalkForwardResult,
    "BuilderPlan": BuilderPlan,
    "StrategyCandidate": StrategyCandidate,
    "EvolutionPlan": EvolutionPlan,
    "AcceptancePipeline": AcceptancePipeline,
    "AcceptanceDecision": AcceptanceDecision,
    "ResearchBudget": ResearchBudget,
    "PromotionDecision": PromotionDecision,
    "StockpickerResearchPlan": StockpickerResearchPlan,
    "AiResearchDraft": AiResearchDraft,
    "AiImprovementProposal": AiImprovementProposal,
    "NeuralResearchPlan": NeuralResearchPlan,
    "PortfolioFitnessScore": PortfolioFitnessScore,
    "MarketIntelligenceObservation": MarketIntelligenceObservation,
    "DriftState": DriftState,
    "DriftReport": DriftReport,
    "RunResearchRequest": RunResearchRequest,
    "RunResearchSuccess": RunResearchSuccess,
    "TestRobustnessRequest": TestRobustnessRequest,
    "TestRobustnessSuccess": TestRobustnessSuccess,
    "OptimizeParametersRequest": OptimizeParametersRequest,
    "OptimizeParametersSuccess": OptimizeParametersSuccess,
    "ValidateWalkForwardRequest": ValidateWalkForwardRequest,
    "ValidateWalkForwardSuccess": ValidateWalkForwardSuccess,
    "GenerateStrategiesRequest": GenerateStrategiesRequest,
    "GenerateStrategiesSuccess": GenerateStrategiesSuccess,
    "EvolveStrategiesRequest": EvolveStrategiesRequest,
    "EvolveStrategiesSuccess": EvolveStrategiesSuccess,
    "AcceptResearchRequest": AcceptResearchRequest,
    "AcceptResearchSuccess": AcceptResearchSuccess,
    "GovernResearchBudgetsRequest": GovernResearchBudgetsRequest,
    "GovernResearchBudgetsSuccess": GovernResearchBudgetsSuccess,
    "ResearchStockpickersRequest": ResearchStockpickersRequest,
    "ResearchStockpickersSuccess": ResearchStockpickersSuccess,
    "AssistResearchAiRequest": AssistResearchAiRequest,
    "AssistResearchAiSuccess": AssistResearchAiSuccess,
    "ResearchNeuralModelsRequest": ResearchNeuralModelsRequest,
    "ResearchNeuralModelsSuccess": ResearchNeuralModelsSuccess,
    "ScorePortfolioFitnessRequest": ScorePortfolioFitnessRequest,
    "ScorePortfolioFitnessSuccess": ScorePortfolioFitnessSuccess,
    "MonitorMarketDriftRequest": MonitorMarketDriftRequest,
    "MonitorMarketDriftSuccess": MonitorMarketDriftSuccess,
}
