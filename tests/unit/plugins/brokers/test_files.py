"""Unit tests for local filesystem market data and symbol catalog broker plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from app.plugins.brokers.contracts import (
    BrokerCapability,
    TimeFrame,
    TradeRequest,
)
from app.plugins.brokers.files import (
    PLUGIN_MANIFEST,
    FilesBroker,
    _detect_digits,
    _extract_symbol_from_path,
    _parse_timestamp,
    create_adapter,
)


def _write_mock_parquet(file_path: Path, rows: list[dict[str, Any]]) -> None:
    """Helper writing a mock Parquet dataset to disk."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pydict: dict[str, list[Any]] = {}
    if rows:
        for k in rows[0].keys():
            pydict[k] = [r[k] for r in rows]
    table = pa.Table.from_pydict(pydict)
    pq.write_table(table, file_path)


def test_files_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability flags."""
    broker = create_adapter()
    assert isinstance(broker, FilesBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)
    assert not broker.has_capability(BrokerCapability.ORDERS)

    assert PLUGIN_MANIFEST["id"] == "broker-files"
    assert PLUGIN_MANIFEST["name"] == "Local Files Connector"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "ticks" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "Files"


def test_parse_timestamp_and_detect_digits() -> None:
    """Verify parsing flexible date/time strings and detecting price digits."""
    # ISO strings
    dt1 = _parse_timestamp("2023-10-01T12:30:00Z")
    assert dt1.year == 2023 and dt1.month == 10 and dt1.day == 1
    assert dt1.tzinfo == UTC

    # Common date + time formats
    dt2 = _parse_timestamp("2023.10.01 09:30:00")
    assert dt2.hour == 9 and dt2.minute == 30

    dt3 = _parse_timestamp("2023/10/01 16:00:00")
    assert dt3.hour == 16

    # Date only
    dt4 = _parse_timestamp("2023-10-01")
    assert dt4.year == 2023 and dt4.day == 1

    # Fallback to current time for invalid string
    dt_now = _parse_timestamp("completely_invalid_timestamp_str")
    assert isinstance(dt_now, datetime)

    # Detect digits
    assert _detect_digits(150.25) == 2
    assert _detect_digits(1.12345) == 5
    assert _detect_digits(100.0) == 0
    assert _detect_digits(0.0) == 2
    assert _detect_digits(-5.0) == 2


def test_extract_symbol_from_path() -> None:
    """Verify extracting canonical uppercase symbol from file stems or directories."""
    # Numeric stem -> parent folder name
    assert (
        _extract_symbol_from_path(Path("data/sq_equity/d1/aapl/2023.parquet")) == "AAPL"
    )
    assert (
        _extract_symbol_from_path(Path("data/sq_futures/d1/@es/2024.parquet")) == "@ES"
    )

    # Ticker stem with timeframe suffix
    assert _extract_symbol_from_path(Path("data/EURUSD_M1.csv")) == "EURUSD"
    assert _extract_symbol_from_path(Path("data/msft-d1.txt")) == "MSFT"
    assert _extract_symbol_from_path(Path("data/BTCUSDT.parquet")) == "BTCUSDT"


def test_files_catalog_scanning_and_symbol_queries(tmp_path: Path) -> None:
    """Verify scanning directory for symbols, catalog count, and group filtering."""
    # Setup mock file hierarchy
    (tmp_path / "stocks" / "d1" / "aapl").mkdir(parents=True)
    (tmp_path / "stocks" / "d1" / "aapl" / "2023.parquet").write_bytes(b"dummy")

    (tmp_path / "stocks" / "d1" / "msft").mkdir(parents=True)
    (tmp_path / "stocks" / "d1" / "msft" / "2023.parquet").write_bytes(b"dummy")

    (tmp_path / "forex").mkdir(parents=True)
    (tmp_path / "forex" / "EURUSD_M1.csv").write_text("dummy", encoding="utf-8")

    # Should be ignored
    (tmp_path / "resources" / "cot_catalog.json").mkdir(parents=True, exist_ok=True)
    (tmp_path / "resources" / "cot_catalog.json" / "manifest.json").write_text(
        "{}", encoding="utf-8"
    )

    broker = FilesBroker(data_dir=tmp_path)

    # 1. Total symbols count
    count_resp = broker.get_num_of_symbols()
    assert count_resp.is_success
    assert count_resp.data == 3

    # 2. Get all symbols
    all_syms = broker.get_symbols()
    assert all_syms.is_success
    assert all_syms.data is not None
    assert len(all_syms.data) == 3
    sym_names = {s.name for s in all_syms.data}
    assert sym_names == {"AAPL", "MSFT", "EURUSD"}

    # 3. Filter by group/category "stocks"
    stocks_syms = broker.get_symbols(group="stocks")
    assert stocks_syms.is_success
    assert stocks_syms.data is not None
    assert len(stocks_syms.data) == 2
    assert {s.name for s in stocks_syms.data} == {"AAPL", "MSFT"}

    # 4. Filter by group/category "forex"
    forex_syms = broker.get_symbols(group="forex")
    assert forex_syms.is_success
    assert forex_syms.data is not None
    assert len(forex_syms.data) == 1
    assert forex_syms.data[0].name == "EURUSD"


def test_get_symbol_info(tmp_path: Path) -> None:
    """Verify get_symbol_info resolves SymbolInfo metadata or fails closed."""
    # Setup mock file
    file_path = tmp_path / "equity" / "d1" / "aapl" / "2023.parquet"
    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"dummy")

    broker = FilesBroker(data_dir=tmp_path)

    # Found
    resp = broker.get_symbol_info("AAPL")
    assert resp.is_success
    assert resp.data is not None
    assert resp.data.name == "AAPL"
    assert resp.data.category == "Stocks"
    assert resp.data.digits == 2
    assert resp.data.currency_base == "USD"

    # Not found
    resp_none = broker.get_symbol_info("NONEXISTENT_TICKER")
    assert not resp_none.is_success
    assert resp_none.error is not None
    assert resp_none.error.code == "SYMBOL_NOT_FOUND"


def test_get_bars_csv_single_timestamp(tmp_path: Path) -> None:
    """Verify parsing CSV files with a single datetime column and filtering."""
    csv_file = tmp_path / "AAPL.csv"
    csv_content = """datetime,open,high,low,close,volume
2023-10-01 09:30:00,170.0,172.5,169.5,171.0,1000
2023-10-01 09:31:00,171.0,173.0,170.5,172.5,1500
2023-10-01 09:32:00,172.5,174.0,172.0,173.0,2000
2023-10-01 09:33:00,173.0,173.5,171.5,172.0,1200
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    broker = FilesBroker(data_dir=tmp_path)

    # All bars
    bars_resp = broker.get_bars("AAPL")
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 4

    # Count limit
    bars_count = broker.get_bars("AAPL", count=2)
    assert bars_count.is_success
    assert bars_count.data is not None
    assert len(bars_count.data) == 2
    assert bars_count.data[0].close == 173.0
    assert bars_count.data[1].close == 172.0

    # Date range filter
    d_from = datetime(2023, 10, 1, 9, 31, 0, tzinfo=UTC)
    d_to = datetime(2023, 10, 1, 9, 32, 0, tzinfo=UTC)
    bars_range = broker.get_bars("AAPL", date_from=d_from, date_to=d_to)
    assert bars_range.is_success
    assert bars_range.data is not None
    assert len(bars_range.data) == 2
    assert bars_range.data[0].open == 171.0
    assert bars_range.data[1].close == 173.0


def test_get_bars_csv_separate_date_time_columns(tmp_path: Path) -> None:
    """Verify parsing StrategyQuant classic CSV format with separate Date and Time columns."""
    csv_file = tmp_path / "EURUSD.csv"
    csv_content = """<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>
2023.01.03,09:30:00,1.0550,1.0560,1.0545,1.0555,500
2023.01.03,09:31:00,1.0555,1.0570,1.0550,1.0565,600
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    broker = FilesBroker(data_dir=tmp_path)
    bars_resp = broker.get_bars("EURUSD")
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 2
    assert bars_resp.data[0].open == 1.0550
    assert bars_resp.data[0].tick_volume == 500
    assert bars_resp.data[1].close == 1.0565


def test_get_bars_parquet(tmp_path: Path) -> None:
    """Verify parsing Parquet tabular dataset into Bar records."""
    pq_file = tmp_path / "stocks" / "d1" / "msft" / "2023.parquet"
    rows = [
        {
            "DateTime": datetime(2023, 1, 3, 0, 0, tzinfo=UTC),
            "Open": 240.0,
            "High": 245.0,
            "Low": 239.0,
            "Close": 243.5,
            "Volume": 10000,
        },
        {
            "DateTime": datetime(2023, 1, 4, 0, 0, tzinfo=UTC),
            "Open": 243.5,
            "High": 248.0,
            "Low": 242.0,
            "Close": 247.0,
            "Volume": 12000,
        },
    ]
    _write_mock_parquet(pq_file, rows)

    broker = FilesBroker(data_dir=tmp_path)
    bars_resp = broker.get_bars("MSFT")
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 2
    assert bars_resp.data[0].open == 240.0
    assert bars_resp.data[1].close == 247.0
    assert bars_resp.data[1].real_volume == 12000


def test_get_bars_timeframe_prioritization(tmp_path: Path) -> None:
    """Verify that get_bars prioritizes the file matching the requested timeframe."""
    # D1 file
    d1_file = tmp_path / "stocks" / "d1" / "aapl" / "2023.parquet"
    d1_rows = [
        {
            "DateTime": datetime(2023, 1, 3, 0, 0, tzinfo=UTC),
            "Open": 100.0,
            "High": 105.0,
            "Low": 99.0,
            "Close": 104.0,
            "Volume": 5000,
        }
    ]
    _write_mock_parquet(d1_file, d1_rows)

    # M1 file
    m1_file = tmp_path / "stocks" / "m1" / "aapl" / "2023.parquet"
    m1_rows = [
        {
            "DateTime": datetime(2023, 1, 3, 9, 30, tzinfo=UTC),
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.5,
            "Close": 100.5,
            "Volume": 50,
        }
    ]
    _write_mock_parquet(m1_file, m1_rows)

    broker = FilesBroker(data_dir=tmp_path)

    # Query D1
    resp_d1 = broker.get_bars("AAPL", timeframe=TimeFrame.D1)
    assert resp_d1.is_success
    assert resp_d1.data is not None
    assert resp_d1.data[0].close == 104.0

    # Query M1
    resp_m1 = broker.get_bars("AAPL", timeframe=TimeFrame.M1)
    assert resp_m1.is_success
    assert resp_m1.data is not None
    assert resp_m1.data[0].close == 100.5


def test_get_bars_errors(tmp_path: Path) -> None:
    """Verify get_bars handles missing files and parse errors gracefully."""
    broker = FilesBroker(data_dir=tmp_path)

    # Missing file
    resp_missing = broker.get_bars("UNKNOWN")
    assert not resp_missing.is_success
    assert resp_missing.error is not None
    assert resp_missing.error.code == "FILE_NOT_FOUND"

    # Corrupt file
    corrupt_file = tmp_path / "CORRUPT.parquet"
    corrupt_file.write_bytes(b"not a valid parquet file")
    resp_corrupt = broker.get_bars("CORRUPT")
    assert not resp_corrupt.is_success
    assert resp_corrupt.error is not None
    assert resp_corrupt.error.code == "PARSE_ERROR"


def test_get_ticks(tmp_path: Path) -> None:
    """Verify get_ticks converts bars to Tick objects or fails if absent."""
    csv_file = tmp_path / "AAPL.csv"
    csv_content = """datetime,open,high,low,close,volume
2023-10-01 09:30:00,170.0,172.5,169.5,171.0,1000
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    broker = FilesBroker(data_dir=tmp_path)

    # Found
    ticks_resp = broker.get_ticks("AAPL", count=1)
    assert ticks_resp.is_success
    assert ticks_resp.data is not None
    assert len(ticks_resp.data) == 1
    t = ticks_resp.data[0]
    assert t.last == 171.0
    assert t.bid == 171.0
    assert t.ask == 171.0
    assert t.volume == 1000.0

    # Not found
    ticks_none = broker.get_ticks("UNKNOWN")
    assert not ticks_none.is_success
    assert ticks_none.error is not None
    assert ticks_none.error.code == "NO_DATA"


def test_unsupported_broker_capabilities() -> None:
    """Verify unsupported trading and connection methods fail closed."""
    broker = create_adapter()

    # Trading rejection
    trade_resp = broker.trade(TradeRequest(symbol="AAPL", volume=1.0))
    assert not trade_resp.is_success
    assert trade_resp.error is not None
    assert trade_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    # Order verification rejection
    order_resp = broker.check_order(TradeRequest(symbol="AAPL", volume=1.0))
    assert not order_resp.is_success
    assert order_resp.error is not None
    assert order_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    # Connection lifecycle
    assert not broker.is_connected()
    conn_resp = broker.connect()
    assert not conn_resp.is_success
    assert conn_resp.error is not None
    assert conn_resp.error.code == "CAPABILITY_NOT_SUPPORTED"

    disc_resp = broker.disconnect()
    assert not disc_resp.is_success
    assert disc_resp.error is not None
    assert disc_resp.error.code == "CAPABILITY_NOT_SUPPORTED"


def test_nonexistent_data_dir(tmp_path: Path) -> None:
    """Verify behavior when data_dir does not exist."""
    non_dir = tmp_path / "does_not_exist"
    broker = FilesBroker(data_dir=non_dir)
    assert broker.get_num_of_symbols().data == 0
    assert len(broker.get_symbols().data or []) == 0
    assert not broker.get_symbol_info("AAPL").is_success
    assert not broker.get_bars("AAPL").is_success


def test_get_bars_start_pos_and_filtering(tmp_path: Path) -> None:
    """Verify start_pos offset and boundary filtering in get_bars."""
    csv_file = tmp_path / "MSFT.csv"
    csv_content = """date,open,high,low,close,vol
2023.01.02,200.0,205.0,199.0,204.0,100
2023.01.03,204.0,206.0,203.0,205.0,200
2023.01.04,205.0,208.0,204.0,207.0,300
2023.01.05,207.0,209.0,206.0,208.0,400
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    broker = FilesBroker(data_dir=tmp_path)

    # start_pos=2 skips first 2 bars
    bars_offset = broker.get_bars("MSFT", start_pos=2)
    assert bars_offset.is_success
    assert bars_offset.data is not None
    assert len(bars_offset.data) == 2
    assert bars_offset.data[0].open == 205.0

    # Date filter skipping before and after
    d_from = datetime(2023, 1, 3, tzinfo=UTC)
    d_to = datetime(2023, 1, 4, tzinfo=UTC)
    bars_filtered = broker.get_bars("MSFT", date_from=d_from, date_to=d_to)
    assert bars_filtered.is_success
    assert bars_filtered.data is not None
    assert len(bars_filtered.data) == 2
    assert bars_filtered.data[0].open == 204.0
    assert bars_filtered.data[1].open == 205.0
