"""cTrader protobuf fixture to canonical value mapping."""

# ruff: noqa: ANN401, FURB171 - protobuf fixtures expose heterogeneous fields.

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.brokers.contracts import BrokerErrorCode, BrokerQuote


def _field(value: object, name: str) -> Any:
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _map_quote(value: object, symbol: str, digits: int) -> BrokerQuote:
    """Map exact relative prices using provider symbol digits."""
    divisor = Decimal(10) ** digits
    timestamp = datetime.fromtimestamp(float(_field(value, "timestamp")) / 1000, UTC)
    bid_raw = _field(value, "bid")
    ask_raw = _field(value, "ask")
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_currency",
        quantity_unit="provider_volume",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(bid_raw) / divisor if bid_raw is not None else None,
        ask=Decimal(ask_raw) / divisor if ask_raw is not None else None,
        provider_timestamp=timestamp,
    )


def _map_error_code(code: str, operation: str) -> BrokerErrorCode:
    """Map the normative cTrader native-error floor."""
    if code in {"MARKET_CLOSED"}:
        return BrokerErrorCode.BROKER_MARKET_CLOSED
    if code == "NOT_ENOUGH_MONEY":
        return BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    if code in {
        "INVALID_REQUEST",
        "INVALID_VOLUME",
        "INVALID_STOPS",
        "BAD_VOLUME",
        "INVALID_EXPIRATION",
    }:
        return BrokerErrorCode.BROKER_REQUEST_INVALID
    if code == "ORDER_NOT_FOUND" and "order" in operation:
        return BrokerErrorCode.BROKER_ORDER_NOT_FOUND
    if code == "POSITION_NOT_FOUND" and "position" in operation:
        return BrokerErrorCode.BROKER_POSITION_NOT_FOUND
    return BrokerErrorCode.BROKER_PROVIDER_ERROR
