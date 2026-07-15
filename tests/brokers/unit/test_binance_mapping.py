"""Binance mapping tests."""

from app.services.brokers import BrokerErrorCode
from app.services.brokers.binance.mapping import _map_error_code, _map_kline


def test_binance_mapping_preserves_product_units() -> None:
    """Documented klines map exact values and timestamps."""
    bar = _map_kline(
        [0, "1", "2", "0.5", "1.5", "10", 60_000, "", 0, "", ""],
        "BTCUSDT",
        "1m",
    )
    assert str(bar.open) == "1"
    assert str(bar.trade_volume) == "10"


def test_binance_map_symbol() -> None:
    """_map_symbol maps standard Binance symbol payload to BrokerSymbolInfo."""
    from app.services.brokers.binance.mapping import _map_symbol

    info = _map_symbol(
        {
            "symbol": "BTCUSDT",
            "quoteAsset": "USDT",
            "baseAsset": "BTC",
            "quoteAssetPrecision": 8,
            "baseAssetPrecision": 8,
            "isSpotTradingAllowed": True,
        }
    )
    assert info.provider_symbol == "BTCUSDT"
    assert info.price_unit == "USDT"
    assert info.price_precision == 8


def test_binance_native_error_floor() -> None:
    """Initial specialized Binance codes are exhaustive."""
    assert _map_error_code(-1003) == BrokerErrorCode.BROKER_RATE_LIMITED
    assert _map_error_code(-1121) == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND
    assert _map_error_code(1) == BrokerErrorCode.BROKER_PROVIDER_ERROR


def test_binance_map_quote() -> None:
    """_map_quote produces a valid BrokerQuote."""
    from app.services.brokers.binance.mapping import _map_quote

    quote = _map_quote(
        {"bidPrice": "1.0", "askPrice": "1.1", "bidQty": "10.0", "askQty": "20.0"},
        "BTCUSDT",
    )
    assert quote.symbol == "BTCUSDT"
    assert str(quote.bid) == "1.0"
    assert str(quote.ask) == "1.1"
    assert str(quote.bid_quantity) == "10.0"
    assert str(quote.ask_quantity) == "20.0"


def test_binance_map_trade() -> None:
    """_map_trade produces a valid BrokerTick."""
    from app.services.brokers.binance.mapping import _map_trade

    tick = _map_trade(
        {"T": 1700000000000, "p": "1.2", "q": "5.0", "a": 12345},
        "BTCUSDT",
    )
    assert tick.symbol == "BTCUSDT"
    assert str(tick.last_price) == "1.2"
    assert str(tick.bid_quantity) == "5.0"
    assert tick.provider_sequence_id == 12345


def test_binance_map_kline_malformed() -> None:
    """_map_kline raises ValueError for malformed payload."""
    import pytest

    with pytest.raises(ValueError, match="malformed Binance kline"):
        _map_kline([0, "1"], "BTCUSDT", "1m")


def test_binance_error_mapping_extra() -> None:
    """Ensure less common native error codes are correctly mapped."""
    assert _map_error_code(-2010) == BrokerErrorCode.BROKER_REQUEST_REJECTED
    assert _map_error_code(-2015) == BrokerErrorCode.BROKER_AUTHENTICATION_FAILED
