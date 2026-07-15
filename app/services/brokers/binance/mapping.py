"""Binance Spot provider payload to canonical DTO mapping."""

# ruff: noqa: PLR2004 - native wire constants are normative provider evidence.

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerErrorCode,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)


def _map_symbol(value: dict[str, Any]) -> BrokerSymbolInfo:
    """Map exact Spot exchange metadata without canonical aliases."""
    symbol = str(value["symbol"])
    return BrokerSymbolInfo(
        provider_symbol=symbol,
        product_profile="binance_spot",
        price_unit=str(value["quoteAsset"]),
        quantity_unit=str(value["baseAsset"]),
        base_asset=str(value["baseAsset"]),
        quote_asset=str(value["quoteAsset"]),
        price_precision=int(value["quoteAssetPrecision"]),
        quantity_precision=int(value["baseAssetPrecision"]),
        trading_flags={"spot_trading_allowed": value.get("isSpotTradingAllowed")},
    )


def _map_quote(value: dict[str, Any], symbol: str) -> BrokerQuote:
    """Map genuine book-ticker values and quantities."""
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_asset",
        quantity_unit="base_asset",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(str(value["bidPrice"])),
        ask=Decimal(str(value["askPrice"])),
        bid_quantity=Decimal(str(value["bidQty"])),
        ask_quantity=Decimal(str(value["askQty"])),
    )


def _map_trade(value: dict[str, Any], symbol: str) -> BrokerTick:
    """Map one genuine aggregate trade without inventing sequence evidence."""
    timestamp = datetime.fromtimestamp(int(value["T"]) / 1000, UTC)
    return BrokerTick(
        symbol=symbol,
        event_timestamp=timestamp,
        provider_receipt_timestamp=datetime.now(UTC),
        price_unit="quote_asset",
        quantity_unit="base_asset",
        tick_type="TRADE",
        provider_sequence_id=value.get("a"),
        last_price=Decimal(str(value["p"])),
        bid_quantity=Decimal(str(value["q"])),
    )


def _map_kline(value: list[Any], symbol: str, timeframe: str) -> BrokerBar:
    """Map one documented Spot kline array."""
    if len(value) < 11:
        raise ValueError("malformed Binance kline")
    return BrokerBar(
        symbol=symbol,
        opening_timestamp=datetime.fromtimestamp(int(value[0]) / 1000, UTC),
        closing_timestamp=datetime.fromtimestamp(int(value[6]) / 1000, UTC),
        is_closed=True,
        open=Decimal(str(value[1])),
        high=Decimal(str(value[2])),
        low=Decimal(str(value[3])),
        close=Decimal(str(value[4])),
        provider_timeframe=timeframe,
        requested_timeframe=timeframe,
        price_unit="quote_asset",
        quantity_unit="base_asset",
        trade_volume=Decimal(str(value[5])),
    )


def _map_error_code(code: int) -> BrokerErrorCode:
    """Map the normative Binance native-error floor."""
    if code == -1003:
        return BrokerErrorCode.BROKER_RATE_LIMITED
    if code == -1121:
        return BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND
    if code == -2010:
        return BrokerErrorCode.BROKER_REQUEST_REJECTED
    if code == -2015:
        return BrokerErrorCode.BROKER_AUTHENTICATION_FAILED
    return BrokerErrorCode.BROKER_PROVIDER_ERROR
