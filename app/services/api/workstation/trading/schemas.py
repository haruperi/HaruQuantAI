"""Trading gateway request schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.services.api.contracts.models import _BaseApiContract


class ExecutionSessionCreateRequest(_BaseApiContract):
    """Create one durable execution-session definition."""

    name: str
    mode: Literal["sim", "demo", "live"]
    provider: str
    description: str = ""
    provider_account_ref: str | None = None
    credential_ref: str | None = None
    simulation_session_id: str | None = None
    dataset_ref: str | None = None
    dataset_revision: str | None = None
    dataset_hash: str | None = None
    sim_initial_balance: Decimal | None = None
    sim_leverage: int | None = Field(default=None, ge=1, le=1000)
    sim_account_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    auto_start: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


class ExecutionSessionUpdateRequest(_BaseApiContract):
    """Update mutable execution-session metadata with optimistic locking."""

    expected_version: int
    name: str
    description: str = ""
    auto_start: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


class ExecutionSessionActionRequest(_BaseApiContract):
    """Apply one revision-checked session lifecycle action."""

    expected_version: int


class ExecutionSessionConfigurationRequest(_BaseApiContract):
    """Complete one stopped legacy SIM session."""

    expected_version: int
    dataset_ref: str
    dataset_revision: str
    dataset_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class TradingAccountProfileResponse(_BaseApiContract):
    """Provider-authored identity and account metrics shown by the shell."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.trading.account_profile.v1"] = (
        "api.trading.account_profile.v1"
    )
    account_name: str
    session_name: str | None = None
    trade_mode: Literal["SIMULATION", "DEMO", "REAL", "CONTEST"]
    selected_mode: Literal["sim", "demo", "live"]
    mode_compatible: bool
    environment_label: str
    source: Literal["simulator", "mt5"]
    currency: str | None = None
    balance: Decimal | None = None
    equity: Decimal | None = None
    profit: Decimal | None = None
    margin: Decimal | None = None
    free_margin: Decimal | None = None
    margin_level: Decimal | None = None
    leverage: Decimal | None = None
    retrieved_at: datetime


class TradingInstrumentConstraintsResponse(_BaseApiContract):
    """Provider-authored order-entry constraints for one exact symbol."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.trading.instrument_constraints.v1"] = (
        "api.trading.instrument_constraints.v1"
    )
    symbol: str
    source_id: str
    quantity_unit: str
    min_quantity: Decimal
    max_quantity: Decimal
    quantity_step: Decimal
    price_tick: Decimal
    digits: int | None = None
    pip_size: Decimal | None = None
    trade_tick_size: Decimal | None = None
    trade_tick_value_profit: Decimal | None = None
    trade_tick_value_loss: Decimal | None = None
    trade_contract_size: Decimal | None = None
    profit_currency: str | None = None
    supported_order_types: tuple[Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"], ...]
    supported_time_in_force: tuple[Literal["GTC", "IOC", "FOK", "GTD", "DAY"], ...]
    supports_stop_loss: bool
    supports_take_profit: bool
    retrieved_at: datetime


class TradingMutationRequest(_BaseApiContract):
    """Exact API projection of one governed Trading request."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.trading_request.v1"] = "trading.trading_request.v1"
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    route: Literal["sim", "demo", "live"]
    action: str
    provider_id: str | None = None
    account_id: str
    simulation_session_id: str | None = None
    portfolio_id: str | None = None
    strategy_id: str
    strategy_version: str
    intent_id: str
    symbol: str | None = None
    side: Literal["BUY", "SELL"] | None = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity_unit: str
    quantity: Decimal | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
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
    instrument_min_quantity: Decimal | None = None
    instrument_max_quantity: Decimal | None = None
    instrument_quantity_step: Decimal | None = None
    instrument_price_tick: Decimal | None = None
    redaction_applied: Literal[True] = True


class OrderPreflightRequest(_BaseApiContract):
    """One candidate human-initiated order submitted for Risk review only.

    Carries no governance IDs — a preflight call produces them; it never
    consumes them.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.order_preflight_request.v1"] = (
        "trading.order_preflight_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    route: Literal["sim", "demo", "live"]
    account_id: str
    simulation_session_id: str | None = None
    portfolio_id: str | None = None
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity: Decimal
    current_price: Decimal
    stop_distance: Decimal | None = None
    idempotency_key: str


class OrderPreflightResponse(_BaseApiContract):
    """The real Risk decision and (when approved) policy verdict produced."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.order_preflight_response.v1"] = (
        "trading.order_preflight_response.v1"
    )
    state: str
    risk_decision_id: str
    action_policy_verdict_id: str | None
    approval_token_ref: str | None
    reasons: tuple[str, ...]
    expires_at: datetime


class CancelOrderPreflightRequest(_BaseApiContract):
    """One candidate single-order cancellation submitted for Risk review only.

    Carries no governance IDs — a preflight call produces them; it never
    consumes them.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.cancel_order_preflight_request.v1"] = (
        "trading.cancel_order_preflight_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    route: Literal["sim", "demo", "live"]
    account_id: str
    simulation_session_id: str | None = None
    portfolio_id: str | None = None
    representative_symbol: str
    target_broker_order_id: str
    idempotency_key: str


class CancelAllPreflightRequest(_BaseApiContract):
    """One candidate bulk cancel-all-orders action submitted for Risk review.

    Carries no governance IDs — a preflight call produces them; it never
    consumes them.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.cancel_all_preflight_request.v1"] = (
        "trading.cancel_all_preflight_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    route: Literal["sim", "demo", "live"]
    account_id: str
    simulation_session_id: str | None = None
    portfolio_id: str | None = None
    representative_symbol: str
    idempotency_key: str


class CancelAllPreflightResponse(_BaseApiContract):
    """The real Risk decision and (when approved) bulk policy verdict produced."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.cancel_all_preflight_response.v1"] = (
        "trading.cancel_all_preflight_response.v1"
    )
    state: str
    risk_decision_id: str
    action_policy_verdict_id: str | None
    approval_token_ref: str | None
    reasons: tuple[str, ...]
    expires_at: datetime


__all__ = (
    "CancelAllPreflightRequest",
    "CancelAllPreflightResponse",
    "CancelOrderPreflightRequest",
    "OrderPreflightRequest",
    "OrderPreflightResponse",
    "TradingAccountProfileResponse",
    "TradingInstrumentConstraintsResponse",
    "TradingMutationRequest",
)
