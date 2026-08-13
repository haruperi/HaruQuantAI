"""Deterministic unit tests for the asset-class classifier.

The classifier is a pure function with no I/O, so every branch is exercised
with literal inputs. MT5 grouping paths use a Windows-style backslash
separator, which is the primary real-world input; forward-slash and missing
paths cover the fallback symbol-name heuristics.
"""

from __future__ import annotations

from app.services.data.market_data.asset_classifier import (
    COMMODITIES,
    CRYPTOCURRENCIES,
    DISPLAY_ASSET_CLASSES,
    ETFS,
    FOREX,
    INDICES,
    OTHER,
    STOCKS,
    classify_symbol,
)


class TestPathClassification:
    """Grouping-path keyword matching."""

    def test_forex_symbol_info_path(self) -> None:
        assert classify_symbol("Forex\\EURJPY", "EURJPY") == FOREX
        assert classify_symbol("Forex\\EURUSD", "EURUSD") == FOREX

    def test_forex_path_backslash(self) -> None:
        assert classify_symbol("Forex\\Majors\\EURUSD", "EURUSD") == FOREX

    def test_forex_path_forward_slash(self) -> None:
        assert classify_symbol("FX/Miners/AUDCAD", "AUDCAD") == FOREX

    def test_currencies_path(self) -> None:
        assert classify_symbol("Currencies\\USDJPY", "USDJPY") == FOREX

    def test_commodities_path(self) -> None:
        assert classify_symbol("Commodities\\Energies\\CL", "CL") == COMMODITIES

    def test_metals_path(self) -> None:
        assert classify_symbol("Metals\\XAGUSD", "XAGUSD") == COMMODITIES

    def test_energy_path(self) -> None:
        assert classify_symbol("Energy\\Brent", "BRN") == COMMODITIES

    def test_indices_path(self) -> None:
        assert classify_symbol("Indices\\US500", "US500") == INDICES

    def test_cash_indexes_path(self) -> None:
        assert classify_symbol("Cash Indexes\\GER40", "GER40") == INDICES

    def test_stocks_path(self) -> None:
        assert classify_symbol("Stocks\\USA\\AAPL", "AAPL") == STOCKS

    def test_shares_path(self) -> None:
        assert classify_symbol("Shares\\EU\\BMW", "BMW") == STOCKS

    def test_etf_path(self) -> None:
        assert classify_symbol("ETF\\SPY", "SPY") == ETFS

    def test_crypto_path(self) -> None:
        assert classify_symbol("Crypto\\BTCUSD", "BTCUSD") == CRYPTOCURRENCIES


class TestSymbolOverrides:
    """Symbol-level precedence over path classification."""

    def test_gold_grouped_under_forex_is_commodity(self) -> None:
        # MT5 commonly groups XAUUSD under Forex; it must surface as Commodities.
        assert classify_symbol("Forex\\Metals\\XAUUSD", "XAUUSD") == COMMODITIES

    def test_silver_variant_symbols(self) -> None:
        assert classify_symbol("Forex", "XAGUSDm") == COMMODITIES
        assert classify_symbol(None, "XAGUSD.r") == COMMODITIES

    def test_crypto_pair_overrides_fx_heuristic(self) -> None:
        # BTCJPY looks like a 6-char yen pair but must be Crypto.
        assert classify_symbol(None, "BTCJPY") == CRYPTOCURRENCIES

    def test_six_char_fx_pair_fallback(self) -> None:
        assert classify_symbol(None, "EURUSD") == FOREX
        assert classify_symbol(None, "GBPCHF") == FOREX

    def test_six_char_non_fx_not_misclassified(self) -> None:
        assert classify_symbol(None, "ABC123") == OTHER


class TestEdgeCases:
    """Missing inputs and unknown content."""

    def test_empty_path_falls_back_to_symbol(self) -> None:
        assert classify_symbol("", "EURUSD") == FOREX

    def test_whitespace_path_segments_ignored(self) -> None:
        assert classify_symbol("  /  / Forex \\ EURUSD", "EURUSD") == FOREX

    def test_unknown_symbol_and_path_returns_other(self) -> None:
        assert classify_symbol("Custom\\Bonds\\DE10Y", "DE10Y") == OTHER

    def test_none_inputs_return_other(self) -> None:
        assert classify_symbol(None, None) == OTHER

    def test_display_classes_order_and_contents(self) -> None:
        assert DISPLAY_ASSET_CLASSES == (
            FOREX,
            COMMODITIES,
            INDICES,
            STOCKS,
            ETFS,
            CRYPTOCURRENCIES,
        )
