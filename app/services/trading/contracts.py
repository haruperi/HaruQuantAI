"""Canonical trading runtime contracts.

This module defines the broker-independent contracts shared by trading
actions, gates, execution coordination, state persistence, reconciliation, and
tool-facing response envelopes. It is intentionally import-safe and contains no
broker, database, secret, socket, thread, clock, or random-number side effects.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.utils.logger import logger
from app.utils.standard import SENSITIVE_KEY_PATTERN, SENSITIVE_VALUE_PATTERN

SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_VERSION = "1.0.0"
SCHEMA_VERSION_PARTS = 3

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


def validate_redacted_json_value(value: JsonValue, *, path: str = "$") -> None:
    """Validate that a JSON value contains no obvious unredacted secrets.

    Args:
        value: JSON-safe value to validate.
        path: Diagnostic path used in validation errors.

    Raises:
        ValueError: If a sensitive key or secret-like string is detected.
    """
    logger.debug("Validating redacted JSON value at {}.", path)
    if isinstance(value, str):
        if SENSITIVE_VALUE_PATTERN.search(value):
            message = f"Sensitive value detected at {path}."
            raise ValueError(message)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_redacted_json_value(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if SENSITIVE_KEY_PATTERN.search(key):
                message = f"Sensitive key detected at {path}.{key}."
                raise ValueError(message)
            validate_redacted_json_value(item, path=f"{path}.{key}")


class TradingContract(BaseModel):
    """Base model for trading contracts.

    Attributes:
        schema_version: Semantic schema version used for compatibility checks.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        use_enum_values=False,
    )

    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Semantic schema version in major.minor.patch form.",
    )

    @model_validator(mode="after")
    def validate_schema_version(self) -> TradingContract:
        """Validate schema compatibility for trading contracts.

        Returns:
            TradingContract: Validated contract instance.

        Raises:
            ValueError: If the schema version is malformed or uses an unknown
                future major version.
        """
        logger.debug(
            "Validating trading schema version for {}: {}",
            self.__class__.__name__,
            self.schema_version,
        )
        parts = self.schema_version.split(".")
        if len(parts) != SCHEMA_VERSION_PARTS:
            raise ValueError("schema_version must use major.minor.patch format.")
        try:
            major = int(parts[0])
            int(parts[1])
            int(parts[2])
        except ValueError as exc:
            raise ValueError("schema_version parts must be integers.") from exc
        if major > SUPPORTED_SCHEMA_MAJOR:
            raise ValueError("Unknown future major schema_version is rejected.")
        return self


class TradingRoute(StrEnum):
    """Supported trading runtime routes."""

    SIM = "sim"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE = "live"


class TradingAction(StrEnum):
    """Canonical platform-independent trading action names."""

    SUBMIT_ORDER = "submit_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    CLOSE_POSITION = "close_position"
    MODIFY_POSITION = "modify_position"
    REDUCE_EXPOSURE = "reduce_exposure"
    PAUSE_STRATEGY = "pause_strategy"
    RESUME_STRATEGY = "resume_strategy"
    SYNC_POSITIONS = "sync_positions"
    RECONCILE_STATE = "reconcile_state"
    TRIGGER_GLOBAL_KILL_SWITCH = "trigger_global_kill_switch"
    TRIGGER_STRATEGY_KILL_SWITCH = "trigger_strategy_kill_switch"
    TRIGGER_SYMBOL_KILL_SWITCH = "trigger_symbol_kill_switch"
    CANCEL_ALL_ORDERS = "cancel_all_orders"
    CLOSE_ALL_POSITIONS = "close_all_positions"


class SideEffectMode(StrEnum):
    """Side-effect classification for trading responses."""

    NONE = "none"
    PACKAGED_ONLY = "packaged_only"
    BROKER_MUTATION_ATTEMPTED = "broker_mutation_attempted"
    BROKER_MUTATION_CONFIRMED = "broker_mutation_confirmed"
    BROKER_MUTATION_REJECTED = "broker_mutation_rejected"
    UNKNOWN_OUTCOME = "unknown_outcome"
    INCIDENT = "incident"


class RetrySafety(StrEnum):
    """Retry safety classification for trading outcomes."""

    SAFE_TO_RETRY = "safe_to_retry"
    RETRY_AFTER_RECONCILIATION = "retry_after_reconciliation"
    RETRY_AFTER_DELAY = "retry_after_delay"
    DO_NOT_RETRY = "do_not_retry"


class TimeInForce(StrEnum):
    """Supported order time-in-force policies."""

    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"
    DAY = "DAY"


class FixExecutionState(StrEnum):
    """Granular FIX-style order and position lifecycle states."""

    SUBMITTED = "Submitted"
    PARTIALLY_FILLED = "Partially Filled"
    FILLED = "Filled"
    PENDING_CANCEL = "Pending Cancel"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    REPLACED = "Replaced"
    REJECTED = "Rejected"


class PromotionStage(StrEnum):
    """Trading promotion ladder stages."""

    OFFLINE_TEST = "offline_test"
    SIMULATION = "simulation"
    REPLAY = "replay"
    READ_ONLY_BROKER_CONNECTION = "read_only_broker_connection"
    PAPER_TRADING = "paper_trading"
    SHADOW_TRADING = "shadow_trading"
    MICRO_LIVE = "micro_live"
    FULL_LIVE = "full_live"


class MutationCapability(StrEnum):
    """Mutation capability allowed by a request context."""

    READ_ONLY = "read_only"
    PACKAGED_ONLY = "packaged_only"
    PAPER_ONLY = "paper_only"
    SHADOW_ONLY = "shadow_only"
    MICRO_LIVE = "micro_live"
    FULL_LIVE = "full_live"


class TradingStatus(StrEnum):
    """Public response status values."""

    SUCCESS = "success"
    ERROR = "error"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class AllocationVector(TradingContract):
    """Institutional block-trading allocation weights.

    Attributes:
        weights: Sub-account ID to volume-weight mapping.
    """

    weights: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Sub-account ID to non-negative volume weight.",
    )

    @field_serializer("weights")
    def serialize_weights(self, weights: dict[str, Decimal]) -> dict[str, str]:
        """Serialize Decimal weights as JSON-safe strings.

        Args:
            weights: Allocation weights to serialize.

        Returns:
            dict[str, str]: JSON-safe stringified decimal weights.
        """
        logger.debug("Serializing {} allocation weights.", len(weights))
        return {account_id: str(weight) for account_id, weight in weights.items()}

    @model_validator(mode="after")
    def validate_weights(self) -> AllocationVector:
        """Validate allocation vector entries.

        Returns:
            AllocationVector: Validated allocation vector.

        Raises:
            ValueError: If an account ID is blank, a weight is negative, or a
                non-empty vector sums to zero.
        """
        logger.info("Validating allocation vector with {} entries.", len(self.weights))
        total = Decimal(0)
        for account_id, weight in self.weights.items():
            if not account_id.strip():
                raise ValueError("Allocation account IDs must be non-empty.")
            if weight < 0:
                raise ValueError("Allocation weights must be non-negative.")
            total += weight
        if self.weights and total <= 0:
            raise ValueError("Allocation weights must sum to a positive value.")
        return self


class RegulatoryTags(TradingContract):
    """Regulatory metadata propagated to approved broker adapters.

    Attributes:
        mifid_algo_id: MiFID II algorithm identifier.
        short_sale_indicator: Short-sale indicator or locate flag.
        capacity: Principal or agency execution capacity.
        custom_tags: Namespaced additional regulatory tags.
    """

    mifid_algo_id: str | None = Field(default=None)
    short_sale_indicator: str | None = Field(default=None)
    capacity: str | None = Field(default=None)
    custom_tags: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_regulatory_tags(self) -> RegulatoryTags:
        """Validate optional regulatory tag payload.

        Returns:
            RegulatoryTags: Validated regulatory tags.

        Raises:
            ValueError: If capacity or custom tag names are invalid.
        """
        logger.info("Validating regulatory tags payload.")
        if self.capacity is not None and self.capacity not in {"principal", "agency"}:
            raise ValueError("capacity must be either principal or agency.")
        for key in self.custom_tags:
            if "." not in key and ":" not in key:
                raise ValueError("custom regulatory tag keys must be namespaced.")
        return self

    def to_broker_payload(self) -> JsonObject:
        """Return the JSON-safe broker adapter regulatory tag payload.

        Returns:
            JsonObject: Adapter-ready regulatory tag payload.
        """
        logger.info("Mapping regulatory tags to broker payload.")
        payload: JsonObject = {}
        if self.mifid_algo_id is not None:
            payload["mifid_algo_id"] = self.mifid_algo_id
        if self.short_sale_indicator is not None:
            payload["short_sale_indicator"] = self.short_sale_indicator
        if self.capacity is not None:
            payload["capacity"] = self.capacity
        if self.custom_tags:
            payload["custom_tags"] = dict(self.custom_tags)
        return payload


class QuoteSnapshot(TradingContract):
    """Quote evidence used for live-sensitive execution validation.

    Attributes:
        symbol: Quoted symbol.
        bid: Current bid.
        ask: Current ask.
        spread: Current spread.
        timestamp: UTC quote timestamp supplied by an injected Clock upstream.
        source: Quote source identifier.
        freshness_age_ms: Quote age in milliseconds at validation time.
        wire_timestamp: Optional PTP-aligned liquidity-provider timestamp.
    """

    symbol: str
    bid: Decimal
    ask: Decimal
    spread: Decimal
    timestamp: str
    source: str
    freshness_age_ms: int = Field(ge=0)
    wire_timestamp: str | None = None

    @field_serializer("bid", "ask", "spread")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal quote values as JSON-safe strings.

        Args:
            value: Decimal value to serialize.

        Returns:
            str: String representation of the decimal.
        """
        logger.debug("Serializing quote decimal value {}.", value)
        return str(value)

    @model_validator(mode="after")
    def validate_quote(self) -> QuoteSnapshot:
        """Validate quote snapshot price relationships.

        Returns:
            QuoteSnapshot: Validated quote snapshot.

        Raises:
            ValueError: If symbol/source are blank or quote prices are invalid.
        """
        logger.info("Validating quote snapshot for symbol {}.", self.symbol)
        if not self.symbol.strip():
            raise ValueError("quote_snapshot.symbol must be non-empty.")
        if not self.source.strip():
            raise ValueError("quote_snapshot.source must be non-empty.")
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("quote bid and ask must be positive.")
        if self.ask < self.bid:
            raise ValueError("quote ask must be greater than or equal to bid.")
        if self.spread < 0:
            raise ValueError("quote spread must be non-negative.")
        return self


class TradingError(TradingContract):
    """Structured public trading error details.

    Attributes:
        code: Stable error code.
        details: Redacted human-readable details.
    """

    code: str
    details: str

    @model_validator(mode="after")
    def validate_error(self) -> TradingError:
        """Validate the error detail contract.

        Returns:
            TradingError: Validated error details.

        Raises:
            ValueError: If code is blank.
        """
        logger.debug("Validating trading error code {}.", self.code)
        if not self.code.strip():
            raise ValueError("error code must be non-empty.")
        validate_redacted_json_value(self.details)
        return self


class TradingMetadata(TradingContract):
    """Public response metadata and side-effect flags.

    Attributes:
        execution_ms: Monotonic execution duration supplied by an injected Clock.
        reads: Whether the operation read external state.
        writes: Whether the operation wrote local state.
        updates: Whether the operation updated local state.
        deletes: Whether the operation deleted or cancelled local state.
        trades: Whether a trade mutation was attempted or confirmed.
        requires_network: Whether the operation required network access.
    """

    execution_ms: Decimal = Field(default=Decimal(0), ge=0)
    reads: bool = False
    writes: bool = False
    updates: bool = False
    deletes: bool = False
    trades: bool = False
    requires_network: bool = False

    @field_serializer("execution_ms")
    def serialize_execution_ms(self, value: Decimal) -> str:
        """Serialize execution duration as a JSON-safe string.

        Args:
            value: Decimal duration in milliseconds.

        Returns:
            str: String representation of the duration.
        """
        logger.debug("Serializing execution_ms {}.", value)
        return str(value)

    @model_validator(mode="after")
    def validate_metadata(self) -> TradingMetadata:
        """Validate metadata consistency.

        Returns:
            TradingMetadata: Validated metadata.
        """
        logger.info("Validated trading metadata with trades={}.", self.trades)
        return self


class TradingRequestEnvelope(TradingContract):
    """Canonical request envelope for trading runtime actions.

    Attributes:
        route: Requested runtime route.
        action: Requested trading action.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        symbol: Optional target symbol.
        payload: JSON-safe action payload.
        allocation_vector: Optional institutional allocation vector.
        regulatory_tags: Optional regulatory metadata.
        oco_group_id: Optional One-Cancels-Other group identifier.
        linked_order_ids: Optional sibling order IDs for bracket/OCO groups.
        quote_snapshot: Quote evidence mandatory for live mutations.
        deadline_utc: Optional pipeline evaluation deadline. When absent, the
            gate pipeline defaults it from the configured gate budget.
    """

    route: TradingRoute
    action: TradingAction
    promotion_stage: PromotionStage
    mutation_capability: MutationCapability
    request_id: str
    correlation_id: str
    symbol: str | None = None
    payload: JsonObject = Field(default_factory=dict)
    allocation_vector: AllocationVector | None = None
    regulatory_tags: RegulatoryTags | None = None
    oco_group_id: str | None = None
    linked_order_ids: tuple[str, ...] = Field(default_factory=tuple)
    quote_snapshot: QuoteSnapshot | None = None
    deadline_utc: str | None = None

    @model_validator(mode="after")
    def validate_request(self) -> TradingRequestEnvelope:
        """Validate request envelope safety requirements.

        Returns:
            TradingRequestEnvelope: Validated request envelope.

        Raises:
            ValueError: If required identifiers are blank, linked order IDs are
                invalid, or live mutations lack matching quote evidence.
        """
        logger.info(
            "Validating trading request {} for route {} and action {}.",
            self.request_id,
            self.route.value,
            self.action.value,
        )
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty.")
        if not self.correlation_id.strip():
            raise ValueError("correlation_id must be non-empty.")
        if self.symbol is not None and not self.symbol.strip():
            raise ValueError("symbol must be non-empty when provided.")
        if self.oco_group_id is not None and not self.oco_group_id.strip():
            raise ValueError("oco_group_id must be non-empty when provided.")
        for linked_order_id in self.linked_order_ids:
            if not linked_order_id.strip():
                raise ValueError("linked_order_ids must not contain blank IDs.")
        live_capabilities = {
            MutationCapability.MICRO_LIVE,
            MutationCapability.FULL_LIVE,
        }
        live_mutation = (
            self.route is TradingRoute.LIVE
            and self.mutation_capability in live_capabilities
        )
        if live_mutation:
            if self.quote_snapshot is None:
                raise ValueError("quote_snapshot is mandatory for live mutations.")
            if self.symbol is not None and self.quote_snapshot.symbol != self.symbol:
                raise ValueError("quote_snapshot symbol must match request symbol.")
        return self

    def to_broker_dispatch_payload(self) -> JsonObject:
        """Build a JSON-safe broker dispatch payload.

        Returns:
            JsonObject: Broker dispatch payload containing regulatory tags when
            present.
        """
        logger.info("Mapping trading request {} to broker payload.", self.request_id)
        payload: JsonObject = dict(self.payload)
        if self.regulatory_tags is not None:
            payload["regulatory_tags"] = self.regulatory_tags.to_broker_payload()
        if self.allocation_vector is not None:
            payload["allocation_vector"] = self.allocation_vector.model_dump(
                mode="json"
            )["weights"]
        if self.oco_group_id is not None:
            payload["oco_group_id"] = self.oco_group_id
        if self.linked_order_ids:
            payload["linked_order_ids"] = list(self.linked_order_ids)
        return payload


class NormalizedTradeResult(TradingContract):
    """Single normalized broker-facing trade result.

    This model is broker-facing and must be wrapped inside public envelope data,
    never exposed as a raw public response object.

    Attributes:
        retcode: Provider return code.
        deal: Provider deal identifier.
        order: Provider order identifier.
        volume: Executed volume.
        price: Executed price.
        bid: Bid observed by provider.
        ask: Ask observed by provider.
        comment: Provider comment, already redacted at the boundary.
        request_id: Request identifier.
        provider: Provider name.
    """

    retcode: str
    deal: str | None = None
    order: str | None = None
    volume: Decimal | None = None
    price: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    comment: str | None = None
    request_id: str
    provider: str

    @field_serializer("volume", "price", "bid", "ask")
    def serialize_optional_decimal(self, value: Decimal | None) -> str | None:
        """Serialize optional Decimal values as JSON-safe strings.

        Args:
            value: Optional decimal value.

        Returns:
            str | None: Stringified value or None.
        """
        logger.debug("Serializing normalized result decimal {}.", value)
        return None if value is None else str(value)

    @model_validator(mode="after")
    def validate_normalized_result(self) -> NormalizedTradeResult:
        """Validate normalized broker result identifiers.

        Returns:
            NormalizedTradeResult: Validated normalized result.

        Raises:
            ValueError: If required identifiers are blank.
        """
        logger.info("Validating normalized trade result from {}.", self.provider)
        if not self.retcode.strip():
            raise ValueError("retcode must be non-empty.")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty.")
        if not self.provider.strip():
            raise ValueError("provider must be non-empty.")
        return self


class TradingResponseEnvelope(TradingContract):
    """Canonical public response envelope for trading operations.

    Attributes:
        status: Outcome status.
        message: Human-readable redacted message.
        data: JSON-safe structured response payload.
        error: Optional structured error.
        metadata: Side-effect metadata.
        route: Runtime route.
        action: Trading action.
        side_effect_mode: Side-effect classification.
        retry_safety: Retry safety classification.
        request_id: Request identifier.
        correlation_id: Correlation identifier.
        audit_ref: Optional audit reference.
        retry_delay_ms: Optional retry delay.
    """

    status: TradingStatus
    message: str
    data: JsonObject = Field(default_factory=dict)
    error: TradingError | None = None
    metadata: TradingMetadata
    route: TradingRoute
    action: TradingAction
    side_effect_mode: SideEffectMode
    retry_safety: RetrySafety
    request_id: str
    correlation_id: str
    audit_ref: str | None = None
    retry_delay_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_response(self) -> TradingResponseEnvelope:
        """Validate response envelope fields.

        Returns:
            TradingResponseEnvelope: Validated response envelope.

        Raises:
            ValueError: If identifiers or message fields are blank.
        """
        logger.info(
            "Validating trading response {} for action {}.",
            self.request_id,
            self.action.value,
        )
        if not self.message.strip():
            raise ValueError("message must be non-empty.")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty.")
        if not self.correlation_id.strip():
            raise ValueError("correlation_id must be non-empty.")
        if self.audit_ref is not None and not self.audit_ref.strip():
            raise ValueError("audit_ref must be non-empty when provided.")
        validate_redacted_json_value(self.message)
        validate_redacted_json_value(self.data)
        return self

    @classmethod
    def accepted_from_command(
        cls,
        *,
        command: TradingCommandAccepted,
        route: TradingRoute,
        correlation_id: str,
        audit_ref: str | None = None,
    ) -> TradingResponseEnvelope:
        """Build the initial async response from local command acceptance.

        Args:
            command: Local command acceptance event.
            route: Runtime route for the accepted command.
            correlation_id: Correlation identifier.
            audit_ref: Optional audit reference.

        Returns:
            TradingResponseEnvelope: Accepted response that carries local
            command acceptance, not final broker confirmation.
        """
        logger.info(
            "Building local command accepted response for {}.",
            command.request_id,
        )
        return cls(
            status=TradingStatus.ACCEPTED,
            message="Command accepted locally.",
            data={"command_accepted": command.model_dump(mode="json")},
            error=None,
            metadata=TradingMetadata(writes=True),
            route=route,
            action=command.action,
            side_effect_mode=SideEffectMode.PACKAGED_ONLY,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            request_id=command.request_id,
            correlation_id=correlation_id,
            audit_ref=audit_ref,
        )


class OrderState(TradingContract):
    """Canonical order state projection.

    Attributes:
        order_id: Local order identifier.
        symbol: Order symbol.
        state: FIX execution state.
        volume: Original order volume.
        filled_volume: Cumulative filled volume.
        remaining_volume: Remaining open volume.
        vwap: Volume-weighted average fill price.
        regulatory_tags: Optional regulatory metadata.
        oco_group_id: Optional OCO group identifier.
        linked_order_ids: Linked sibling order identifiers.
    """

    order_id: str
    symbol: str
    state: FixExecutionState
    volume: Decimal = Field(ge=0)
    filled_volume: Decimal = Field(default=Decimal(0), ge=0)
    remaining_volume: Decimal = Field(default=Decimal(0), ge=0)
    vwap: Decimal | None = None
    regulatory_tags: RegulatoryTags | None = None
    oco_group_id: str | None = None
    linked_order_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_serializer("volume", "filled_volume", "remaining_volume", "vwap")
    def serialize_order_decimal(self, value: Decimal | None) -> str | None:
        """Serialize order Decimal fields as JSON-safe strings.

        Args:
            value: Optional decimal value.

        Returns:
            str | None: Stringified value or None.
        """
        logger.debug("Serializing order decimal {}.", value)
        return None if value is None else str(value)

    @model_validator(mode="after")
    def validate_order_state(self) -> OrderState:
        """Validate order state volume accounting.

        Returns:
            OrderState: Validated order state.

        Raises:
            ValueError: If identifiers are blank or volumes are inconsistent.
        """
        logger.info("Validating order state {}.", self.order_id)
        if not self.order_id.strip() or not self.symbol.strip():
            raise ValueError("order_id and symbol must be non-empty.")
        if self.filled_volume + self.remaining_volume > self.volume:
            raise ValueError("filled plus remaining volume cannot exceed volume.")
        return self


class PositionState(TradingContract):
    """Canonical position state projection.

    Attributes:
        position_id: Local position identifier.
        symbol: Position symbol.
        state: FIX-compatible position lifecycle state.
        volume: Current position volume.
        vwap: Position volume-weighted average price.
        regulatory_tags: Optional regulatory metadata.
        linked_order_ids: Order IDs associated with this position.
    """

    position_id: str
    symbol: str
    state: FixExecutionState
    volume: Decimal = Field(ge=0)
    vwap: Decimal | None = None
    regulatory_tags: RegulatoryTags | None = None
    linked_order_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_serializer("volume", "vwap")
    def serialize_position_decimal(self, value: Decimal | None) -> str | None:
        """Serialize position Decimal fields as JSON-safe strings.

        Args:
            value: Optional decimal value.

        Returns:
            str | None: Stringified value or None.
        """
        logger.debug("Serializing position decimal {}.", value)
        return None if value is None else str(value)

    @model_validator(mode="after")
    def validate_position_state(self) -> PositionState:
        """Validate position state identifiers.

        Returns:
            PositionState: Validated position state.

        Raises:
            ValueError: If identifiers are blank.
        """
        logger.info("Validating position state {}.", self.position_id)
        if not self.position_id.strip() or not self.symbol.strip():
            raise ValueError("position_id and symbol must be non-empty.")
        return self


class TradingCommandAccepted(TradingContract):
    """Local command acceptance event for asynchronous live execution."""

    request_id: str
    command_id: str
    accepted_at: str
    action: TradingAction


class TradingCommandRejected(TradingContract):
    """Local command rejection event."""

    request_id: str
    reason_code: str
    rejected_at: str
    action: TradingAction


class BrokerDispatchEvent(TradingContract):
    """Broker dispatch event emitted after local command acceptance."""

    request_id: str
    command_id: str
    broker_request_ref: str
    dispatched_at: str


class BrokerAcknowledgementEvent(TradingContract):
    """Broker acknowledgement event separated from final execution reports."""

    request_id: str
    broker_request_ref: str
    acknowledged_at: str
    normalized_result: NormalizedTradeResult


class ExecutionReportEvent(TradingContract):
    """Execution report event carrying normalized fill or reject facts."""

    request_id: str
    broker_event_id: str
    reported_at: str
    normalized_result: NormalizedTradeResult
    execution_state: FixExecutionState


class ReconciliationResolutionEvent(TradingContract):
    """Reconciliation resolution event after unknown or divergent outcomes."""

    request_id: str
    reconciliation_id: str
    resolved_at: str
    resolution: str
    retry_safety: RetrySafety


class TradingToolDefinition(TradingContract):
    """AI-facing trading tool metadata definition.

    Attributes:
        name: Unique tool name.
        purpose: Human-readable tool purpose.
        route_support: Supported runtime routes.
        input_schema: JSON Schema input contract.
        output_schema: JSON Schema output contract.
        approval_required: Whether backend approval is required.
        side_effect_ceiling: Maximum permitted side-effect mode.
        risk_level: Risk classification.
        error_codes: Stable error codes emitted by the tool.
        audit_metadata: JSON-safe audit metadata.
    """

    name: str
    purpose: str
    route_support: tuple[TradingRoute, ...]
    input_schema: JsonObject = Field(default_factory=dict)
    output_schema: JsonObject = Field(default_factory=dict)
    approval_required: bool
    side_effect_ceiling: SideEffectMode
    risk_level: str
    error_codes: tuple[str, ...] = Field(default_factory=tuple)
    audit_metadata: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tool_definition(self) -> TradingToolDefinition:
        """Validate trading tool metadata.

        Returns:
            TradingToolDefinition: Validated tool metadata.

        Raises:
            ValueError: If metadata is incomplete or mutation ceilings are too
                broad for AI-facing tools.
        """
        logger.info("Validating trading tool definition {}.", self.name)
        if not self.name.strip() or not self.purpose.strip():
            raise ValueError("Tool name and purpose must be non-empty.")
        if not self.route_support:
            raise ValueError("Tool route_support must not be empty.")
        if self.side_effect_ceiling not in {
            SideEffectMode.NONE,
            SideEffectMode.PACKAGED_ONLY,
        }:
            raise ValueError("AI-facing trading tools cannot broker mutations.")
        return self


class TradingToolRegistry(TradingContract):
    """Immutable catalog of approved trading tool definitions."""

    tools: dict[str, TradingToolDefinition] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registry(self) -> TradingToolRegistry:
        """Validate registry key and definition consistency.

        Returns:
            TradingToolRegistry: Validated trading tool registry.

        Raises:
            ValueError: If a registry key differs from its definition name.
        """
        logger.info("Validating trading tool registry with {} tools.", len(self.tools))
        for name, definition in self.tools.items():
            if name != definition.name:
                raise ValueError("Trading tool registry keys must match names.")
        return self
