"""Immutable canonical contracts for the Trading domain."""

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import Annotated, ClassVar, Final, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    field_validator,
    model_validator,
)

from app.utils import canonical_json, is_sensitive_key, logger, to_json_safe

TRADING_CONTRACT_VERSION: Final = "v1"

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type EnvelopeStatus = Literal[
    "success",
    "rejected",
    "blocked",
    "pending_approval",
    "packaged",
    "sent",
    "partial",
    "filled",
    "cancelled",
    "unknown_outcome",
    "error",
]
type TradingAction = Literal[
    "submit_order",
    "modify_order",
    "cancel_order",
    "close_position",
    "modify_position",
    "reduce_exposure",
    "pause_strategy",
    "resume_strategy",
    "sync_positions",
    "trigger_kill_switch",
    "clear_kill_switch",
    "cancel_all_orders",
    "close_all_positions",
    "portfolio_rebalance",
]
type OrderType = Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
type TimeInForce = Literal["GTC", "IOC", "FOK", "GTD", "DAY"]

_SHA256_HEX_LENGTH = 64


def _reject_float(value: object) -> object:
    """Reject binary floats from broker-critical Decimal material.

    Args:
        value: Candidate Decimal-compatible value.

    Returns:
        Original non-float value for Decimal parsing.

    Raises:
        TypeError: If the candidate is a binary float.
    """
    logger.debug("Rejecting unsafe binary float Trading material")
    if isinstance(value, float):
        raise TypeError("broker-critical numeric material cannot be a float")
    return value


type _ExactDecimal = Annotated[Decimal, BeforeValidator(_reject_float)]


def _validate_text(value: str, field_name: str) -> str:
    """Validate required canonical text.

    Args:
        value: Candidate text.
        field_name: Stable field name for the validation message.

    Returns:
        Validated text.

    Raises:
        ValueError: If the value is blank or has surrounding whitespace.
    """
    logger.debug("Validating Trading text field: %s", field_name)
    if not value or value != value.strip():
        message = f"{field_name} must be non-empty and trimmed"
        raise ValueError(message)
    return value


def _validate_optional_text(value: str | None, field_name: str) -> str | None:
    """Validate optional canonical text.

    Args:
        value: Candidate optional text.
        field_name: Stable field name for the validation message.

    Returns:
        Validated optional text.

    Raises:
        ValueError: If a supplied value is blank or untrimmed.
    """
    logger.debug("Validating optional Trading text field: %s", field_name)
    if value is None:
        return None
    return _validate_text(value, field_name)


def _validate_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field_name: Stable field name for the validation message.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the timestamp is naive or non-UTC.
    """
    logger.debug("Validating Trading UTC field: %s", field_name)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be timezone-aware UTC"
        raise ValueError(message)
    return value


def _validate_execution_price_shape(
    order_type: OrderType,
    limit_price: Decimal | None,
    stop_price: Decimal | None,
    subject: str,
) -> None:
    """Validate prices required by one explicit order type.

    Args:
        order_type: Chosen executable order type.
        limit_price: Optional caller-approved limit price.
        stop_price: Optional caller-approved trigger price.
        subject: Human-readable contract subject for errors.

    Raises:
        ValueError: If the supplied prices conflict with the order type.
    """
    logger.debug("Validating %s execution price shape", subject)
    if order_type == "MARKET" and (limit_price is not None or stop_price is not None):
        message = f"MARKET {subject} cannot carry trigger or limit prices"
        raise ValueError(message)
    if order_type == "LIMIT" and (limit_price is None or stop_price is not None):
        message = f"LIMIT {subject} require only a limit price"
        raise ValueError(message)
    if order_type == "STOP" and (stop_price is None or limit_price is not None):
        message = f"STOP {subject} require only a stop price"
        raise ValueError(message)
    if order_type == "STOP_LIMIT" and (stop_price is None or limit_price is None):
        message = f"STOP_LIMIT {subject} require stop and limit prices"
        raise ValueError(message)


def _validate_expiration_shape(
    time_in_force: TimeInForce | None,
    expiration: datetime | None,
    start_time: datetime,
    subject: str,
) -> None:
    """Validate GTD expiration material without deriving a default.

    Args:
        time_in_force: Caller-approved time-in-force value.
        expiration: Optional caller-approved expiration timestamp.
        start_time: Earliest permitted expiration instant.
        subject: Human-readable contract subject for errors.

    Raises:
        ValueError: If expiration evidence is missing or contradictory.
    """
    logger.debug("Validating %s expiration shape", subject)
    if time_in_force == "GTD" and expiration is None:
        message = f"GTD {subject} require expiration"
        raise ValueError(message)
    if time_in_force != "GTD" and expiration is not None:
        raise ValueError("expiration requires GTD time_in_force")
    if expiration is not None and expiration <= start_time:
        message = f"expiration must be later than {subject} start"
        raise ValueError(message)


def _validate_intent_targets(
    action: TradingAction,
    target_order_id: str | None,
    target_position_id: str | None,
) -> None:
    """Validate receiver-owned broker target identifiers for mutations.

    Args:
        action: Trading action to execute.
        target_order_id: Broker order identifier read from Trading state.
        target_position_id: Broker position identifier read from Trading state.

    Raises:
        ValueError: If target evidence conflicts with the requested action.
    """
    logger.debug("Validating OrderIntent broker targets for %s", action)
    if action == "submit_order" and (
        target_order_id is not None or target_position_id is not None
    ):
        raise ValueError("new orders cannot carry target broker identifiers")
    if action in {"modify_order", "cancel_order"} and (
        target_order_id is None or target_position_id is not None
    ):
        raise ValueError("order mutations require only target_broker_order_id")
    if action in {
        "close_position",
        "modify_position",
        "reduce_exposure",
    } and (target_position_id is None or target_order_id is not None):
        raise ValueError("position mutations require only target_broker_position_id")


def _validate_decimal(
    value: Decimal | None,
    field_name: str,
    *,
    positive: bool = False,
    non_negative: bool = False,
) -> Decimal | None:
    """Validate an exact finite Decimal.

    Args:
        value: Candidate Decimal.
        field_name: Stable field name for the validation message.
        positive: Whether zero and negative values are forbidden.
        non_negative: Whether negative values are forbidden.

    Returns:
        Validated Decimal or ``None``.

    Raises:
        ValueError: If the value is non-finite or violates its sign constraint.
    """
    logger.debug("Validating Trading Decimal field: %s", field_name)
    if value is None:
        return None
    if not isinstance(value, Decimal) or not value.is_finite():
        message = f"{field_name} must be a finite Decimal"
        raise ValueError(message)
    if positive and value <= 0:
        message = f"{field_name} must be positive"
        raise ValueError(message)
    if non_negative and value < 0:
        message = f"{field_name} must be non-negative"
        raise ValueError(message)
    return value


def _freeze_json_mapping(value: Mapping[str, object]) -> Mapping[str, JsonValue]:
    """Validate and freeze one JSON-safe mapping.

    Args:
        value: Source mapping.

    Returns:
        Immutable JSON-safe mapping.

    Raises:
        TypeError: If the value does not serialize to a mapping.
        ValueError: If the mapping is not JSON-safe.
    """
    logger.debug("Freezing canonical Trading mapping")
    safe = to_json_safe(value)
    if not isinstance(safe, dict):
        raise TypeError("value must be a JSON-safe mapping")
    return MappingProxyType(safe)


def _contains_sensitive_key(value: JsonValue) -> bool:
    """Return whether material contains a protected key with unredacted value.

    Args:
        value: JSON-safe boundary material to inspect recursively.

    Returns:
        Whether any nested sensitive key retains a value other than the canonical
        redaction marker.
    """
    logger.debug("Checking Trading boundary material for sensitive keys")
    if isinstance(value, dict):
        return any(
            (is_sensitive_key(key) and item != "[REDACTED]")
            or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


class _TradingModel(BaseModel):
    """Strict immutable base for Trading-owned contracts."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
        allow_inf_nan=False,
    )


class TradingRoute(StrEnum):
    """Supported Trading execution routes."""

    SIM = "sim"
    PAPER = "paper"
    LIVE = "live"


class TradingRequest(_TradingModel):
    """Canonical governed request entering Trading.

    Attributes:
        request_id: Unique request trace identifier.
        workflow_id: Workflow trace identifier.
        correlation_id: Cross-domain correlation identifier.
        route: Selected execution route.
        action: Requested Trading action.
        idempotency_key: Caller-controlled duplicate-detection key.
        risk_decision_id: Exact Risk decision reference.
    """

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.trading_request.v1"] = "trading.trading_request.v1"
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    route: TradingRoute
    action: TradingAction
    provider_id: str | None = None
    account_id: str
    portfolio_id: str | None = None
    strategy_id: str
    strategy_version: str
    intent_id: str
    symbol: str | None = None
    side: Literal["BUY", "SELL"] | None = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity_unit: str
    quantity: _ExactDecimal | None = None
    price: _ExactDecimal | None = None
    stop_price: _ExactDecimal | None = None
    stop_loss: _ExactDecimal | None = None
    take_profit: _ExactDecimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    expiration: datetime | None = None
    target_broker_order_id: str | None = None
    target_broker_position_id: str | None = None
    order_id: str | None = None
    position_id: str | None = None
    expected_version: int | None = None
    risk_decision_id: str
    action_policy_verdict_id: str
    approval_token_ref: str
    eligibility_decision_id: str | None = None
    allocation_decision_id: str | None = None
    scope_level: Literal["global", "portfolio", "strategy", "symbol"] | None = None
    control_reason: str | None = None
    idempotency_key: str
    canonical_material_version: str
    system_time: datetime
    broker_time: datetime | None = None
    valid_until: datetime
    instrument_min_quantity: _ExactDecimal | None = None
    instrument_max_quantity: _ExactDecimal | None = None
    instrument_quantity_step: _ExactDecimal | None = None
    instrument_price_tick: _ExactDecimal | None = None
    redaction_applied: Literal[True] = True

    @field_validator(
        "request_id",
        "workflow_id",
        "correlation_id",
        "account_id",
        "strategy_id",
        "strategy_version",
        "intent_id",
        "quantity_unit",
        "risk_decision_id",
        "action_policy_verdict_id",
        "approval_token_ref",
        "idempotency_key",
        "canonical_material_version",
    )
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate required request text.

        Args:
            value: Candidate field value.

        Returns:
            Validated text.

        Raises:
            ValueError: If the value is blank or untrimmed.
        """
        logger.debug("Validating required TradingRequest text")
        return _validate_text(value, "request text")

    @field_validator(
        "causation_id",
        "provider_id",
        "portfolio_id",
        "symbol",
        "order_id",
        "position_id",
        "target_broker_order_id",
        "target_broker_position_id",
        "eligibility_decision_id",
        "allocation_decision_id",
        "control_reason",
    )
    @classmethod
    def _validate_optional_request_text(cls, value: str | None) -> str | None:
        """Validate optional request text.

        Args:
            value: Candidate optional value.

        Returns:
            Validated optional text.

        Raises:
            ValueError: If a supplied value is blank or untrimmed.
        """
        logger.debug("Validating optional TradingRequest text")
        return _validate_optional_text(value, "optional request text")

    @field_validator(
        "quantity",
        "instrument_min_quantity",
        "instrument_max_quantity",
        "instrument_quantity_step",
        "instrument_price_tick",
    )
    @classmethod
    def _validate_positive_decimals(cls, value: Decimal | None) -> Decimal | None:
        """Validate positive quantity-related Decimals.

        Args:
            value: Candidate exact Decimal.

        Returns:
            Validated Decimal or ``None``.

        Raises:
            ValueError: If the value is non-finite or not positive.
        """
        logger.debug("Validating positive TradingRequest Decimal")
        return _validate_decimal(value, "quantity value", positive=True)

    @field_validator("price", "stop_price", "stop_loss", "take_profit")
    @classmethod
    def _validate_price_decimals(cls, value: Decimal | None) -> Decimal | None:
        """Validate optional finite price Decimals.

        Args:
            value: Candidate exact Decimal.

        Returns:
            Validated Decimal or ``None``.

        Raises:
            ValueError: If the value is non-finite.
        """
        logger.debug("Validating TradingRequest price Decimal")
        return _validate_decimal(value, "price value")

    @field_validator("system_time", "broker_time", "valid_until", "expiration")
    @classmethod
    def _validate_request_time(cls, value: datetime | None) -> datetime | None:
        """Validate request UTC evidence.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp or ``None``.

        Raises:
            ValueError: If the timestamp is naive or non-UTC.
        """
        logger.debug("Validating TradingRequest time evidence")
        if value is None:
            return None
        return _validate_utc(value, "request timestamp")

    @model_validator(mode="after")
    def _validate_request_invariants(self) -> Self:
        """Validate route, authority, and validity invariants.

        Returns:
            Validated request.

        Raises:
            ValueError: If route evidence, validity, or addressing conflicts.
        """
        logger.debug("Validating canonical TradingRequest invariants")
        if (
            self.route in {TradingRoute.PAPER, TradingRoute.LIVE}
            and self.provider_id is None
        ):
            raise ValueError("paper/live requests require provider_id")
        if self.valid_until <= self.system_time:
            raise ValueError("valid_until must be later than system_time")
        _validate_expiration_shape(
            self.time_in_force,
            self.expiration,
            self.system_time,
            "requests",
        )
        _validate_execution_price_shape(
            self.order_type,
            self.price,
            self.stop_price,
            "requests",
        )
        if self.expected_version is not None and self.expected_version < 0:
            raise ValueError("expected_version must be non-negative")
        if self.scope_level == "portfolio" and self.portfolio_id is None:
            raise ValueError("portfolio kill-switch scope requires portfolio_id")
        if self.scope_level == "symbol" and self.symbol is None:
            raise ValueError("symbol kill-switch scope requires symbol")
        if (
            self.instrument_min_quantity
            and self.instrument_max_quantity
            and self.instrument_min_quantity > self.instrument_max_quantity
        ):
            raise ValueError("instrument quantity bounds are inverted")
        return self


class StandardTradingEnvelope(_TradingModel):
    """Finite JSON-safe result envelope returned by Trading.

    Attributes:
        status: Canonical finite outcome state.
        message: Bounded human-readable summary.
        data: Optional JSON-safe result data.
        errors: Structured redacted errors.
        warnings: Structured redacted warnings.
        audit_metadata: Required trace and operation evidence.
    """

    status: EnvelopeStatus
    message: str
    data: JsonValue | None
    errors: tuple[Mapping[str, JsonValue], ...]
    warnings: tuple[Mapping[str, JsonValue], ...]
    audit_metadata: Mapping[str, JsonValue]

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        """Validate envelope message.

        Args:
            value: Candidate message.

        Returns:
            Validated message.

        Raises:
            ValueError: If the message is blank or untrimmed.
        """
        logger.debug("Validating StandardTradingEnvelope message")
        return _validate_text(value, "message")

    @field_validator("data", mode="before")
    @classmethod
    def _validate_data(cls, value: object) -> JsonValue:
        """Convert envelope data to JSON-safe form.

        Args:
            value: Candidate result data.

        Returns:
            JSON-safe result data.
        """
        logger.debug("Validating StandardTradingEnvelope data")
        return to_json_safe(value)

    @field_validator("errors", "warnings", mode="before")
    @classmethod
    def _validate_evidence_rows(
        cls, value: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, JsonValue], ...]:
        """Validate and freeze envelope evidence rows.

        Args:
            value: Candidate evidence rows.

        Returns:
            Immutable JSON-safe evidence rows.
        """
        logger.debug("Validating StandardTradingEnvelope evidence rows")
        return tuple(_freeze_json_mapping(row) for row in value)

    @field_validator("audit_metadata", mode="before")
    @classmethod
    def _validate_audit_metadata(
        cls, value: Mapping[str, object]
    ) -> Mapping[str, JsonValue]:
        """Validate required audit metadata.

        Args:
            value: Candidate audit metadata.

        Returns:
            Immutable JSON-safe audit metadata.

        Raises:
            ValueError: If metadata is absent or not JSON-safe.
        """
        logger.debug("Validating StandardTradingEnvelope audit metadata")
        if not value:
            raise ValueError("audit_metadata must not be empty")
        return _freeze_json_mapping(value)

    @model_validator(mode="after")
    def _validate_status_evidence(self) -> Self:
        """Validate status and error consistency.

        Returns:
            Validated envelope.

        Raises:
            ValueError: If success/error evidence conflicts with status.
        """
        logger.debug("Validating StandardTradingEnvelope status evidence")
        if self.status == "error" and not self.errors:
            raise ValueError("error status requires error evidence")
        if (
            self.status
            not in {
                "error",
                "rejected",
                "blocked",
                "unknown_outcome",
            }
            and self.errors
        ):
            raise ValueError("non-failure status cannot contain errors")
        material = to_json_safe(
            {
                "data": self.data,
                "errors": self.errors,
                "warnings": self.warnings,
                "audit_metadata": self.audit_metadata,
            }
        )
        if _contains_sensitive_key(material):
            raise ValueError("Trading envelope contains unredacted sensitive keys")
        return self


class OrderIntent(_TradingModel):
    """Deterministic executable intent produced after Risk approval.

    Attributes:
        client_order_id: Stable Trading-owned order identifier.
        route: Selected authority route.
        approved_volume: Exact executable Risk-approved volume.
        risk_approved_volume: Original Risk-approved volume for equality checking.
        idempotency_hash: Canonical SHA-256 material digest.
    """

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.order_intent.v1"] = "trading.order_intent.v1"
    client_order_id: str
    request_id: str
    workflow_id: str
    correlation_id: str
    route: TradingRoute
    provider_id: str | None
    account_id: str
    strategy_id: str
    strategy_version: str
    source_intent_id: str
    symbol: str
    action: TradingAction
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity_unit: str
    approved_volume: _ExactDecimal
    risk_approved_volume: _ExactDecimal
    price: _ExactDecimal | None = None
    stop_price: _ExactDecimal | None = None
    stop_loss: _ExactDecimal | None = None
    take_profit: _ExactDecimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    expiration: datetime | None = None
    target_broker_order_id: str | None = None
    target_broker_position_id: str | None = None
    idempotency_hash: str
    canonical_material_version: str
    risk_decision_id: str
    action_policy_verdict_id: str
    approval_token_ref: str
    created_at: datetime
    valid_until: datetime

    @field_validator(
        "client_order_id",
        "request_id",
        "workflow_id",
        "correlation_id",
        "account_id",
        "strategy_id",
        "strategy_version",
        "source_intent_id",
        "symbol",
        "quantity_unit",
        "canonical_material_version",
        "risk_decision_id",
        "action_policy_verdict_id",
        "approval_token_ref",
    )
    @classmethod
    def _validate_intent_text(cls, value: str) -> str:
        """Validate required order-intent text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating OrderIntent text")
        return _validate_text(value, "order intent text")

    @field_validator(
        "provider_id",
        "target_broker_order_id",
        "target_broker_position_id",
    )
    @classmethod
    def _validate_intent_provider(cls, value: str | None) -> str | None:
        """Validate optional intent provider.

        Args:
            value: Candidate provider identifier.

        Returns:
            Validated optional provider.

        Raises:
            ValueError: If supplied provider text is invalid.
        """
        logger.debug("Validating OrderIntent provider")
        return _validate_optional_text(value, "provider_id")

    @field_validator("approved_volume", "risk_approved_volume")
    @classmethod
    def _validate_intent_volume(cls, value: Decimal) -> Decimal:
        """Validate exact positive intent volume.

        Args:
            value: Candidate volume.

        Returns:
            Validated positive Decimal.

        Raises:
            ValueError: If volume is non-finite or not positive.
        """
        logger.debug("Validating OrderIntent volume")
        validated = _validate_decimal(value, "intent volume", positive=True)
        if validated is None:
            raise ValueError("intent volume is required")
        return validated

    @field_validator("price", "stop_price", "stop_loss", "take_profit")
    @classmethod
    def _validate_intent_price(cls, value: Decimal | None) -> Decimal | None:
        """Validate optional intent price.

        Args:
            value: Candidate price.

        Returns:
            Validated price or ``None``.

        Raises:
            ValueError: If the price is non-finite.
        """
        logger.debug("Validating OrderIntent price")
        return _validate_decimal(value, "intent price")

    @field_validator("idempotency_hash")
    @classmethod
    def _validate_intent_hash(cls, value: str) -> str:
        """Validate a SHA-256 intent digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated lowercase digest.

        Raises:
            ValueError: If the digest is not lowercase SHA-256 hexadecimal.
        """
        logger.debug("Validating OrderIntent idempotency hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("idempotency_hash must be lowercase SHA-256 hex")
        return value

    @field_validator("created_at", "valid_until", "expiration")
    @classmethod
    def _validate_intent_time(cls, value: datetime | None) -> datetime | None:
        """Validate intent UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp or ``None``.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating OrderIntent time")
        if value is None:
            return None
        return _validate_utc(value, "intent timestamp")

    @model_validator(mode="after")
    def _validate_intent_invariants(self) -> Self:
        """Validate Risk-size, route, and validity invariants.

        Returns:
            Validated order intent.

        Raises:
            ValueError: If executable size or authority evidence conflicts.
        """
        logger.debug("Validating OrderIntent invariants")
        if self.approved_volume != self.risk_approved_volume:
            raise ValueError("OrderIntent must preserve exact Risk-approved size")
        if (
            self.route in {TradingRoute.PAPER, TradingRoute.LIVE}
            and self.provider_id is None
        ):
            raise ValueError("paper/live intent requires provider_id")
        if self.valid_until <= self.created_at:
            raise ValueError("intent validity must end after creation")
        _validate_expiration_shape(
            self.time_in_force,
            self.expiration,
            self.created_at,
            "intents",
        )
        _validate_execution_price_shape(
            self.order_type,
            self.price,
            self.stop_price,
            "intents",
        )
        _validate_intent_targets(
            self.action,
            self.target_broker_order_id,
            self.target_broker_position_id,
        )
        return self


class ExecutionReceipt(_TradingModel):
    """Immutable route-authority response classification.

    Attributes:
        status: Finite authority outcome.
        retry_safe: Whether the exact action is proven safe to retry.
        reconciliation_required: Whether authority comparison is mandatory.
    """

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.execution_receipt.v1"] = "trading.execution_receipt.v1"
    receipt_id: str
    intent_id: str
    client_order_id: str
    route: TradingRoute
    authority: str
    provider_order_id: str | None = None
    provider_deal_ids: tuple[str, ...] = ()
    status: Literal[
        "accepted",
        "rejected",
        "partial",
        "filled",
        "cancelled",
        "unknown_outcome",
    ]
    requested_quantity: _ExactDecimal
    filled_quantity: _ExactDecimal
    average_price: _ExactDecimal | None = None
    authority_timestamp: datetime
    received_at: datetime
    response_classification: str
    retry_safe: bool
    reconciliation_required: bool
    request_id: str
    correlation_id: str

    @field_validator(
        "receipt_id",
        "intent_id",
        "client_order_id",
        "authority",
        "response_classification",
        "request_id",
        "correlation_id",
    )
    @classmethod
    def _validate_receipt_text(cls, value: str) -> str:
        """Validate required receipt text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating ExecutionReceipt text")
        return _validate_text(value, "receipt text")

    @field_validator("provider_order_id")
    @classmethod
    def _validate_provider_order_id(cls, value: str | None) -> str | None:
        """Validate optional provider order identity.

        Args:
            value: Candidate provider order identifier.

        Returns:
            Validated optional identifier.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating ExecutionReceipt provider order id")
        return _validate_optional_text(value, "provider_order_id")

    @field_validator("provider_deal_ids")
    @classmethod
    def _validate_provider_deal_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate provider deal identifiers.

        Args:
            value: Candidate deal identifiers.

        Returns:
            Validated identifiers.

        Raises:
            ValueError: If identifiers are blank, untrimmed, or duplicated.
        """
        logger.debug("Validating ExecutionReceipt deal ids")
        validated = tuple(_validate_text(item, "provider_deal_id") for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("provider deal identifiers must be unique")
        return validated

    @field_validator("requested_quantity", "filled_quantity")
    @classmethod
    def _validate_receipt_quantity(cls, value: Decimal) -> Decimal:
        """Validate non-negative receipt quantity.

        Args:
            value: Candidate quantity.

        Returns:
            Validated quantity.

        Raises:
            ValueError: If quantity is non-finite or negative.
        """
        logger.debug("Validating ExecutionReceipt quantity")
        validated = _validate_decimal(value, "receipt quantity", non_negative=True)
        if validated is None:
            raise ValueError("receipt quantity is required")
        return validated

    @field_validator("average_price")
    @classmethod
    def _validate_receipt_price(cls, value: Decimal | None) -> Decimal | None:
        """Validate optional average fill price.

        Args:
            value: Candidate average price.

        Returns:
            Validated average price or ``None``.

        Raises:
            ValueError: If price is non-finite.
        """
        logger.debug("Validating ExecutionReceipt average price")
        return _validate_decimal(value, "average_price")

    @field_validator("authority_timestamp", "received_at")
    @classmethod
    def _validate_receipt_time(cls, value: datetime) -> datetime:
        """Validate receipt UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating ExecutionReceipt timestamp")
        return _validate_utc(value, "receipt timestamp")

    @model_validator(mode="after")
    def _validate_receipt_invariants(self) -> Self:
        """Validate authority, fill, and retry evidence.

        Returns:
            Validated receipt.

        Raises:
            ValueError: If authority outcome evidence is inconsistent.
        """
        logger.debug("Validating ExecutionReceipt invariants")
        if self.filled_quantity > self.requested_quantity:
            raise ValueError("filled quantity cannot exceed requested quantity")
        if self.status in {"filled", "partial"} and self.filled_quantity <= 0:
            raise ValueError("filled or partial receipt requires a positive fill")
        if self.status == "unknown_outcome" and (
            self.retry_safe or not self.reconciliation_required
        ):
            raise ValueError(
                "unknown outcome must block retry and require reconciliation"
            )
        if (
            self.status in {"accepted", "filled", "partial"}
            and self.provider_order_id is None
        ):
            raise ValueError("acknowledged receipt requires authority order identity")
        return self


class TradeRecord(_TradingModel):
    """Official immutable execution and reconciliation record.

    Attributes:
        receipt: Canonical authority receipt.
        reconciliation_state: Explicit reconciliation truth.
        incidents: Bounded incident references.
    """

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.trade_record.v1"] = "trading.trade_record.v1"
    record_id: str
    receipt: ExecutionReceipt
    fill_ids: tuple[str, ...]
    commission: _ExactDecimal | None = None
    spread_cost: _ExactDecimal | None = None
    slippage_cost: _ExactDecimal | None = None
    cost_currency_or_unit: str | None = None
    authority_state: str
    reconciliation_state: Literal["reconciled", "unreconciled", "blocked"]
    warnings: tuple[str, ...] = ()
    incidents: tuple[str, ...] = ()
    created_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator(
        "record_id",
        "authority_state",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_record_text(cls, value: str) -> str:
        """Validate required trade-record text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating TradeRecord text")
        return _validate_text(value, "trade record text")

    @field_validator("cost_currency_or_unit")
    @classmethod
    def _validate_cost_unit(cls, value: str | None) -> str | None:
        """Validate optional cost unit.

        Args:
            value: Candidate cost unit.

        Returns:
            Validated optional unit.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating TradeRecord cost unit")
        return _validate_optional_text(value, "cost_currency_or_unit")

    @field_validator("fill_ids", "warnings", "incidents")
    @classmethod
    def _validate_record_rows(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate record identifiers and evidence rows.

        Args:
            value: Candidate text tuple.

        Returns:
            Validated tuple.

        Raises:
            ValueError: If an item is blank or untrimmed.
        """
        logger.debug("Validating TradeRecord evidence rows")
        return tuple(_validate_text(item, "record evidence") for item in value)

    @field_validator("commission", "spread_cost", "slippage_cost")
    @classmethod
    def _validate_cost(cls, value: Decimal | None) -> Decimal | None:
        """Validate factual non-negative cost.

        Args:
            value: Candidate cost.

        Returns:
            Validated cost or ``None``.

        Raises:
            ValueError: If cost is non-finite or negative.
        """
        logger.debug("Validating TradeRecord factual cost")
        return _validate_decimal(value, "execution cost", non_negative=True)

    @field_validator("created_at")
    @classmethod
    def _validate_record_time(cls, value: datetime) -> datetime:
        """Validate record UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating TradeRecord timestamp")
        return _validate_utc(value, "record timestamp")

    @model_validator(mode="after")
    def _validate_record_invariants(self) -> Self:
        """Validate reconciliation and factual-cost evidence.

        Returns:
            Validated trade record.

        Raises:
            ValueError: If reconciliation or cost evidence is inconsistent.
        """
        logger.debug("Validating TradeRecord invariants")
        costs = (self.commission, self.spread_cost, self.slippage_cost)
        if (
            any(value is not None for value in costs)
            and self.cost_currency_or_unit is None
        ):
            raise ValueError("factual costs require currency or unit evidence")
        if (
            self.receipt.reconciliation_required
            and self.reconciliation_state == "reconciled"
        ):
            raise ValueError("receipt requiring reconciliation cannot start reconciled")
        return self


_REBALANCE_ACTION_FIELDS = {
    "action_id",
    "component_id",
    "eligibility_decision_id",
    "action",
    "reduce_only",
    "current_exposure",
    "target_exposure",
    "reduction_amount",
}
_REBALANCE_TEXT_FIELDS = (
    "action_id",
    "component_id",
    "eligibility_decision_id",
)


def _rebalance_decimal(value: JsonValue, field: str) -> Decimal | None:
    """Parse one optional canonical rebalance Decimal.

    Args:
        value: JSON-safe Decimal text or null.
        field: Field name for deterministic errors.

    Returns:
        Parsed Decimal or ``None``.

    Raises:
        TypeError: If a supplied value is not text.
        ValueError: If text is not a finite Decimal.
    """
    logger.debug("Parsing rebalance Decimal field %s", field)
    if value is None:
        return None
    if not isinstance(value, str):
        message = f"rebalance {field} must serialize as text"
        raise TypeError(message)
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("rebalance Decimal text is invalid") from error
    if not parsed.is_finite():
        raise ValueError("rebalance Decimal must be finite")
    return parsed


def _validate_rebalance_action(
    action: Mapping[str, object],
) -> tuple[str, Mapping[str, JsonValue]]:
    """Validate one complete deterministic rebalance action row.

    Args:
        action: Candidate action mapping.

    Returns:
        Validated action identity and frozen JSON-safe mapping.

    Raises:
        TypeError: If required types are invalid.
        ValueError: If action material conflicts with the contract.
    """
    logger.debug("Validating one rebalance action row")
    safe = _freeze_json_mapping(action)
    if set(safe) != _REBALANCE_ACTION_FIELDS:
        raise ValueError("rebalance action fields do not match the contract")
    for field in _REBALANCE_TEXT_FIELDS:
        field_value = safe[field]
        if not isinstance(field_value, str):
            message = f"rebalance {field} must be text"
            raise TypeError(message)
        _validate_text(field_value, field)
    if safe["action"] != "reduce_exposure" or safe["reduce_only"] is not True:
        raise ValueError("rebalance action must be reduce-only reduce_exposure")
    current = _rebalance_decimal(safe["current_exposure"], "current_exposure")
    target = _rebalance_decimal(safe["target_exposure"], "target_exposure")
    reduction = _rebalance_decimal(safe["reduction_amount"], "reduction_amount")
    if (
        current is None
        or target is None
        or reduction is None
        or current <= target
        or target < 0
        or reduction <= 0
        or reduction != current - target
    ):
        raise ValueError("rebalance exposure reduction is invalid")
    return str(safe["action_id"]), safe


class PortfolioRebalanceExecutionRequest(_TradingModel):
    """Receiver-owned request for one authorized immutable rebalance plan.

    Attributes:
        plan_id: Immutable Portfolio rebalance plan reference.
        allocation_version: Exact target allocation version.
        actions: Ordered self-contained action projections.
        canonical_hash: SHA-256 digest over all canonical material except itself.
    """

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.portfolio_rebalance_execution_request.v1"] = (
        "trading.portfolio_rebalance_execution_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    plan_id: str
    plan_version: str
    portfolio_id: str
    allocation_version: str
    allocation_decision_id: str
    eligibility_decision_ids: tuple[str, ...]
    actions: tuple[Mapping[str, JsonValue], ...]
    route: TradingRoute
    approval_token_ref: str
    canonical_material_version: str
    valid_from: datetime
    valid_until: datetime
    canonical_hash: str

    _HASHED_FIELDS: ClassVar[tuple[str, ...]] = (
        "contract_version",
        "schema_id",
        "request_id",
        "workflow_id",
        "correlation_id",
        "plan_id",
        "plan_version",
        "portfolio_id",
        "allocation_version",
        "allocation_decision_id",
        "eligibility_decision_ids",
        "actions",
        "route",
        "approval_token_ref",
        "canonical_material_version",
        "valid_from",
        "valid_until",
    )

    @field_validator(
        "request_id",
        "workflow_id",
        "correlation_id",
        "plan_id",
        "plan_version",
        "portfolio_id",
        "allocation_version",
        "allocation_decision_id",
        "approval_token_ref",
        "canonical_material_version",
    )
    @classmethod
    def _validate_rebalance_text(cls, value: str) -> str:
        """Validate required rebalance text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating rebalance request text")
        return _validate_text(value, "rebalance request text")

    @field_validator("eligibility_decision_ids")
    @classmethod
    def _validate_eligibility_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate exact eligibility-decision references.

        Args:
            value: Candidate decision identifiers.

        Returns:
            Validated identifiers.

        Raises:
            ValueError: If references are absent, invalid, or duplicated.
        """
        logger.debug("Validating rebalance eligibility references")
        validated = tuple(
            _validate_text(item, "eligibility decision id") for item in value
        )
        if not validated or len(set(validated)) != len(validated):
            raise ValueError("eligibility decision ids must be non-empty and unique")
        return validated

    @field_validator("actions", mode="before")
    @classmethod
    def _validate_actions(
        cls, value: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, JsonValue], ...]:
        """Validate ordered self-contained rebalance actions.

        Args:
            value: Candidate action projections.

        Returns:
            Immutable JSON-safe action projections.

        Raises:
            TypeError: If an action identity is not text.
            ValueError: If actions are absent, malformed, duplicated, or not
                reduce-only.
        """
        logger.debug("Validating ordered rebalance actions")
        if not value:
            raise ValueError("rebalance request requires ordered actions")
        frozen: list[Mapping[str, JsonValue]] = []
        action_ids: list[str] = []
        for action in value:
            action_id, safe = _validate_rebalance_action(action)
            action_ids.append(action_id)
            frozen.append(safe)
        if len(set(action_ids)) != len(action_ids):
            raise ValueError("rebalance action ids must be unique")
        return tuple(frozen)

    @field_validator("valid_from", "valid_until")
    @classmethod
    def _validate_rebalance_time(cls, value: datetime) -> datetime:
        """Validate rebalance UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating rebalance request timestamp")
        return _validate_utc(value, "rebalance timestamp")

    @field_validator("canonical_hash")
    @classmethod
    def _validate_rebalance_hash_shape(cls, value: str) -> str:
        """Validate rebalance SHA-256 digest shape.

        Args:
            value: Candidate digest.

        Returns:
            Validated lowercase digest.

        Raises:
            ValueError: If digest is not lowercase SHA-256 hexadecimal.
        """
        logger.debug("Validating rebalance canonical hash shape")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("canonical_hash must be lowercase SHA-256 hex")
        return value

    @model_validator(mode="after")
    def _validate_rebalance_invariants(self) -> Self:
        """Validate lifetime and canonical hash binding.

        Returns:
            Validated rebalance request.

        Raises:
            ValueError: If lifetime or canonical hash evidence conflicts.
        """
        logger.debug("Validating PortfolioRebalanceExecutionRequest invariants")
        if self.valid_until <= self.valid_from:
            raise ValueError("rebalance validity must end after it begins")
        referenced_eligibility = {
            str(action["eligibility_decision_id"]) for action in self.actions
        }
        if referenced_eligibility != set(self.eligibility_decision_ids):
            raise ValueError("rebalance eligibility references do not match actions")
        material = {field: getattr(self, field) for field in self._HASHED_FIELDS}
        expected = sha256(canonical_json(material).encode("utf-8")).hexdigest()
        if self.canonical_hash != expected:
            raise ValueError("canonical_hash does not match rebalance material")
        return self


__all__ = [
    "TRADING_CONTRACT_VERSION",
    "ExecutionReceipt",
    "JsonValue",
    "OrderIntent",
    "PortfolioRebalanceExecutionRequest",
    "StandardTradingEnvelope",
    "TradeRecord",
    "TradingRequest",
    "TradingRoute",
]
