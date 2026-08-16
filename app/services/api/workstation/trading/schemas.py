"""Trading gateway request schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.services.api.contracts.models import _BaseApiContract


class TradingMutationRequest(_BaseApiContract):
    """Exact API projection of one governed Trading request."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.trading_request.v1"] = "trading.trading_request.v1"
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    route: Literal["demo", "live"]
    action: str
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
    route: Literal["paper", "live"]
    account_id: str
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
    route: Literal["paper", "live"]
    account_id: str
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
    route: Literal["paper", "live"]
    account_id: str
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
    "TradingMutationRequest",
)
