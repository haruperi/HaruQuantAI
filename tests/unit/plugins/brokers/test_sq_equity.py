"""Unit tests for StrategyQuant US Equity broker and symbol catalog plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from app.plugins.brokers.contracts import (
    BrokerCapability,
    TimeFrame,
    TradeRequest,
)
from app.plugins.brokers.sq_equity import (
    PLUGIN_MANIFEST,
    SQEquityBroker,
    _clean_symbol,
    create_adapter,
)


def _create_mock_parquet(file_path: Path, rows: list[dict[str, Any]]) -> None:
    """Helper creating a real Parquet file on disk for isolated testing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pydict: dict[str, list[Any]] = {}
    if rows:
        for k in rows[0].keys():
            pydict[k] = [r[k] for r in rows]
    table = pa.Table.from_pydict(pydict)
    pq.write_table(table, file_path)


def test_sq_equity_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability flags."""
    broker = create_adapter()
    assert isinstance(broker, SQEquityBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)
    assert not broker.has_capability(BrokerCapability.ORDERS)

    assert PLUGIN_MANIFEST["id"] == "broker-sq-equity"
    assert PLUGIN_MANIFEST["name"] == "StrategyQuant US Equities Connector"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "SQEquity"


def test_clean_symbol_normalization() -> None:
    """Verify ticker cleanup utility handles multiple SQX suffix patterns."""
    assert _clean_symbol("AAPL") == "AAPL"
    assert _clean_symbol("aapl.d") == "AAPL"
    assert _clean_symbol("AAPL_limited.D") == "AAPL"
    assert _clean_symbol("SPY_benchmark.D") == "SPY"
    assert _clean_symbol("MSFT.D") == "MSFT"


def test_sq_equity_symbol_info_resolution() -> None:
    """Verify resolving canonical SymbolInfo for equities and benchmark ETFs."""
    broker = create_adapter()

    # 1. Standard stock
    resp = broker.get_symbol_info("AAPL")
    assert resp.is_success
    assert resp.data is not None
    assert resp.data.name == "AAPL"
    assert resp.data.digits == 2
    assert resp.data.currency_base == "USD"
    assert resp.data.category == "Stocks"

    # 2. Suffix variations
    resp_suffix = broker.get_symbol_info("AAPL_limited.D")
    assert resp_suffix.is_success
    assert resp_suffix.data is not None
    assert resp_suffix.data.name == "AAPL"

    # 3. Benchmark ETF
    resp_etf = broker.get_symbol_info("SPY")
    assert resp_etf.is_success
    assert resp_etf.data is not None
    assert resp_etf.data.name == "SPY"
    assert resp_etf.data.category == "ETFs"

    # 4. Unknown ticker
    unknown = broker.get_symbol_info("NONEXISTENT_TICKER_XYZ")
    assert not unknown.is_success
    assert unknown.error is not None
    assert unknown.error.code == "SYMBOL_NOT_FOUND"


def test_sq_equity_get_symbols_and_filtering() -> None:
    """Verify retrieving catalog symbols, counts, and category filtering."""
    broker = create_adapter()

    # Total count
    count_resp = broker.get_num_of_symbols()
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data >= 105

    # All symbols
    all_syms = broker.get_symbols()
    assert all_syms.is_success
    assert all_syms.data is not None
    assert len(all_syms.data) == count_resp.data

    # Filter by ETFs
    etfs = broker.get_symbols(group="ETFs")
    assert etfs.is_success
    assert etfs.data is not None
    etf_names = {s.name for s in etfs.data}
    assert "SPY" in etf_names
    assert "QQQ" in etf_names

    # Filter by Exchange
    nasdaq = broker.get_symbols(group="NASDAQ")
    assert nasdaq.is_success
    assert nasdaq.data is not None
    nasdaq_names = {s.name for s in nasdaq.data}
    assert "AAPL" in nasdaq_names
    assert "MSFT" in nasdaq_names

    # Filter non-matching
    none_match = broker.get_symbols(group="NonexistentGroup12345")
    assert none_match.is_success
    assert none_match.data == []


def test_sq_equity_missing_catalog_hard_fail(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when catalog CSV is missing."""
    empty_csv = tmp_path / "nonexistent.csv"
    broker = SQEquityBroker(catalog_path=empty_csv)

    with pytest.raises(
        FileNotFoundError, match="StrategyQuant US Equity catalog not found"
    ):
        broker.get_symbol_info("AAPL")

    with pytest.raises(
        FileNotFoundError, match="StrategyQuant US Equity catalog not found"
    ):
        broker.get_symbols()

    with pytest.raises(
        FileNotFoundError, match="StrategyQuant US Equity catalog not found"
    ):
        broker.get_num_of_symbols()


def test_sq_equity_empty_catalog_csv_handling(tmp_path: Path) -> None:
    """Verify ValueError is raised when catalog CSV is empty or has no valid rows."""
    bad_csv = tmp_path / "bad_catalog.csv"
    bad_csv.write_text("invalid;corrupt\nrow1\nrow2\n", encoding="utf-8")

    broker = SQEquityBroker(catalog_path=bad_csv)
    with pytest.raises(ValueError, match="is empty or contains no valid instruments"):
        broker.get_symbol_info("SPY")


def test_sq_equity_get_bars_from_parquet(tmp_path: Path) -> None:
    """Verify loading, parsing, and filtering historical candlestick bars."""
    data_dir = tmp_path / "sq_equity"
    rows = [
        {
            "DateTime": datetime(2023, 1, 3, 9, 30, tzinfo=UTC),
            "Open": 130.0,
            "High": 131.0,
            "Low": 129.5,
            "Close": 130.5,
            "Volume": 1000,
        },
        {
            "DateTime": datetime(2023, 1, 4, 9, 30, tzinfo=UTC),
            "Open": 131.0,
            "High": 133.0,
            "Low": 130.0,
            "Close": 132.0,
            "Volume": 1500,
        },
        {
            "DateTime": datetime(2023, 1, 5, 9, 30, tzinfo=UTC),
            "Open": 132.0,
            "High": 134.0,
            "Low": 131.5,
            "Close": 133.5,
            "Volume": 1200,
        },
        {
            "DateTime": datetime(2023, 1, 6, 9, 30, tzinfo=UTC),
            "Open": 133.5,
            "High": 135.0,
            "Low": 133.0,
            "Close": 134.5,
            "Volume": 2000,
        },
    ]
    parquet_path = data_dir / "d1" / "aapl" / "2023.parquet"
    _create_mock_parquet(parquet_path, rows)

    broker = SQEquityBroker(data_dir=data_dir)

    # 1. Fetch all bars
    bars_resp = broker.get_bars("AAPL", timeframe=TimeFrame.D1)
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 4
    assert bars_resp.data[0].open == 130.0
    assert bars_resp.data[-1].close == 134.5

    # 2. Count limit (tail slicing)
    tail_resp = broker.get_bars("AAPL", count=2)
    assert tail_resp.is_success
    assert tail_resp.data is not None
    assert len(tail_resp.data) == 2
    assert tail_resp.data[0].close == 133.5
    assert tail_resp.data[1].close == 134.5

    # 3. Start pos offset
    offset_resp = broker.get_bars("AAPL", start_pos=2)
    assert offset_resp.is_success
    assert offset_resp.data is not None
    assert len(offset_resp.data) == 2
    assert offset_resp.data[0].close == 133.5

    # 4. Date filtering
    dt_from = datetime(2023, 1, 4, tzinfo=UTC)
    dt_to = datetime(2023, 1, 5, 23, 59, tzinfo=UTC)
    filtered = broker.get_bars("AAPL", date_from=dt_from, date_to=dt_to)
    assert filtered.is_success
    assert filtered.data is not None
    assert len(filtered.data) == 2


def test_sq_equity_get_bars_m1_fallback_to_d1(tmp_path: Path) -> None:
    """Verify fallback to D1 partition when M1 partition is missing."""
    data_dir = tmp_path / "sq_equity"
    rows = [
        {
            "DateTime": datetime(2023, 1, 3, tzinfo=UTC),
            "Open": 100.0,
            "High": 105.0,
            "Low": 99.0,
            "Close": 104.0,
            "Volume": 500,
        }
    ]
    parquet_path = data_dir / "d1" / "msft" / "2023.parquet"
    _create_mock_parquet(parquet_path, rows)

    broker = SQEquityBroker(data_dir=data_dir)

    # Request M1 when only D1 exists
    resp = broker.get_bars("MSFT", timeframe=TimeFrame.M1)
    assert resp.is_success
    assert resp.data is not None
    assert len(resp.data) == 1
    assert resp.data[0].close == 104.0


def test_sq_equity_get_bars_missing_symbol(tmp_path: Path) -> None:
    """Verify failure response when target symbol directory does not exist."""
    data_dir = tmp_path / "sq_equity"
    broker = SQEquityBroker(data_dir=data_dir)

    resp = broker.get_bars("UNKNOWN_TICKER")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_equity_get_bars_empty_partition_directory(tmp_path: Path) -> None:
    """Verify failure response when target directory exists but has no parquet files."""
    empty_dir = tmp_path / "sq_equity" / "d1" / "empty_sym"
    empty_dir.mkdir(parents=True, exist_ok=True)

    broker = SQEquityBroker(data_dir=tmp_path / "sq_equity")
    resp = broker.get_bars("EMPTY_SYM")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NO_DATA"


def test_sq_equity_get_bars_read_error(tmp_path: Path) -> None:
    """Verify failure response when parquet file reading raises an exception."""
    corrupt_file = tmp_path / "sq_equity" / "d1" / "corrupt" / "bad.parquet"
    corrupt_file.parent.mkdir(parents=True, exist_ok=True)
    corrupt_file.write_bytes(b"not a valid parquet file contents")

    broker = SQEquityBroker(data_dir=tmp_path / "sq_equity")
    resp = broker.get_bars("CORRUPT")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "READ_ERROR"


def test_sq_equity_ticks_unsupported() -> None:
    """Verify tick data retrieval returns unsupported capability failure."""
    broker = create_adapter()
    resp = broker.get_ticks("AAPL")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "UNSUPPORTED_CAPABILITY"
    assert "Tick data is not supported" in resp.message


def test_sq_equity_trading_rejections() -> None:
    """Verify all trading and execution operations reject as unsupported."""
    broker = create_adapter()

    req = TradeRequest(symbol="AAPL", volume=1.0)
    trade_resp = broker.trade(req)
    assert not trade_resp.is_success
    assert trade_resp.error is not None
    assert trade_resp.error.code == "CAPABILITY_NOT_SUPPORTED"
    assert "doesn't have trading capabilities" in trade_resp.message

    chk_resp = broker.check_order(req)
    assert not chk_resp.is_success
    assert "doesn't have trading capabilities" in chk_resp.message


def test_sq_equity_connection_rejections() -> None:
    """Verify connection operations reject as unsupported for offline provider."""
    broker = create_adapter()

    conn_resp = broker.connect()
    assert not conn_resp.is_success
    assert conn_resp.error is not None
    assert conn_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    alive_resp = broker.is_connected()
    assert not alive_resp.is_success
    assert alive_resp.error is not None
    assert alive_resp.error.code == "CAPABILITY_NOT_SUPPORTED"
