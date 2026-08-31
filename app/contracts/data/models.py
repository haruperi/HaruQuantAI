"""Strict Pydantic v2 wire records for the ratified Data v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# These reference types are annotation-only for readers but Pydantic resolves
# them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import (  # noqa: TC001
    BrokerRef,
    InstrumentRef,
    ProviderRef,
)
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    CurrencyCode,
    DecimalValue,
    JsonObject,
    JsonValue,
    Precision,
    SeriesPointKey,
    Timeframe,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Constrained local string aliases reused across data records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: IANA zone names are limited to zone/path segments made of
# letters, digits, ``+``, ``-``, and ``_``; this is a syntactic wire check,
# not tzdb resolution (same contract as the Catalogue alias).
type IanaTimezone = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9+\-_]+(?:/[A-Za-z0-9+\-_]+)*$"),
]
# Uppercase quality rule code; the fixed rule list is enumerated by
# FR-DATA-DETECT_DATA_QUALITY and is not part of the wire grammar.
type RuleCode = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]

# Closed enum literals local to the Data records.
type TickType = Literal["BID_ASK", "LAST"]
type DeduplicationPolicy = Literal["KEEP_FIRST", "KEEP_LAST", "REJECT"]
type NewsImpact = Literal["NONE", "LOW", "MEDIUM", "HIGH"]
type ProfileSourceKind = Literal["TICK", "LOWER_GRANULARITY"]

# Widest unsigned 32-bit flag word; §22.3 defines bits 0-5.
_U32_MAX = 4_294_967_295


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


def _require_positive_decimal(fields: tuple[tuple[str, DecimalValue], ...]) -> None:
    """Reject decimal fields that are not strictly positive.

    Args:
        fields: ``(field name, value)`` pairs bounded to ``> 0``.

    Raises:
        ValueError: Any listed decimal is zero or negative.
    """
    for name, value in fields:
        if Decimal(value) <= 0:
            raise ValueError(name + " must be positive")


def _require_nonnegative_decimal(
    fields: tuple[tuple[str, DecimalValue | None], ...],
) -> None:
    """Reject present decimal fields below zero.

    Args:
        fields: ``(field name, value)`` pairs bounded to ``>= 0``; a None
            value skips the bound because the field is absent.

    Raises:
        ValueError: Any present decimal is negative.
    """
    for name, value in fields:
        if value is not None and Decimal(value) < 0:
            raise ValueError(name + " must be >= 0")


class DataSeriesRef(WireModel):
    """Reference to one market or external data series identity."""

    series_id: Uuid7
    schema_version: Literal[1] = 1


class SeriesInterval(WireModel):
    """Half-open UTC interval `[from_at, to_at)`.

    The interval must be positive; half-open interval semantics follow
    Project §15.4 and apply to every data interval record.
    """

    from_at: UtcTimestamp
    to_at: UtcTimestamp

    @model_validator(mode="after")
    def validate_order(self) -> SeriesInterval:
        """Reject empty or inverted intervals.

        Returns:
            The validated interval.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class SeriesCoverage(WireModel):
    """Half-open covered window plus observable interior gap intervals."""

    from_at: UtcTimestamp
    to_at: UtcTimestamp
    gap_intervals: tuple[SeriesInterval, ...] = ()
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_order(self) -> SeriesCoverage:
        """Reject an empty or inverted coverage window.

        Returns:
            The validated coverage.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class DataSeriesVersion(WireModel):
    """One immutable published version of a data series.

    Exactly one of ``timeframe`` and ``tick_type`` discriminates bar-series
    versus tick-series precision; series identity uniqueness is
    ``(instrument_id, broker_id, timeframe, tick_type)``.
    """

    series_version_id: Uuid7
    series_id: Uuid7
    version: int = Field(ge=1)
    instrument: InstrumentRef
    instrument_version_id: Uuid7
    session_version_id: Uuid7 | None
    calendar_version_id: Uuid7 | None
    broker: BrokerRef | None
    timeframe: Timeframe | None
    tick_type: TickType | None
    timezone: IanaTimezone
    precision: Precision
    coverage: SeriesCoverage
    row_count: int = Field(ge=0)
    source_artifact_id: Uuid7
    canonical_artifact_id: Uuid7
    import_policy: Uuid7 | None
    aggregation_lineage: Uuid7 | None
    findings_summary: tuple[ValidationIssue, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_timeframe_exclusivity(self) -> DataSeriesVersion:
        """Reject versions that set both or neither series discriminator.

        Returns:
            The validated series version.

        Raises:
            ValueError: ``timeframe`` and ``tick_type`` are not set to
                exactly one value.
        """
        if (self.timeframe is None) == (self.tick_type is None):
            raise ValueError("exactly one of timeframe and tick_type must be set")
        return self


class DataConnectionRef(WireModel):
    """Reference to one registered data connection by type."""

    connection_id: Uuid7
    connection_type: Literal["CSV", "PARQUET", "CONNECTOR", "QUANTDATA"]
    declared_capabilities: tuple[CapabilityIdentifier, ...] = ()
    schema_version: Literal[1] = 1


class DataImportPlan(WireModel):
    """One CSV import plan pinned to a registered connection.

    The same plan imports a fixture identically through UI and CLI.
    """

    plan_id: Uuid7
    connection: DataConnectionRef
    source_artifact_id: Uuid7
    delimiter: str = ","
    has_header: bool = True
    encoding: NonEmptyStr = "utf-8"
    timestamp_format: str | None = None
    timezone: IanaTimezone
    column_mapping: dict[NonEmptyStr, NonEmptyStr]
    decimal_separator: str = "."
    malformed_row_policy: Literal["REJECT_ROW", "ABORT_IMPORT"]
    deduplication_policy: DeduplicationPolicy = "KEEP_FIRST"
    schema_version: Literal[1] = 1


class DataImportReceipt(WireModel):
    """Deterministic row counters for one executed import.

    The counters reconcile exactly to the input rows in every
    malformed-row mode: accepted, rejected, and duplicate rows partition
    the input, while transformed and published rows are pipeline stages
    bounded by the accepted rows.
    """

    receipt_id: Uuid7
    series_version_id: Uuid7
    input_rows: int = Field(ge=0)
    accepted_rows: int = Field(ge=0)
    rejected_rows: int = Field(ge=0)
    duplicate_rows: int = Field(ge=0)
    transformed_rows: int = Field(ge=0)
    published_rows: int = Field(ge=0)
    findings: tuple[ValidationIssue, ...] = ()
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_counter_reconciliation(self) -> DataImportReceipt:
        """Reject counter sets that do not reconcile to the input rows.

        Returns:
            The validated receipt.

        Raises:
            ValueError: Accepted, rejected, and duplicate rows do not sum
                to ``input_rows``, or a pipeline stage count exceeds the
                accepted rows.
        """
        if self.accepted_rows + self.rejected_rows + self.duplicate_rows != (
            self.input_rows
        ):
            raise ValueError(
                "accepted, rejected, and duplicate rows must sum to input_rows"
            )
        if self.transformed_rows > self.accepted_rows:
            raise ValueError("transformed_rows must be <= accepted_rows")
        if self.published_rows > self.accepted_rows:
            raise ValueError("published_rows must be <= accepted_rows")
        return self


class Bar(WireModel):
    """One OHLCV bar covering the half-open window from its open time."""

    timestamp: UtcTimestamp
    open: DecimalValue
    high: DecimalValue
    low: DecimalValue
    close: DecimalValue
    volume: DecimalValue
    spread_ticks: DecimalValue | None = None
    source_sequence: int = Field(ge=0)
    flags: int = Field(ge=0, le=_U32_MAX)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_ohlcv(self) -> Bar:
        """Reject bars that violate the ratified OHLC relationships.

        Returns:
            The validated bar.

        Raises:
            ValueError: A bounded decimal is negative or the
                high/low/open/close relationships are inconsistent.
        """
        _require_nonnegative_decimal(
            (("volume", self.volume), ("spread_ticks", self.spread_ticks))
        )
        open_price = Decimal(self.open)
        close_price = Decimal(self.close)
        high = Decimal(self.high)
        low = Decimal(self.low)
        # FR-DATA-VALIDATE_OHLC_BARS: nonfinite values are already rejected
        # structurally by the DecimalValue wire grammar.
        if low > min(open_price, close_price):
            raise ValueError("low must be <= min(open, close)")
        if high < max(open_price, close_price):
            raise ValueError("high must be >= max(open, close)")
        if low > high:
            raise ValueError("low must be <= high")
        return self


class Tick(WireModel):
    """One normalized bid/ask/last tick observation.

    Duplicate timestamps are preserved deterministically through
    ``source_sequence``; reimporting the same fixture yields the same
    canonical order and hash.
    """

    timestamp: UtcTimestamp
    bid: DecimalValue
    ask: DecimalValue
    last: DecimalValue | None = None
    volume: DecimalValue | None = None
    source_sequence: int = Field(ge=0)
    flags: int = Field(ge=0)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_nonnegative_volume(self) -> Tick:
        """Reject negative tick volume when volume is present.

        Returns:
            The validated tick.

        Raises:
            ValueError: ``volume`` is negative.
        """
        _require_nonnegative_decimal((("volume", self.volume),))
        return self


class DataQualityFinding(WireModel):
    """One detected quality finding pinned to a data version."""

    finding_id: Uuid7
    data_version_id: Uuid7
    rule_code: RuleCode
    severity: Literal["INFO", "WARNING", "ERROR"]
    point: SeriesPointKey | None = None
    range_from: UtcTimestamp | None = None
    range_to: UtcTimestamp | None = None
    observed: JsonValue = None
    expected: JsonValue = None
    resolution_state: Literal["OPEN", "ACCEPTED", "REJECTED", "TRANSFORMED"] = "OPEN"
    derived_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class DataQualityDecision(WireModel):
    """One explicit version-producing resolution of quality findings.

    A decision never mutates the source version; it records the
    source-to-derived lineage when the action transforms data.
    """

    decision_id: Uuid7
    finding_ids: tuple[Uuid7, ...] = Field(min_length=1)
    action: Literal["ACCEPT", "REJECT", "TRANSFORM"]
    policy_version: int = Field(ge=1)
    derived_version_id: Uuid7 | None = None
    decided_at: UtcTimestamp
    schema_version: Literal[1] = 1


class AggregationSpec(WireModel):
    """One bar-aggregation specification from a source series version.

    Custom intervals are positive multiples of a supported unit
    (``M10``/``H2`` valid; zero/mixed/overflow rejected), which the shared
    ``Timeframe`` grammar already enforces; aggregation never crosses
    session boundaries.
    """

    spec_id: Uuid7
    source_version_id: Uuid7
    target_timeframe: Timeframe
    session_version_id: Uuid7 | None
    calendar_version_id: Uuid7 | None
    timezone: IanaTimezone
    alignment_origin: Literal["SESSION_BOUNDARY", "UTC_MIDNIGHT"]
    gap_policy: Literal["ABSENT_EMPTY", "SYNTHETIC_GAP"] = "ABSENT_EMPTY"
    algorithm_version: NonEmptyStr
    schema_version: Literal[1] = 1


class RetentionPolicy(WireModel):
    """One retention and quarantine policy for artifact collection.

    Collection is reachability-based from committed manifests; referenced
    data is never collected and interrupted collection is recoverable.
    """

    policy_id: Uuid7
    retention_days: int | None = Field(default=None, ge=1)
    quarantine_days: int = Field(default=30, ge=1)
    schema_version: Literal[1] = 1


class AlignmentPolicy(WireModel):
    """One point-in-time alignment policy for external series.

    No value timestamped after a decision event can affect that event;
    ``look_ahead_prohibited`` is therefore pinned true.
    """

    direction: Literal["EXACT", "LAST_KNOWN", "AGGREGATE"]
    max_age_seconds: int = Field(ge=1)
    missing_policy: Literal["NULL", "CARRY_FORWARD", "FAIL"]
    timezone: IanaTimezone
    look_ahead_prohibited: Literal[True] = True


class RunDataBinding(WireModel):
    """One immutable binding of committed series versions to a run.

    Only committed versions bind, later imports never change a bound
    manifest, and missing prerequisites fail
    ``DATA_PRECISION_UNAVAILABLE`` before queueing.
    """

    binding_id: Uuid7
    run_manifest_id: Uuid7
    series_version_ids: tuple[Uuid7, ...] = Field(min_length=1)
    precision: Precision
    validated_at: UtcTimestamp
    schema_version: Literal[1] = 1


class AlignedSeries(WireModel):
    """One aligned external-series version produced under a policy."""

    alignment_id: Uuid7
    source_version_id: Uuid7
    policy: AlignmentPolicy
    aligned_version_id: Uuid7
    schema_version: Literal[1] = 1


class ConnectorProfile(WireModel):
    """One versioned connector identity and its governed limits.

    Credential references are opaque Workspace ``SecretRef`` identifiers
    and remain unavailable to strategy, result-panel, and research
    processes.
    """

    profile_id: Uuid7
    connector_kind: NonEmptyStr
    declared_capabilities: tuple[CapabilityIdentifier, ...]
    credential_refs: tuple[Uuid7, ...] = ()
    rate_limit: int | None = Field(default=None, ge=1)
    rate_window_seconds: int | None = Field(default=None, ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ConnectorSyncPlan(WireModel):
    """One incremental connector synchronization plan.

    Repeating the same synchronization is idempotent with the same
    committed hash; cursor and checkpoint support interruption resume
    under the §21.6 page contract.
    """

    plan_id: Uuid7
    profile_id: Uuid7
    connector_version: NonEmptyStr
    requested_from: UtcTimestamp
    requested_to: UtcTimestamp
    overlap_window_seconds: int = Field(default=0, ge=0)
    deduplication: DeduplicationPolicy = "KEEP_FIRST"
    revision_policy: Literal["COMPARE_OVERLAP", "FULL_RESCAN"] = "COMPARE_OVERLAP"
    cursor: str | None = None
    checkpoint: str | None = None
    max_records: int = Field(ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_requested_window(self) -> ConnectorSyncPlan:
        """Reject an empty or inverted requested synchronization window.

        Returns:
            The validated plan.

        Raises:
            ValueError: ``requested_to`` is not strictly after
                ``requested_from``.
        """
        if self.requested_to <= self.requested_from:
            raise ValueError("requested_to must be after requested_from")
        return self


class ConnectorSyncReceipt(WireModel):
    """One executed connector synchronization page receipt.

    Interruption resumes without duplicate publication by carrying the
    next cursor forward.
    """

    receipt_id: Uuid7
    records: int = Field(ge=0)
    provider_revision_ids: tuple[Uuid7, ...] = ()
    next_cursor: str | None = None
    is_complete: bool
    content_hash: ContentHash
    committed_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class VolumeProfileSource(WireModel):
    """One validated volume-profile source declaration.

    Insufficient precision or incomplete sessions fail or are explicitly
    flagged through ``is_sufficient`` and the coverage diagnostics.
    """

    source_id: Uuid7
    data_version_id: Uuid7
    source_kind: ProfileSourceKind
    session_version_id: Uuid7
    price_step: DecimalValue
    bin_count: int | None = Field(default=None, ge=1)
    coverage_diagnostics: tuple[ValidationIssue, ...] = ()
    is_sufficient: bool
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_price_step(self) -> VolumeProfileSource:
        """Reject nonpositive profile price steps.

        Returns:
            The validated source.

        Raises:
            ValueError: ``price_step`` is zero or negative.
        """
        _require_positive_decimal((("price_step", self.price_step),))
        return self


class ExternalIndicatorSeriesVersion(WireModel):
    """One immutable imported external-indicator series version.

    ``definition_id``/``definition_version`` reference the Strategy-owned
    external indicator definition version as opaque identifiers.
    """

    series_id: Uuid7
    version: int = Field(ge=1)
    definition_id: Uuid7
    definition_version: int = Field(ge=1)
    instrument: InstrumentRef
    timeframe: Timeframe | None
    timezone: IanaTimezone
    source_artifact_id: Uuid7
    source_hash: ContentHash
    canonical_artifact_id: Uuid7
    coverage: SeriesCoverage
    alignment_policy: AlignmentPolicy
    synchronization_findings: tuple[ValidationIssue, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class SyntheticModelSpec(WireModel):
    """One versioned synthetic-data model configuration.

    The same manifest produces byte-identical canonical output because
    the pinned seed streams and parameters follow §15.5.
    """

    spec_id: Uuid7
    model_type: NonEmptyStr
    model_version: NonEmptyStr
    parameters: JsonObject
    timeframe: Timeframe
    from_at: UtcTimestamp
    to_at: UtcTimestamp
    instrument: InstrumentRef
    seed_streams: tuple[NonEmptyStr, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_window(self) -> SyntheticModelSpec:
        """Reject an empty or inverted generation window.

        Returns:
            The validated specification.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class ScenarioTransform(WireModel):
    """One pinned scenario transform applied to a source series."""

    kind: Literal["SHOCK", "GAP", "VOLATILITY", "LIQUIDITY", "OUTAGE", "MISSINGNESS"]
    parameters: JsonObject


class ScenarioSeriesVersion(WireModel):
    """One immutable transformed or synthetic series version.

    The source version is never mutated, transform order is pinned, and
    synthetic data cannot masquerade as observed provider evidence
    unless the consumer explicitly permits it.
    """

    series_id: Uuid7
    version: int = Field(ge=1)
    source_version_id: Uuid7
    source_hash: ContentHash
    transforms: tuple[ScenarioTransform, ...] = ()
    classification: Literal["SYNTHETIC", "SCENARIO"]
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class MarketNewsObservation(WireModel):
    """One governed economic-calendar or news observation.

    Uniqueness is
    ``(source_id, provider_item_id, observed_at, revision)`` in
    ``economic_news_observation_versions``.
    """

    observation_id: Uuid7
    source_id: NonEmptyStr
    provider_item_id: NonEmptyStr
    first_seen_at: UtcTimestamp
    retrieved_at: UtcTimestamp
    scheduled_at: UtcTimestamp | None = None
    published_at: UtcTimestamp | None = None
    scope_currencies: tuple[CurrencyCode, ...] = ()
    scope_instruments: tuple[InstrumentRef, ...] = ()
    category: NonEmptyStr
    impact: NewsImpact
    language: NonEmptyStr
    payload_hash: ContentHash
    schema_version: Literal[1] = 1


class MarketNewsRevision(WireModel):
    """One point-in-time revision of a news observation.

    Point-in-time queries never expose information before it was
    observed; visibility starts at ``visible_from``.
    """

    revision_id: Uuid7
    observation_id: Uuid7
    revision: int = Field(ge=1)
    kind: Literal["REVISION", "CANCELLATION", "RESCHEDULE", "VALUES"]
    actual: DecimalValue | None = None
    forecast: DecimalValue | None = None
    previous: DecimalValue | None = None
    visible_from: UtcTimestamp
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class MarketEvent(WireModel):
    """One normalized real-time provider market event.

    Duplicates, late events, and gaps remain observable; repeated
    ingestion yields the same accepted order.
    """

    event_id: Uuid7
    provider: ProviderRef
    event_kind: Literal["QUOTE", "TICK", "DEPTH_UPDATE", "MARKET_STATUS", "HEARTBEAT"]
    event_time: UtcTimestamp
    receipt_time: UtcTimestamp
    provider_sequence: int | None = Field(default=None, ge=0)
    ordering_mode: Literal["PROVIDER_SEQUENCE", "RECEIPT_ORDER"]
    instrument: InstrumentRef | None = None
    values: JsonObject
    raw_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_ordering_mode(self) -> MarketEvent:
        """Reject provider-sequence ordering without a provider sequence.

        Returns:
            The validated event.

        Raises:
            ValueError: ``ordering_mode`` is ``PROVIDER_SEQUENCE`` while
                ``provider_sequence`` is absent.
        """
        # Ordering by provider sequence is impossible without the sequence;
        # receipt ordering needs no provider-supplied sequence.
        if self.ordering_mode == "PROVIDER_SEQUENCE" and self.provider_sequence is (
            None
        ):
            raise ValueError("PROVIDER_SEQUENCE ordering requires provider_sequence")
        return self


class MarketFeedState(WireModel):
    """One generation-scoped market feed readiness observation.

    A boolean connected flag cannot satisfy readiness; the explicit state
    ladder and uncovered intervals are authoritative.
    """

    feed_id: Uuid7
    provider: ProviderRef
    generation: int = Field(ge=1)
    state: Literal[
        "CONNECTING",
        "LIVE",
        "DELAYED",
        "STALE",
        "GAP",
        "RECONNECTING",
        "FAILED",
        "STOPPED",
    ]
    last_event_at: UtcTimestamp | None = None
    observed_at: UtcTimestamp
    uncovered_intervals: tuple[SeriesInterval, ...] = ()
    schema_version: Literal[1] = 1


class MarketReplayRef(WireModel):
    """Reference to one recorded bounded market-event replay.

    Replay reproduces normalized events and never claims current live
    evidence.
    """

    replay_id: Uuid7
    feed_id: Uuid7
    generation: int = Field(ge=1)
    partition_artifact_ids: tuple[Uuid7, ...] = ()
    from_at: UtcTimestamp
    to_at: UtcTimestamp
    event_count: int = Field(ge=0)
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_window(self) -> MarketReplayRef:
        """Reject an empty or inverted replay window.

        Returns:
            The validated replay reference.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class QuantDataImportSpec(WireModel):
    """One governed QuantDataManager import specification.

    Paths outside ``allowed_root`` are rejected and every imported
    version retains complete source-root, decoder, and mapping lineage;
    changed input or decoder produces a distinct version.
    """

    spec_id: Uuid7
    allowed_root: NonEmptyStr
    series_selection: tuple[NonEmptyStr, ...] = ()
    decoder_version: NonEmptyStr
    mapping_version_ids: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class IngestHistoryRequest(WireModel):
    """Operation-discriminated historical data ingestion request.

    REGISTER_CONNECTION requires only ``connection``; IMPORT requires
    only ``plan``; EXPORT requires ``series_version_id`` plus
    ``export_format``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REGISTER_CONNECTION", "IMPORT", "EXPORT"]
    connection: DataConnectionRef | None = None
    plan: DataImportPlan | None = None
    series_version_id: Uuid7 | None = None
    export_format: Literal["CSV", "PARQUET"] | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> IngestHistoryRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "REGISTER_CONNECTION":
                _require_present((("connection", self.connection),))
                _require_absent(
                    (
                        ("plan", self.plan),
                        ("series_version_id", self.series_version_id),
                        ("export_format", self.export_format),
                    )
                )
            case "IMPORT":
                _require_present((("plan", self.plan),))
                _require_absent(
                    (
                        ("connection", self.connection),
                        ("series_version_id", self.series_version_id),
                        ("export_format", self.export_format),
                    )
                )
            case "EXPORT":
                _require_present(
                    (
                        ("series_version_id", self.series_version_id),
                        ("export_format", self.export_format),
                    )
                )
                _require_absent(
                    (
                        ("connection", self.connection),
                        ("plan", self.plan),
                    )
                )
        return self


class IngestHistorySuccess(WireModel):
    """Successful historical data ingestion operation result."""

    request_id: Uuid7
    connection: DataConnectionRef | None = None
    receipt: DataImportReceipt | None = None
    version: DataSeriesVersion | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class SyncConnectorsRequest(WireModel):
    """Operation-discriminated connector synchronization request.

    PLAN requires the target profile, window, bound, and optional
    deduplication policies; FETCH requires only ``plan``; COMMIT requires
    ``plan`` and ``receipt``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PLAN", "FETCH", "COMMIT"]
    profile_id: Uuid7 | None = None
    requested_from: UtcTimestamp | None = None
    requested_to: UtcTimestamp | None = None
    max_records: int | None = Field(default=None, ge=1)
    overlap_window_seconds: int | None = Field(default=None, ge=0)
    deduplication: DeduplicationPolicy | None = None
    revision_policy: Literal["COMPARE_OVERLAP", "FULL_RESCAN"] | None = None
    plan: ConnectorSyncPlan | None = None
    receipt: ConnectorSyncReceipt | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> SyncConnectorsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or the PLAN window is inverted.
        """
        match self.operation:
            case "PLAN":
                _require_present(
                    (
                        ("profile_id", self.profile_id),
                        ("requested_from", self.requested_from),
                        ("requested_to", self.requested_to),
                        ("max_records", self.max_records),
                    )
                )
                _require_absent((("plan", self.plan), ("receipt", self.receipt)))
                if (
                    self.requested_to is not None
                    and self.requested_from is not None
                    and self.requested_to <= self.requested_from
                ):
                    raise ValueError("PLAN requires requested_to after requested_from")
            case "FETCH":
                _require_present((("plan", self.plan),))
                _require_absent(
                    (
                        ("profile_id", self.profile_id),
                        ("requested_from", self.requested_from),
                        ("requested_to", self.requested_to),
                        ("max_records", self.max_records),
                        ("overlap_window_seconds", self.overlap_window_seconds),
                        ("deduplication", self.deduplication),
                        ("revision_policy", self.revision_policy),
                        ("receipt", self.receipt),
                    )
                )
            case "COMMIT":
                _require_present((("plan", self.plan), ("receipt", self.receipt)))
                _require_absent(
                    (
                        ("profile_id", self.profile_id),
                        ("requested_from", self.requested_from),
                        ("requested_to", self.requested_to),
                        ("max_records", self.max_records),
                        ("overlap_window_seconds", self.overlap_window_seconds),
                        ("deduplication", self.deduplication),
                        ("revision_policy", self.revision_policy),
                    )
                )
        return self


class SyncConnectorsSuccess(WireModel):
    """Successful connector synchronization operation result."""

    request_id: Uuid7
    plan: ConnectorSyncPlan | None = None
    receipt: ConnectorSyncReceipt | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ImportQuantdataRequest(WireModel):
    """Operation-discriminated QuantDataManager import request.

    DISCOVER, DECODE, and SYNC all operate on one governed
    ``QuantDataImportSpec``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DISCOVER", "DECODE", "SYNC"]
    spec: QuantDataImportSpec
    schema_version: Literal[1] = 1


class ImportQuantdataSuccess(WireModel):
    """Successful QuantDataManager import operation result."""

    request_id: Uuid7
    spec: QuantDataImportSpec | None = None
    committed_version_ids: tuple[Uuid7, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class NormalizeTicksRequest(WireModel):
    """Tick normalization request carrying the raw tick batch."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["NORMALIZE"]
    ticks: tuple[Tick, ...] = Field(min_length=1)
    schema_version: Literal[1] = 1


class NormalizeTicksSuccess(WireModel):
    """Successful tick normalization operation result."""

    request_id: Uuid7
    version_id: Uuid7 | None = None
    findings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ResolveQualityRequest(WireModel):
    """Operation-discriminated data quality request.

    DETECT requires only ``data_version_id``; RESOLVE requires only
    ``decision``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DETECT", "RESOLVE"]
    data_version_id: Uuid7 | None = None
    decision: DataQualityDecision | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ResolveQualityRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "DETECT":
                _require_present((("data_version_id", self.data_version_id),))
                _require_absent((("decision", self.decision),))
            case "RESOLVE":
                _require_present((("decision", self.decision),))
                _require_absent((("data_version_id", self.data_version_id),))
        return self


class ResolveQualitySuccess(WireModel):
    """Successful data quality operation result."""

    request_id: Uuid7
    findings: tuple[DataQualityFinding, ...] = ()
    decision: DataQualityDecision | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AggregateBarsRequest(WireModel):
    """Operation-discriminated bar aggregation request.

    AGGREGATE requires only ``spec``; VALIDATE_TIMEFRAME requires only
    ``target_timeframe``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["AGGREGATE", "VALIDATE_TIMEFRAME"]
    spec: AggregationSpec | None = None
    target_timeframe: Timeframe | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> AggregateBarsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "AGGREGATE":
                _require_present((("spec", self.spec),))
                _require_absent((("target_timeframe", self.target_timeframe),))
            case "VALIDATE_TIMEFRAME":
                _require_present((("target_timeframe", self.target_timeframe),))
                _require_absent((("spec", self.spec),))
        return self


class AggregateBarsSuccess(WireModel):
    """Successful bar aggregation operation result."""

    request_id: Uuid7
    spec: AggregationSpec | None = None
    derived_version_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ManageRetentionRequest(WireModel):
    """Operation-discriminated retention management request.

    DEFINE_POLICY requires only ``policy``; COLLECT carries no
    operation-specific fields and collects by manifest reachability.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_POLICY", "COLLECT"]
    policy: RetentionPolicy | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageRetentionRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: A required field is missing or a forbidden field
                is set for the selected operation.
        """
        match self.operation:
            case "DEFINE_POLICY":
                _require_present((("policy", self.policy),))
            case "COLLECT":
                _require_absent((("policy", self.policy),))
        return self


class ManageRetentionSuccess(WireModel):
    """Successful retention management operation result."""

    request_id: Uuid7
    policy: RetentionPolicy | None = None
    collected_count: int = Field(default=0, ge=0)
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AlignSeriesRequest(WireModel):
    """Operation-discriminated external series alignment request.

    ALIGN and DEFINE_POLICY both require ``source_version_id`` and
    ``policy``; they differ only in execution effect.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["ALIGN", "DEFINE_POLICY"]
    source_version_id: Uuid7 | None = None
    policy: AlignmentPolicy | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> AlignSeriesRequest:
        """Require the alignment inputs for every operation.

        Returns:
            The validated request.

        Raises:
            ValueError: ``source_version_id`` or ``policy`` is missing.
        """
        _require_present(
            (
                ("source_version_id", self.source_version_id),
                ("policy", self.policy),
            )
        )
        return self


class AlignSeriesSuccess(WireModel):
    """Successful external series alignment operation result."""

    request_id: Uuid7
    aligned: AlignedSeries | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class PrepareProfilesRequest(WireModel):
    """Volume-profile source validation request.

    The request carries exactly the source declaration inputs; the
    capability computes sufficiency and coverage diagnostics.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["VALIDATE_SOURCE"]
    data_version_id: Uuid7
    source_kind: ProfileSourceKind
    session_version_id: Uuid7
    price_step: DecimalValue
    bin_count: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_price_step(self) -> PrepareProfilesRequest:
        """Reject nonpositive profile price steps.

        Returns:
            The validated request.

        Raises:
            ValueError: ``price_step`` is zero or negative.
        """
        _require_positive_decimal((("price_step", self.price_step),))
        return self


class PrepareProfilesSuccess(WireModel):
    """Successful volume-profile source validation result."""

    request_id: Uuid7
    source: VolumeProfileSource | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ImportIndicatorsRequest(WireModel):
    """External indicator series import request.

    The request carries the immutable input side of the imported series
    version; the capability computes canonical artifact, coverage,
    synchronization findings, and content hash.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["IMPORT"]
    series_id: Uuid7
    definition_id: Uuid7
    definition_version: int = Field(ge=1)
    instrument: InstrumentRef
    timeframe: Timeframe | None = None
    timezone: IanaTimezone
    source_artifact_id: Uuid7
    source_hash: ContentHash
    alignment_policy: AlignmentPolicy
    schema_version: Literal[1] = 1


class ImportIndicatorsSuccess(WireModel):
    """Successful external indicator series import result."""

    request_id: Uuid7
    version_id: Uuid7 | None = None
    findings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class BindRunDataRequest(WireModel):
    """Operation-discriminated run data binding request.

    BIND requires ``run_manifest_id``, ``series_version_ids``, and
    ``precision``; VALIDATE_PRECISION requires the latter two only.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["BIND", "VALIDATE_PRECISION"]
    run_manifest_id: Uuid7 | None = None
    series_version_ids: tuple[Uuid7, ...] | None = Field(default=None, min_length=1)
    precision: Precision | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> BindRunDataRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "BIND":
                _require_present(
                    (
                        ("run_manifest_id", self.run_manifest_id),
                        ("series_version_ids", self.series_version_ids),
                        ("precision", self.precision),
                    )
                )
            case "VALIDATE_PRECISION":
                _require_present(
                    (
                        ("series_version_ids", self.series_version_ids),
                        ("precision", self.precision),
                    )
                )
                _require_absent((("run_manifest_id", self.run_manifest_id),))
        return self


class BindRunDataSuccess(WireModel):
    """Successful run data binding operation result."""

    request_id: Uuid7
    binding: RunDataBinding | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GenerateScenariosRequest(WireModel):
    """Operation-discriminated synthetic and scenario request.

    CONFIGURE_MODEL and GENERATE require only ``spec``; TRANSFORM
    requires ``source_version_id``, ``source_hash``, and
    ``classification`` with optional pinned ``transforms``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CONFIGURE_MODEL", "GENERATE", "TRANSFORM"]
    spec: SyntheticModelSpec | None = None
    source_version_id: Uuid7 | None = None
    source_hash: ContentHash | None = None
    transforms: tuple[ScenarioTransform, ...] = ()
    classification: Literal["SYNTHETIC", "SCENARIO"] | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GenerateScenariosRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields
                are set for the selected operation.
        """
        match self.operation:
            case "CONFIGURE_MODEL" | "GENERATE":
                _require_present((("spec", self.spec),))
                _require_absent(
                    (
                        ("source_version_id", self.source_version_id),
                        ("source_hash", self.source_hash),
                        ("classification", self.classification),
                    )
                )
                if self.transforms:
                    raise ValueError("forbidden field is set: transforms")
            case "TRANSFORM":
                _require_present(
                    (
                        ("source_version_id", self.source_version_id),
                        ("source_hash", self.source_hash),
                        ("classification", self.classification),
                    )
                )
                _require_absent((("spec", self.spec),))
        return self


class GenerateScenariosSuccess(WireModel):
    """Successful synthetic and scenario operation result."""

    request_id: Uuid7
    spec: SyntheticModelSpec | None = None
    scenario_version_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class TrackMarketNewsRequest(WireModel):
    """Operation-discriminated economic calendar and news request.

    RECORD requires only ``observation``; REVISE requires only
    ``revision``; QUERY requires ``as_of`` plus a positive interval and
    carries source/category/language/impact filters plus coverage and
    freshness policy.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["RECORD", "REVISE", "QUERY"]
    observation: MarketNewsObservation | None = None
    revision: MarketNewsRevision | None = None
    as_of: UtcTimestamp | None = None
    from_at: UtcTimestamp | None = None
    to_at: UtcTimestamp | None = None
    source_id: NonEmptyStr | None = None
    category: NonEmptyStr | None = None
    language: NonEmptyStr | None = None
    impact: tuple[NewsImpact, ...] = ()
    require_complete_coverage: bool = False
    freshness_limit_seconds: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> TrackMarketNewsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or the QUERY interval is inverted.
        """
        query_fields = (
            ("as_of", self.as_of),
            ("from_at", self.from_at),
            ("to_at", self.to_at),
            ("source_id", self.source_id),
            ("category", self.category),
            ("language", self.language),
            ("freshness_limit_seconds", self.freshness_limit_seconds),
        )
        match self.operation:
            case "RECORD":
                _require_present((("observation", self.observation),))
                _require_absent((("revision", self.revision), *query_fields))
            case "REVISE":
                _require_present((("revision", self.revision),))
                _require_absent((("observation", self.observation), *query_fields))
            case "QUERY":
                _require_present(
                    (
                        ("as_of", self.as_of),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
                _require_absent(
                    (
                        ("observation", self.observation),
                        ("revision", self.revision),
                    )
                )
                if (
                    self.to_at is not None
                    and self.from_at is not None
                    and (self.to_at <= self.from_at)
                ):
                    raise ValueError("QUERY requires to_at after from_at")
        return self


class TrackMarketNewsSuccess(WireModel):
    """Successful economic calendar and news operation result."""

    request_id: Uuid7
    observation: MarketNewsObservation | None = None
    revision: MarketNewsRevision | None = None
    observations: tuple[MarketNewsObservation, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class StreamMarketEventsRequest(WireModel):
    """Operation-discriminated real-time market event request.

    BIND_FEED requires only ``provider_id``; FEED_STATE requires only
    ``feed_id``; REPLAY requires ``feed_id`` plus a positive interval.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["BIND_FEED", "FEED_STATE", "REPLAY"]
    provider_id: Uuid7 | None = None
    feed_id: Uuid7 | None = None
    from_at: UtcTimestamp | None = None
    to_at: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> StreamMarketEventsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or the REPLAY window is inverted.
        """
        match self.operation:
            case "BIND_FEED":
                _require_present((("provider_id", self.provider_id),))
                _require_absent(
                    (
                        ("feed_id", self.feed_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
            case "FEED_STATE":
                _require_present((("feed_id", self.feed_id),))
                _require_absent(
                    (
                        ("provider_id", self.provider_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
            case "REPLAY":
                _require_present(
                    (
                        ("feed_id", self.feed_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
                _require_absent((("provider_id", self.provider_id),))
                if (
                    self.to_at is not None
                    and self.from_at is not None
                    and (self.to_at <= self.from_at)
                ):
                    raise ValueError("REPLAY requires to_at after from_at")
        return self


class StreamMarketEventsSuccess(WireModel):
    """Successful real-time market event operation result."""

    request_id: Uuid7
    feed_state: MarketFeedState | None = None
    replay: MarketReplayRef | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class StreamMarketEventsSubscription(WireModel):
    """Owner-required live delivery subscription request.

    The subscription is the delivery companion of
    ``data.stream-market-events@1``: an absent provider/feed selector
    subscribes per the runtime default binding, ``resume_event_id``
    reconnects after interruption, and ``replay_limit`` bounds buffered
    replay per FR-DATA-BOUND_EVENT_BUFFERS.
    """

    provider_id: Uuid7 | None = None
    feed_id: Uuid7 | None = None
    instruments: tuple[InstrumentRef, ...] = ()
    resume_event_id: Uuid7 | None = None
    replay_limit: int = Field(default=0, ge=0, le=10000)
    schema_version: Literal[1] = 1


# TickType, DeduplicationPolicy, NewsImpact, ProfileSourceKind, and the
# other PEP 695 ``type`` aliases are not classes, so they cannot be
# registered in WIRE_MODELS.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "DataSeriesRef": DataSeriesRef,
    "SeriesInterval": SeriesInterval,
    "SeriesCoverage": SeriesCoverage,
    "DataSeriesVersion": DataSeriesVersion,
    "DataConnectionRef": DataConnectionRef,
    "DataImportPlan": DataImportPlan,
    "DataImportReceipt": DataImportReceipt,
    "Bar": Bar,
    "Tick": Tick,
    "DataQualityFinding": DataQualityFinding,
    "DataQualityDecision": DataQualityDecision,
    "AggregationSpec": AggregationSpec,
    "RetentionPolicy": RetentionPolicy,
    "AlignmentPolicy": AlignmentPolicy,
    "RunDataBinding": RunDataBinding,
    "AlignedSeries": AlignedSeries,
    "ConnectorProfile": ConnectorProfile,
    "ConnectorSyncPlan": ConnectorSyncPlan,
    "ConnectorSyncReceipt": ConnectorSyncReceipt,
    "VolumeProfileSource": VolumeProfileSource,
    "ExternalIndicatorSeriesVersion": ExternalIndicatorSeriesVersion,
    "SyntheticModelSpec": SyntheticModelSpec,
    "ScenarioTransform": ScenarioTransform,
    "ScenarioSeriesVersion": ScenarioSeriesVersion,
    "MarketNewsObservation": MarketNewsObservation,
    "MarketNewsRevision": MarketNewsRevision,
    "MarketEvent": MarketEvent,
    "MarketFeedState": MarketFeedState,
    "MarketReplayRef": MarketReplayRef,
    "QuantDataImportSpec": QuantDataImportSpec,
    "IngestHistoryRequest": IngestHistoryRequest,
    "IngestHistorySuccess": IngestHistorySuccess,
    "SyncConnectorsRequest": SyncConnectorsRequest,
    "SyncConnectorsSuccess": SyncConnectorsSuccess,
    "ImportQuantdataRequest": ImportQuantdataRequest,
    "ImportQuantdataSuccess": ImportQuantdataSuccess,
    "NormalizeTicksRequest": NormalizeTicksRequest,
    "NormalizeTicksSuccess": NormalizeTicksSuccess,
    "ResolveQualityRequest": ResolveQualityRequest,
    "ResolveQualitySuccess": ResolveQualitySuccess,
    "AggregateBarsRequest": AggregateBarsRequest,
    "AggregateBarsSuccess": AggregateBarsSuccess,
    "ManageRetentionRequest": ManageRetentionRequest,
    "ManageRetentionSuccess": ManageRetentionSuccess,
    "AlignSeriesRequest": AlignSeriesRequest,
    "AlignSeriesSuccess": AlignSeriesSuccess,
    "PrepareProfilesRequest": PrepareProfilesRequest,
    "PrepareProfilesSuccess": PrepareProfilesSuccess,
    "ImportIndicatorsRequest": ImportIndicatorsRequest,
    "ImportIndicatorsSuccess": ImportIndicatorsSuccess,
    "BindRunDataRequest": BindRunDataRequest,
    "BindRunDataSuccess": BindRunDataSuccess,
    "GenerateScenariosRequest": GenerateScenariosRequest,
    "GenerateScenariosSuccess": GenerateScenariosSuccess,
    "TrackMarketNewsRequest": TrackMarketNewsRequest,
    "TrackMarketNewsSuccess": TrackMarketNewsSuccess,
    "StreamMarketEventsRequest": StreamMarketEventsRequest,
    "StreamMarketEventsSuccess": StreamMarketEventsSuccess,
    "StreamMarketEventsSubscription": StreamMarketEventsSubscription,
}
