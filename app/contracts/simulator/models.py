"""Strict Pydantic v2 wire records for the ratified Simulator v1 contracts."""

from decimal import Decimal
from fractions import Fraction
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# Pydantic resolves this cross-owner record at class-creation time, so the
# import must remain at runtime despite being annotation-only for readers.
from app.contracts.catalogue.models import UniverseRef  # noqa: TC001
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    DecimalValue,
    JobState,
    JsonObject,
    Money,
    OrderState,
    OrderType,
    Precision,
    ResultState,
    Segment,
    Side,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Constrained local string aliases reused across simulator records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: a seed root is an opaque nonempty hexadecimal string.
# Unlike canonical digests, both letter cases are accepted.
type HexSeed = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]+$")]
# Artifact checksum dictionary keys are nonempty artifact names.
type ArtifactKey = Annotated[str, StringConstraints(min_length=1)]

# Closed enums from the ratified Simulator v1 public records.
type ManifestState = Literal["VALIDATING", "COMMITTED"]
type TargetRuntime = Literal["MT5", "MT4", "TRADESTATION", "MULTICHARTS", "JFOREX"]
type PositionModel = Literal["ONE_POSITION", "HEDGING", "NETTING"]
type SpreadPolicy = Literal["OHLC_CONSTRUCTED", "CUSTOM", "RECORDED"]
type MissingSidePolicy = Literal["REJECT", "SYNTHESIZE_FORBIDDEN"]
# Positions and trades carry realized directions only; the shared Direction
# literal's BOTH value is a strategy-side policy, never a position direction.
type PositionDirection = Literal["LONG", "SHORT"]
type PositionState = Literal["OPEN", "CLOSED"]
type CloseReason = Literal[
    "STOP",
    "TARGET",
    "TRAILING",
    "BREAKEVEN",
    "BARS",
    "RULE",
    "EOD",
    "FRIDAY",
    "SIGNAL",
    "END_OF_DATA",
    "CANCELLED",
]
type ExitKind = Literal[
    "STOP",
    "TARGET",
    "TRAILING",
    "BREAKEVEN",
    "BARS",
    "RULE",
    "EOD",
    "FRIDAY",
]
type MissingValuePolicy = Literal["BLOCK", "NULL_VALUE"]
type IndicatorStateScope = Literal["STRATEGY_INSTANCE", "CHART"]
type ResultCompletion = Literal["COMPLETE", "INCOMPLETE"]
type PerturbationKind = Literal[
    "COST", "DATA", "PARAMETER", "EXECUTION_DELAY", "TRADE_SEQUENCE"
]
type StockpickerEvaluationTiming = Literal["BEFORE_OPEN", "ON_OPEN", "ON_CLOSE"]

# Inclusive upper bound of the volume-profile value-area percentage; the
# ratified range is the half-open interval (0, 100].
_VALUE_AREA_PERCENT_MAX = Decimal(100)


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


class ProviderPin(WireModel):
    """One pinned behavior provider binding of a run manifest."""

    capability_key: CapabilityIdentifier
    version: int = Field(ge=1)
    implementation_hash: ContentHash


class CostBreakdown(WireModel):
    """Exact trading-cost decomposition of one simulated trade.

    The six cost components must sum exactly to ``net_pl``.
    """

    price_pl: Money
    spread_effect: Money
    slippage_effect: Money
    commission: Money
    swap: Money
    conversion_adjustment: Money
    net_pl: Money
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_component_sum(self) -> CostBreakdown:
        """Reject component sets that do not sum exactly to ``net_pl``.

        Returns:
            The validated cost breakdown.

        Raises:
            ValueError: The canonical sum of the six cost components
                differs from ``net_pl``.
        """
        # Fraction arithmetic over finite decimals is exact, so the ratified
        # "components sum exactly to net_pl" rule never suffers
        # decimal-context rounding.
        total = Fraction(0)
        for component in (
            self.price_pl,
            self.spread_effect,
            self.slippage_effect,
            self.commission,
            self.swap,
            self.conversion_adjustment,
        ):
            total += Fraction(Decimal(component.amount))
        if total != Fraction(Decimal(self.net_pl.amount)):
            raise ValueError("cost components must sum exactly to net_pl")
        return self


class ResultSegment(WireModel):
    """One half-open result segment with its trade-admission policies.

    ``FULL`` segments may overlap other segments; every other segment is
    disjoint and boundary events belong to exactly one segment. No-trade
    zones prohibit new or scale-in exposure while exits stay active.
    """

    segment_id: Uuid7
    result_id: Uuid7
    segment: Segment
    from_at: UtcTimestamp
    to_at: UtcTimestamp
    entry_policy: NonEmptyStr
    exit_policy: NonEmptyStr
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_interval(self) -> ResultSegment:
        """Reject inverted segment intervals.

        UtcTimestamp strings use one fixed-width format, so lexicographic
        order equals chronological order.

        Returns:
            The validated result segment.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class RunManifest(WireModel):
    """Immutable pinned-input manifest of one deterministic simulation run.

    The manifest is created atomically with its queued job after validation,
    is immutable after commit, and comparing two manifests reports every
    material input difference.
    """

    manifest_id: Uuid7
    job_id: Uuid7
    capability_snapshot_id: Uuid7
    snapshot_hash: ContentHash
    behavior_providers: tuple[ProviderPin, ...] = Field(min_length=1)
    engine_profile_id: Uuid7
    engine_profile_version: int = Field(ge=1)
    strategy_version_id: Uuid7
    strategy_hash: ContentHash
    settings_hash: ContentHash
    data_binding_id: Uuid7
    catalogue_version_ids: tuple[Uuid7, ...] = ()
    block_version_hashes: tuple[ContentHash, ...] = ()
    seed_root: HexSeed
    seed_streams: tuple[NonEmptyStr, ...] = ()
    environment: NonEmptyStr
    segments: tuple[ResultSegment, ...] = ()
    output_artifact_ids: tuple[Uuid7, ...] = ()
    state: ManifestState
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class EngineProfileVersion(WireModel):
    """One immutable version of a target-runtime engine profile.

    A run cannot start when any declared semantic is absent from the
    profile.
    """

    profile_id: Uuid7
    version: int = Field(ge=1)
    target_runtime: TargetRuntime
    target_version_range: NonEmptyStr
    signal_evaluation_timing: NonEmptyStr
    order_activation_timing: NonEmptyStr
    same_bar_policy: NonEmptyStr
    gap_policy: NonEmptyStr
    fill_priority: NonEmptyStr
    position_model: PositionModel
    rounding_policy: NonEmptyStr
    session_policy: NonEmptyStr
    collision_policy: NonEmptyStr
    cost_policy: NonEmptyStr
    capability_matrix: tuple[CapabilityIdentifier, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PrecisionModel(WireModel):
    """One declared simulation precision mode and its spread semantics.

    Recorded-spread mode never synthesizes the ask side.
    """

    precision: Precision
    intrabar_path_policy: NonEmptyStr
    spread_policy: SpreadPolicy
    missing_side_policy: MissingSidePolicy = "REJECT"
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_recorded_spread(self) -> PrecisionModel:
        """Reject recorded-spread models that would synthesize a side.

        Returns:
            The validated precision model.

        Raises:
            ValueError: ``spread_policy`` is RECORDED while
                ``missing_side_policy`` is not REJECT.
        """
        if self.spread_policy == "RECORDED" and self.missing_side_policy != "REJECT":
            raise ValueError("recorded-spread mode never synthesizes the ask side")
        return self


class SimulationRequest(WireModel):
    """One admitted backtest request with idempotent submission semantics.

    Repeating a request with the same idempotency key returns the original
    job; no duplicate is queued.
    """

    request_id: Uuid7
    strategy_version_id: Uuid7
    engine_profile_id: Uuid7
    settings: JsonObject
    data_binding_id: Uuid7
    seed_root: HexSeed
    seed_streams: tuple[NonEmptyStr, ...] = ()
    idempotency_key: NonEmptyStr
    priority: int = Field(default=0, ge=0)
    schema_version: Literal[1] = 1


class SimulationRunRef(WireModel):
    """One live reference to a simulation job's effective lifecycle state.

    Terminal states are immutable and repeated commands return the
    effective state.
    """

    run_id: Uuid7
    job_id: Uuid7
    manifest_id: Uuid7
    state: JobState
    progress: DecimalValue = "0"
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_progress(self) -> SimulationRunRef:
        """Reject progress fractions outside the closed interval [0, 1].

        Returns:
            The validated run reference.

        Raises:
            ValueError: ``progress`` is below 0 or above 1.
        """
        progress = Decimal(self.progress)
        if progress < 0 or progress > 1:
            raise ValueError("progress must be within [0, 1]")
        return self


class SimOrder(WireModel):
    """One simulated order with its execution state.

    Filled quantity is monotonic and never exceeds the requested quantity;
    stop-limit orders keep distinct trigger and limit phases.
    """

    order_id: Uuid7
    result_id: Uuid7
    order_sequence: int = Field(ge=0)
    entry_id: Uuid7 | None = None
    order_group_id: Uuid7 | None = None
    magic_number: int | None = Field(default=None, ge=0)
    symbol: NonEmptyStr
    order_type: OrderType
    side: Side
    requested_quantity: DecimalValue
    requested_price: DecimalValue | None = None
    stop_price: DecimalValue | None = None
    limit_price: DecimalValue | None = None
    protection_owner_id: Uuid7 | None = None
    activation: UtcTimestamp | None = None
    expiry: UtcTimestamp | None = None
    state: OrderState
    filled_quantity: DecimalValue = "0"
    reason: str = ""
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_order_semantics(self) -> SimOrder:
        """Reject invalid quantities and stop-limit phase collisions.

        Returns:
            The validated simulated order.

        Raises:
            ValueError: The requested or filled quantity violates its
                ratified range, the filled quantity exceeds the requested
                quantity, or a STOP_LIMIT order lacks distinct trigger and
                limit prices.
        """
        if Decimal(self.requested_quantity) <= 0:
            raise ValueError("requested_quantity must be positive")
        if Decimal(self.filled_quantity) < 0:
            raise ValueError("filled_quantity must be >= 0")
        if Decimal(self.filled_quantity) > Decimal(self.requested_quantity):
            raise ValueError("filled_quantity must not exceed requested_quantity")
        if self.order_type == "STOP_LIMIT":
            if self.stop_price is None or self.limit_price is None:
                raise ValueError("STOP_LIMIT requires stop_price and limit_price")
            if self.stop_price == self.limit_price:
                raise ValueError("STOP_LIMIT requires distinct stop and limit prices")
        return self


class SimFill(WireModel):
    """One simulated fill with its seeded price composition.

    Seeded randomized slippage reproduces identically across repeated runs
    on one manifest.
    """

    fill_id: Uuid7
    order_id: Uuid7
    fill_sequence: int = Field(ge=0)
    timestamp: UtcTimestamp
    side: Side
    quantity: DecimalValue
    base_price: DecimalValue
    spread_price: DecimalValue
    slippage: DecimalValue
    final_price: DecimalValue
    slippage_seed: str | None = None
    source_event_id: Uuid7
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_quantity(self) -> SimFill:
        """Reject nonpositive fill quantities.

        Returns:
            The validated simulated fill.

        Raises:
            ValueError: ``quantity`` is not positive.
        """
        if Decimal(self.quantity) <= 0:
            raise ValueError("quantity must be positive")
        return self


class SimPosition(WireModel):
    """One simulated position derived strictly from the order/fill ledger.

    No independent position mutation bypasses the order and fill ledger.
    """

    position_id: Uuid7
    result_id: Uuid7
    symbol: NonEmptyStr
    direction: PositionDirection
    opened_at: UtcTimestamp | None = None
    closed_at: UtcTimestamp | None = None
    max_size: DecimalValue
    current_size: DecimalValue
    state: PositionState
    realized_pl: Money
    unrealized_pl: Money | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_sizes(self) -> SimPosition:
        """Reject negative position sizes.

        Returns:
            The validated simulated position.

        Raises:
            ValueError: ``max_size`` or ``current_size`` is negative.
        """
        if Decimal(self.max_size) < 0:
            raise ValueError("max_size must be >= 0")
        if Decimal(self.current_size) < 0:
            raise ValueError("current_size must be >= 0")
        return self


class SimTrade(WireModel):
    """One closed simulated trade with its cost allocation."""

    trade_id: Uuid7
    result_id: Uuid7
    position_id: Uuid7
    segment: Segment
    direction: PositionDirection
    size: DecimalValue
    open_price: DecimalValue
    close_price: DecimalValue
    opened_at: UtcTimestamp
    closed_at: UtcTimestamp
    gross_pl: Money
    costs: CostBreakdown
    net_pl: Money
    pips: DecimalValue
    close_reason: CloseReason
    mae: DecimalValue | None = None
    mfe: DecimalValue | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_size(self) -> SimTrade:
        """Reject nonpositive trade sizes.

        Returns:
            The validated simulated trade.

        Raises:
            ValueError: ``size`` is not positive.
        """
        if Decimal(self.size) <= 0:
            raise ValueError("size must be positive")
        return self


class SizingDecision(WireModel):
    """One position-sizing decision with its rejection outcome.

    Missing risk inputs or a below-minimum size reject the order; no
    implicit minimum-size trade exists.
    """

    decision_id: Uuid7
    method: NonEmptyStr
    method_version: int = Field(ge=1)
    computed_size: DecimalValue | None = None
    normalized_size: DecimalValue | None = None
    rejected_reason: NonEmptyStr | None = None
    order_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class ExitSchedule(WireModel):
    """One declared exit with its collision and schedule semantics.

    Same-event collisions resolve through the versioned path/priority
    policy with all considered conditions recorded; trading schedule
    boundaries use the configured session timezone.
    """

    exit_id: Uuid7
    kind: ExitKind
    level: DecimalValue | None = None
    activation: JsonObject = Field(default_factory=dict)
    collision_priority: int = Field(ge=0)
    considered_conditions: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class IndicatorRuntimeSpec(WireModel):
    """One isolated indicator runtime instance specification.

    State is isolated per strategy instance or chart; parallel strategies
    cannot alter one another; insufficient warm-up blocks or yields
    declared nulls.
    """

    instance_id: Uuid7
    indicator_id: NonEmptyStr
    indicator_version: int = Field(ge=1)
    chart_ordinal: int = Field(ge=0)
    warmup_bars: int = Field(default=0, ge=0)
    missing_value_policy: MissingValuePolicy
    state_scope: IndicatorStateScope
    schema_version: Literal[1] = 1


class SimulationResult(WireModel):
    """One committed or staged simulation result with its artifacts.

    A result commits only after order/trade/equity reconciliation, schema
    validation, and artifact checksums; stopped or cancelled partial
    outputs stay explicitly INCOMPLETE and can never be promoted or
    exported as complete. Exactly one result exists per manifest.
    """

    result_id: Uuid7
    strategy_version_id: Uuid7
    manifest_id: Uuid7
    state: ResultState
    completion: ResultCompletion
    metric_value_ids: tuple[Uuid7, ...] = ()
    order_artifact_id: Uuid7 | None = None
    trade_artifact_id: Uuid7 | None = None
    equity_artifact_id: Uuid7 | None = None
    diagnostic_artifact_id: Uuid7 | None = None
    created_at: UtcTimestamp
    committed_at: UtcTimestamp | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ResultCommitReceipt(WireModel):
    """One commit receipt proving reconciliation and artifact checksums.

    Replaying the commit never creates a second logical result.
    """

    receipt_id: Uuid7
    result_id: Uuid7
    manifest_id: Uuid7
    reconciliation_passed: Literal[True]
    schema_validation_passed: Literal[True]
    artifact_checksums: dict[ArtifactKey, ContentHash]
    committed_at: UtcTimestamp
    schema_version: Literal[1] = 1


class EvaluationCacheKey(WireModel):
    """One exact-content evaluation cache key.

    Compatible repeats reuse one result; any semantic input change causes
    a cache miss.
    """

    cache_key: ContentHash
    strategy_hash: ContentHash
    engine_hash: ContentHash
    data_binding_hash: ContentHash
    partition_hash: ContentHash
    cost_hash: ContentHash
    metric_hook_hash: ContentHash
    seed_hash: ContentHash
    result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class PerturbationSpec(WireModel):
    """One declared input perturbation for robustness re-runs.

    A zero-perturbation run's hash equals the baseline hash; baseline
    semantics are unchanged.
    """

    perturbation_id: Uuid7
    kind: PerturbationKind
    parameters: JsonObject
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DistributedEvaluationPlan(WireModel):
    """One worker-independent distributed evaluation plan.

    Plans are independent of worker identity, machine locale, scheduling
    order, and artifact locality; local and remote golden runs produce
    identical canonical artifacts; checkpoint/resume discards or resumes
    staged work per policy on worker loss.
    """

    plan_id: Uuid7
    manifest_id: Uuid7
    partition_ids: tuple[Uuid7, ...] = Field(min_length=1)
    worker_requirements: tuple[CapabilityIdentifier, ...] = ()
    locality_hints: tuple[ContentHash, ...] = ()
    schema_version: Literal[1] = 1


class StockpickerSimulationSpec(WireModel):
    """One stockpicker simulation specification over a pinned universe.

    The daily-strict profile restricts evaluation to daily OHLC with
    pessimistic ambiguity rules and next-session protection activation.
    """

    spec_id: Uuid7
    universe: UniverseRef
    universe_version: int = Field(ge=1)
    ranking_timestamp: UtcTimestamp
    rebalance_schedule: NonEmptyStr
    allocation_policy: JsonObject
    turnover_cost_policy: JsonObject
    delisting_policy: NonEmptyStr
    missing_data_policy: NonEmptyStr
    evaluation_timing: StockpickerEvaluationTiming
    daily_strict_profile: bool = False
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class VolumeProfileResult(WireModel):
    """One calculated volume profile over a Data volume-profile source.

    Experimental capability; semantics per PROJECT §21.7 and §23.11.
    """

    profile_id: Uuid7
    source_id: Uuid7
    session_version_ids: tuple[Uuid7, ...] = ()
    value_area_percent: DecimalValue = "70"
    poc_price: DecimalValue
    value_area_high: DecimalValue
    value_area_low: DecimalValue
    bins_artifact_id: Uuid7
    is_incomplete_source: bool
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_value_area_percent(self) -> VolumeProfileResult:
        """Reject value-area percentages outside the interval (0, 100].

        Returns:
            The validated volume profile result.

        Raises:
            ValueError: ``value_area_percent`` is not greater than 0 and
                at most 100.
        """
        value_area = Decimal(self.value_area_percent)
        if value_area <= 0 or value_area > _VALUE_AREA_PERCENT_MAX:
            raise ValueError("value_area_percent must be within (0, 100]")
        return self


class TpoProfileResult(WireModel):
    """One calculated TPO profile over a Data volume-profile source.

    Experimental capability; independent of volume calculations.
    """

    tpo_id: Uuid7
    source_id: Uuid7
    session_version_ids: tuple[Uuid7, ...] = ()
    poc_price: DecimalValue
    tpo_counts_artifact_id: Uuid7
    is_incomplete_source: bool
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ConfigureEngineRequest(WireModel):
    """Operation-discriminated engine profile request.

    DEFINE_PROFILE requires ``profile``; LIST_PROFILES forbids it.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_PROFILE", "LIST_PROFILES"]
    profile: EngineProfileVersion | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ConfigureEngineRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "DEFINE_PROFILE":
                _require_present((("profile", self.profile),))
            case "LIST_PROFILES":
                _require_absent((("profile", self.profile),))
        return self


class ConfigureEngineSuccess(WireModel):
    """Successful engine profile operation result."""

    request_id: Uuid7
    profile: EngineProfileVersion | None = None
    profiles: tuple[EngineProfileVersion, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ModelPrecisionRequest(WireModel):
    """Operation-discriminated precision model request.

    DEFINE_MODEL stores the declared model; VALIDATE_INPUTS checks a
    candidate model's declared inputs. Both require ``model``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_MODEL", "VALIDATE_INPUTS"]
    model: PrecisionModel | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ModelPrecisionRequest:
        """Require the precision model for both operations.

        Returns:
            The validated request.

        Raises:
            ValueError: ``model`` is missing.
        """
        _require_present((("model", self.model),))
        return self


class ModelPrecisionSuccess(WireModel):
    """Successful precision model operation result."""

    request_id: Uuid7
    model: PrecisionModel | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class SimulateOrdersRequest(WireModel):
    """Operation-discriminated simulation and job-control request.

    SUBMIT requires ``simulation_request``; the PAUSE, RESUME, STOP,
    CANCEL, and INSPECT job actions require ``job_id``; COMPARE requires
    the ``baseline_result_id`` and ``candidate_result_id`` pair whose
    differential comparison reports the earliest mismatch.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "SUBMIT", "PAUSE", "RESUME", "STOP", "CANCEL", "INSPECT", "COMPARE"
    ]
    simulation_request: SimulationRequest | None = None
    job_id: Uuid7 | None = None
    baseline_result_id: Uuid7 | None = None
    candidate_result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> SimulateOrdersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "SUBMIT":
                _require_present((("simulation_request", self.simulation_request),))
                _require_absent(
                    (
                        ("job_id", self.job_id),
                        ("baseline_result_id", self.baseline_result_id),
                        ("candidate_result_id", self.candidate_result_id),
                    )
                )
            case "PAUSE" | "RESUME" | "STOP" | "CANCEL" | "INSPECT":
                _require_present((("job_id", self.job_id),))
                _require_absent(
                    (
                        ("simulation_request", self.simulation_request),
                        ("baseline_result_id", self.baseline_result_id),
                        ("candidate_result_id", self.candidate_result_id),
                    )
                )
            case "COMPARE":
                _require_present(
                    (
                        ("baseline_result_id", self.baseline_result_id),
                        ("candidate_result_id", self.candidate_result_id),
                    )
                )
                _require_absent(
                    (
                        ("simulation_request", self.simulation_request),
                        ("job_id", self.job_id),
                    )
                )
        return self


class SimulateOrdersSuccess(WireModel):
    """Successful simulation and job-control operation result."""

    request_id: Uuid7
    run: SimulationRunRef | None = None
    manifest: RunManifest | None = None
    order: SimOrder | None = None
    comparison: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CalculateCostsRequest(WireModel):
    """Operation-discriminated sizing and trading-cost request.

    SIZE_POSITION requires ``method``, ``method_version``, and the
    free-form ``context`` of sizing inputs; APPLY_COSTS requires only
    ``context``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["SIZE_POSITION", "APPLY_COSTS"]
    method: NonEmptyStr | None = None
    method_version: int | None = Field(default=None, ge=1)
    context: JsonObject | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CalculateCostsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "SIZE_POSITION":
                _require_present(
                    (
                        ("method", self.method),
                        ("method_version", self.method_version),
                        ("context", self.context),
                    )
                )
            case "APPLY_COSTS":
                _require_present((("context", self.context),))
                _require_absent(
                    (
                        ("method", self.method),
                        ("method_version", self.method_version),
                    )
                )
        return self


class CalculateCostsSuccess(WireModel):
    """Successful sizing and trading-cost operation result."""

    request_id: Uuid7
    sizing: SizingDecision | None = None
    costs: CostBreakdown | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ManageExitsRequest(WireModel):
    """Operation-discriminated exit, collision, and ATM request.

    SCHEDULE_EXIT requires ``schedule``; RESOLVE_COLLISION and EXECUTE_ATM
    require ``run_id``; ALLOCATE_PARTIAL requires ``run_id`` plus the
    free-form allocation ``context``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "SCHEDULE_EXIT", "RESOLVE_COLLISION", "EXECUTE_ATM", "ALLOCATE_PARTIAL"
    ]
    schedule: ExitSchedule | None = None
    run_id: Uuid7 | None = None
    context: JsonObject | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageExitsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "SCHEDULE_EXIT":
                _require_present((("schedule", self.schedule),))
                _require_absent(
                    (
                        ("run_id", self.run_id),
                        ("context", self.context),
                    )
                )
            case "RESOLVE_COLLISION" | "EXECUTE_ATM":
                _require_present((("run_id", self.run_id),))
                _require_absent(
                    (
                        ("schedule", self.schedule),
                        ("context", self.context),
                    )
                )
            case "ALLOCATE_PARTIAL":
                _require_present(
                    (
                        ("run_id", self.run_id),
                        ("context", self.context),
                    )
                )
                _require_absent((("schedule", self.schedule),))
        return self


class ManageExitsSuccess(WireModel):
    """Successful exit, collision, and ATM operation result."""

    request_id: Uuid7
    schedule: ExitSchedule | None = None
    allocations: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class RunIndicatorsRequest(WireModel):
    """Operation-discriminated indicator runtime request.

    PREPARE_SPEC registers the declared runtime specification; EVALUATE
    evaluates it. Both require ``spec``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PREPARE_SPEC", "EVALUATE"]
    spec: IndicatorRuntimeSpec | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> RunIndicatorsRequest:
        """Require the indicator runtime specification for both operations.

        Returns:
            The validated request.

        Raises:
            ValueError: ``spec`` is missing.
        """
        _require_present((("spec", self.spec),))
        return self


class RunIndicatorsSuccess(WireModel):
    """Successful indicator runtime operation result."""

    request_id: Uuid7
    spec: IndicatorRuntimeSpec | None = None
    findings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CommitResultsRequest(WireModel):
    """Operation-discriminated result commit request.

    VALIDATE requires the staged ``result`` record; COMMIT requires the
    validated ``result_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["VALIDATE", "COMMIT"]
    result: SimulationResult | None = None
    result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CommitResultsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "VALIDATE":
                _require_present((("result", self.result),))
                _require_absent((("result_id", self.result_id),))
            case "COMMIT":
                _require_present((("result_id", self.result_id),))
                _require_absent((("result", self.result),))
        return self


class CommitResultsSuccess(WireModel):
    """Successful result commit operation result."""

    request_id: Uuid7
    result: SimulationResult | None = None
    receipt: ResultCommitReceipt | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CacheEvaluationsRequest(WireModel):
    """Operation-discriminated evaluation cache request.

    LOOKUP requires ``cache_key``; STORE requires ``cache_key`` plus the
    produced ``result_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["LOOKUP", "STORE"]
    cache_key: EvaluationCacheKey | None = None
    result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CacheEvaluationsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "LOOKUP":
                _require_present((("cache_key", self.cache_key),))
                _require_absent((("result_id", self.result_id),))
            case "STORE":
                _require_present(
                    (
                        ("cache_key", self.cache_key),
                        ("result_id", self.result_id),
                    )
                )
        return self


class CacheEvaluationsSuccess(WireModel):
    """Successful evaluation cache operation result."""

    request_id: Uuid7
    cache_key: EvaluationCacheKey | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CalculateProfilesRequest(WireModel):
    """Operation-discriminated volume-profile and TPO request.

    Both operations require the Data-owned profile ``source_id``; the
    optional ``session_version_ids`` bound the calculation window.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CALCULATE_VOLUME_PROFILE", "CALCULATE_TPO"]
    source_id: Uuid7
    session_version_ids: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class CalculateProfilesSuccess(WireModel):
    """Successful volume-profile and TPO operation result."""

    request_id: Uuid7
    volume_profile: VolumeProfileResult | None = None
    tpo_profile: TpoProfileResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class PerturbInputsRequest(WireModel):
    """Perturbation definition request; requires ``spec``."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_PERTURBATION"]
    spec: PerturbationSpec | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> PerturbInputsRequest:
        """Require the perturbation specification.

        Returns:
            The validated request.

        Raises:
            ValueError: ``spec`` is missing.
        """
        _require_present((("spec", self.spec),))
        return self


class PerturbInputsSuccess(WireModel):
    """Successful perturbation definition operation result."""

    request_id: Uuid7
    spec: PerturbationSpec | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DistributeEvaluationsRequest(WireModel):
    """Operation-discriminated distributed evaluation request.

    PLAN requires the ``manifest_id`` being distributed; STREAM_PROGRESS
    requires the ``plan_id`` whose bounded intermediate summaries are
    requested.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "STREAM_PROGRESS"]
    manifest_id: Uuid7 | None = None
    plan_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DistributeEvaluationsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "PLAN":
                _require_present((("manifest_id", self.manifest_id),))
                _require_absent((("plan_id", self.plan_id),))
            case "STREAM_PROGRESS":
                _require_present((("plan_id", self.plan_id),))
                _require_absent((("manifest_id", self.manifest_id),))
        return self


class DistributeEvaluationsSuccess(WireModel):
    """Successful distributed evaluation operation result."""

    request_id: Uuid7
    plan: DistributedEvaluationPlan | None = None
    progress: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class SimulateStockpickersRequest(WireModel):
    """Operation-discriminated stockpicker simulation request.

    DEFINE_SPEC requires ``spec``; SIMULATE requires the stored
    ``spec_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_SPEC", "SIMULATE"]
    spec: StockpickerSimulationSpec | None = None
    spec_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> SimulateStockpickersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "DEFINE_SPEC":
                _require_present((("spec", self.spec),))
                _require_absent((("spec_id", self.spec_id),))
            case "SIMULATE":
                _require_present((("spec_id", self.spec_id),))
                _require_absent((("spec", self.spec),))
        return self


class SimulateStockpickersSuccess(WireModel):
    """Successful stockpicker simulation operation result."""

    request_id: Uuid7
    spec: StockpickerSimulationSpec | None = None
    result_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# ProviderPin is the nested record component of RunManifest; the R6
# SimulationEvent payload lives in events.py with its own WIRE_EVENTS
# registry. PEP 695 ``type`` aliases are not classes and cannot register.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "ProviderPin": ProviderPin,
    "CostBreakdown": CostBreakdown,
    "ResultSegment": ResultSegment,
    "RunManifest": RunManifest,
    "EngineProfileVersion": EngineProfileVersion,
    "PrecisionModel": PrecisionModel,
    "SimulationRequest": SimulationRequest,
    "SimulationRunRef": SimulationRunRef,
    "SimOrder": SimOrder,
    "SimFill": SimFill,
    "SimPosition": SimPosition,
    "SimTrade": SimTrade,
    "SizingDecision": SizingDecision,
    "ExitSchedule": ExitSchedule,
    "IndicatorRuntimeSpec": IndicatorRuntimeSpec,
    "SimulationResult": SimulationResult,
    "ResultCommitReceipt": ResultCommitReceipt,
    "EvaluationCacheKey": EvaluationCacheKey,
    "PerturbationSpec": PerturbationSpec,
    "DistributedEvaluationPlan": DistributedEvaluationPlan,
    "StockpickerSimulationSpec": StockpickerSimulationSpec,
    "VolumeProfileResult": VolumeProfileResult,
    "TpoProfileResult": TpoProfileResult,
    "ConfigureEngineRequest": ConfigureEngineRequest,
    "ConfigureEngineSuccess": ConfigureEngineSuccess,
    "ModelPrecisionRequest": ModelPrecisionRequest,
    "ModelPrecisionSuccess": ModelPrecisionSuccess,
    "SimulateOrdersRequest": SimulateOrdersRequest,
    "SimulateOrdersSuccess": SimulateOrdersSuccess,
    "CalculateCostsRequest": CalculateCostsRequest,
    "CalculateCostsSuccess": CalculateCostsSuccess,
    "ManageExitsRequest": ManageExitsRequest,
    "ManageExitsSuccess": ManageExitsSuccess,
    "RunIndicatorsRequest": RunIndicatorsRequest,
    "RunIndicatorsSuccess": RunIndicatorsSuccess,
    "CommitResultsRequest": CommitResultsRequest,
    "CommitResultsSuccess": CommitResultsSuccess,
    "CacheEvaluationsRequest": CacheEvaluationsRequest,
    "CacheEvaluationsSuccess": CacheEvaluationsSuccess,
    "CalculateProfilesRequest": CalculateProfilesRequest,
    "CalculateProfilesSuccess": CalculateProfilesSuccess,
    "PerturbInputsRequest": PerturbInputsRequest,
    "PerturbInputsSuccess": PerturbInputsSuccess,
    "DistributeEvaluationsRequest": DistributeEvaluationsRequest,
    "DistributeEvaluationsSuccess": DistributeEvaluationsSuccess,
    "SimulateStockpickersRequest": SimulateStockpickersRequest,
    "SimulateStockpickersSuccess": SimulateStockpickersSuccess,
}
