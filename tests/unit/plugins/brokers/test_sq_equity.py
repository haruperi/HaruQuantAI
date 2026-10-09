"""Unit tests for StrategyQuant US Equity broker and symbol catalog plugin."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

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
    _decode_sq_dat_bars,
    _decode_sq_dat_bytes,
    _find_sq_dat_file,
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


def _create_mock_sq_dat(
    file_path: Path,
    timeframe: str = "D",
    bars: list[dict[str, Any]] | None = None,
) -> None:
    """Helper creating a real StrategyQuant 4.2 binary archive on disk for testing."""
    import struct

    file_path.parent.mkdir(parents=True, exist_ok=True)
    if bars is None:
        bars = []

    out = bytearray()

    def write_utf(s: str) -> None:
        enc = s.encode("utf-8")
        out.extend(struct.pack(">H", len(enc)))
        out.extend(enc)

    write_utf("4.2")
    write_utf(timeframe)
    write_utf("ABCDEFGH")
    out.extend(struct.pack(">QI", len(bars), 8))
    out.extend(b"\x00" * (8 * 7))  # 8 col modifiers
    write_utf("SnRbTs")

    if not bars:
        file_path.write_bytes(out)
        return

    # Block sync sequence:
    out.extend(bytes(range(15)))
    out.extend(bytes([0, 0, 0, 0, 0xBB, 0xBB, 0xBB]))

    # Keyframe:
    first = bars[0]
    ts_ms = int(first["DateTime"].timestamp() * 1000)
    o_raw = int(first["Open"] * 1_000_000)
    h_raw = int(first["High"] * 1_000_000)
    l_raw = int(first["Low"] * 1_000_000)
    c_raw = int(first["Close"] * 1_000_000)
    v_raw = int(first["Volume"] * 100_000)

    out.extend(struct.pack(">Q5q", ts_ms, o_raw, h_raw, l_raw, c_raw, v_raw))

    # Delta records:
    prev_ts, prev_o, prev_h, prev_l, prev_c, prev_v = (
        ts_ms,
        o_raw,
        h_raw,
        l_raw,
        c_raw,
        v_raw,
    )
    for b in bars[1:]:
        curr_ts = int(b["DateTime"].timestamp() * 1000)
        curr_o = int(b["Open"] * 1_000_000)
        curr_h = int(b["High"] * 1_000_000)
        curr_l = int(b["Low"] * 1_000_000)
        curr_c = int(b["Close"] * 1_000_000)
        curr_v = int(b["Volume"] * 100_000)

        raw_deltas = [
            curr_ts - prev_ts,
            curr_o - prev_o,
            curr_h - prev_h,
            curr_l - prev_l,
            curr_c - prev_c,
            curr_v - prev_v,
        ]

        nybbles = []
        delta_bytes = bytearray()
        for d in raw_deltas:
            sign_bit = 4 if d >= 0 else 0
            abs_d = abs(d)
            if abs_d >= 2**32:
                nybbles.append(sign_bit | 3)  # length = 8 bytes (1 << 3)
                delta_bytes.extend(struct.pack(">Q", abs_d))
            else:
                nybbles.append(sign_bit | 2)  # length = 4 bytes (1 << 2)
                delta_bytes.extend(struct.pack(">I", abs_d))

        flag_bytes = bytes(
            [
                (nybbles[0] << 4) | nybbles[1],
                (nybbles[2] << 4) | nybbles[3],
                (nybbles[4] << 4) | nybbles[5],
            ]
        )
        out.extend(flag_bytes)
        out.extend(delta_bytes)

        prev_ts, prev_o, prev_h, prev_l, prev_c, prev_v = (
            curr_ts,
            curr_o,
            curr_h,
            curr_l,
            curr_c,
            curr_v,
        )

    file_path.write_bytes(out)


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


def test_decode_sq_dat_bars_isolated(tmp_path: Path) -> None:
    """Verify decoding a mock SQ 4.2 dat file with keyframe and delta compression."""
    dat_path = tmp_path / "test.dat"
    rows = [
        {
            "DateTime": datetime(2023, 1, 3, 9, 30, tzinfo=UTC),
            "Open": 150.0,
            "High": 155.0,
            "Low": 149.0,
            "Close": 154.0,
            "Volume": 1000,
        },
        {
            "DateTime": datetime(2023, 1, 4, 9, 30, tzinfo=UTC),
            "Open": 154.0,
            "High": 158.0,
            "Low": 153.0,
            "Close": 157.0,
            "Volume": 1200,
        },
        {
            "DateTime": datetime(2023, 1, 5, 9, 30, tzinfo=UTC),
            "Open": 156.0,
            "High": 159.0,
            "Low": 155.0,
            "Close": 156.5,
            "Volume": 800,
        },
    ]
    _create_mock_sq_dat(dat_path, bars=rows)

    # All bars
    bars = _decode_sq_dat_bars(dat_path)
    assert len(bars) == 3
    assert bars[0].open == 150.0
    assert bars[0].close == 154.0
    assert bars[1].close == 157.0
    assert bars[2].close == 156.5

    # Tail count
    tail = _decode_sq_dat_bars(dat_path, count=2)
    assert len(tail) == 2
    assert tail[0].close == 157.0
    assert tail[1].close == 156.5

    # Start position offset
    offset = _decode_sq_dat_bars(dat_path, start_pos=1)
    assert len(offset) == 2
    assert offset[0].close == 157.0

    # Date range filter
    dt_from = datetime(2023, 1, 4, tzinfo=UTC)
    dt_to = datetime(2023, 1, 4, 23, 59, tzinfo=UTC)
    filtered = _decode_sq_dat_bars(dat_path, date_from=dt_from, date_to=dt_to)
    assert len(filtered) == 1
    assert filtered[0].close == 157.0


def test_decode_sq_dat_corrupt_or_empty(tmp_path: Path) -> None:
    """Verify error and edge handling for malformed or empty SQ dat archives."""
    # Too short file
    short_file = tmp_path / "short.dat"
    short_file.write_bytes(b"too short")
    with pytest.raises(ValueError, match="Corrupt or incomplete SQ dat archive"):
        _decode_sq_dat_bars(short_file)

    # Empty file with header but no blocks
    empty_file = tmp_path / "empty.dat"
    _create_mock_sq_dat(empty_file, bars=[])
    assert _decode_sq_dat_bars(empty_file) == []


def test_find_sq_dat_file_resolution(tmp_path: Path) -> None:
    """Verify locating .dat files in SQX directory structures."""
    history_dir = tmp_path / "History"
    aapl_file = history_dir / "A" / "AAPL.D" / "AAPL.D_D1.dat"
    _create_mock_sq_dat(aapl_file)

    found = _find_sq_dat_file(history_dir, "AAPL", TimeFrame.D1)
    assert found == aapl_file

    found_suffix = _find_sq_dat_file(history_dir, "AAPL_limited.D", TimeFrame.D1)
    assert found_suffix == aapl_file

    assert _find_sq_dat_file(history_dir, "UNKNOWN", TimeFrame.D1) is None
    assert _find_sq_dat_file(tmp_path / "nonexistent", "AAPL") is None


def test_sq_equity_get_bars_from_sq_dat(tmp_path: Path) -> None:
    """Verify SQEquityBroker resolves and decodes bars from sqx_history_dir."""
    sqx_dir = tmp_path / "History"
    dat_path = sqx_dir / "S" / "SPY_benchmark.D" / "SPY_benchmark.D_D1.dat"
    rows = [
        {
            "DateTime": datetime(2023, 5, 1, tzinfo=UTC),
            "Open": 415.0,
            "High": 418.0,
            "Low": 414.0,
            "Close": 417.0,
            "Volume": 50000,
        },
        {
            "DateTime": datetime(2023, 5, 2, tzinfo=UTC),
            "Open": 417.0,
            "High": 419.0,
            "Low": 416.0,
            "Close": 418.5,
            "Volume": 60000,
        },
    ]
    _create_mock_sq_dat(dat_path, bars=rows)

    broker = SQEquityBroker(data_dir=tmp_path / "empty_market", sqx_history_dir=sqx_dir)
    resp = broker.get_bars("SPY", timeframe=TimeFrame.D1)
    assert resp.is_success
    assert resp.data is not None
    assert len(resp.data) == 2
    assert resp.data[0].open == 415.0
    assert resp.metadata.extensions.get("source") == "sq_dat"


def test_sq_equity_get_bars_sq_dat_read_error(tmp_path: Path) -> None:
    """Verify failure response when SQ dat decoding encounters corruption."""
    sqx_dir = tmp_path / "History"
    corrupt_dat = sqx_dir / "A" / "AAPL.D" / "AAPL.D_D1.dat"
    corrupt_dat.parent.mkdir(parents=True, exist_ok=True)
    corrupt_dat.write_bytes(b"\x00\x034.2\x00\x01D\x00\x08ABCDEFGH" + b"\xff" * 50)

    broker = SQEquityBroker(data_dir=tmp_path / "market", sqx_history_dir=sqx_dir)
    resp = broker.get_bars("AAPL")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "READ_ERROR"


def test_decode_sq_dat_bytes_direct(tmp_path: Path) -> None:
    """Verify _decode_sq_dat_bytes parses raw byte payloads in memory."""
    dat_file = tmp_path / "test.dat"
    rows = [
        {
            "DateTime": datetime(2023, 6, 1, tzinfo=UTC),
            "Open": 100.0,
            "High": 105.0,
            "Low": 99.0,
            "Close": 104.0,
            "Volume": 10000,
        }
    ]
    _create_mock_sq_dat(dat_file, bars=rows)
    raw_bytes = dat_file.read_bytes()

    bars = _decode_sq_dat_bytes(raw_bytes, source_name="memory_test")
    assert len(bars) == 1
    assert bars[0].open == 100.0
    assert bars[0].close == 104.0


def test_sq_equity_get_bars_cdn_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify remote CDN acquisition when local bars are not present."""
    dat_file = tmp_path / "2023.dat"
    rows = [
        {
            "DateTime": datetime(2023, 7, 10, tzinfo=UTC),
            "Open": 420.0,
            "High": 425.0,
            "Low": 418.0,
            "Close": 424.0,
            "Volume": 250000,
        },
        {
            "DateTime": datetime(2023, 7, 11, tzinfo=UTC),
            "Open": 424.0,
            "High": 430.0,
            "Low": 422.0,
            "Close": 429.0,
            "Volume": 300000,
        },
    ]
    _create_mock_sq_dat(dat_file, bars=rows)
    dat_bytes = dat_file.read_bytes()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        z.writestr("2023.dat", dat_bytes)
    zip_bytes = zip_buffer.getvalue()

    broker = SQEquityBroker(data_dir=tmp_path / "empty_dir", sqx_history_dir=None)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = zip_bytes
    monkeypatch.setattr(broker.session, "get", MagicMock(return_value=mock_resp))

    resp = broker.get_bars("NVDA", timeframe=TimeFrame.D1)
    assert resp.is_success
    assert resp.data is not None
    assert len(resp.data) == 2
    assert resp.data[0].open == 420.0
    assert resp.data[1].close == 429.0
    assert resp.metadata.extensions.get("source") == "cdn"


def test_sq_equity_get_bars_cdn_404_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify clean NOT_FOUND failure when CDN returns 404."""
    broker = SQEquityBroker(data_dir=tmp_path / "empty_dir", sqx_history_dir=None)

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""
    monkeypatch.setattr(broker.session, "get", MagicMock(return_value=mock_resp))

    resp = broker.get_bars("NONEXISTENT", timeframe=TimeFrame.D1)
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_equity_get_bars_cdn_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify resilient handling when CDN request raises network exception."""
    import requests

    broker = SQEquityBroker(data_dir=tmp_path / "empty_dir", sqx_history_dir=None)
    monkeypatch.setattr(
        broker.session,
        "get",
        MagicMock(side_effect=requests.RequestException("Network timeout")),
    )

    resp = broker.get_bars("NVDA", timeframe=TimeFrame.D1)
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_equity_env_reference_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify SQX_REFERENCE_ROOT environment variable sets sqx_history_dir."""
    fake_sqx = tmp_path / "fake_sqx"
    hist_dir = fake_sqx / "user" / "data" / "History" / "sq_equity"
    hist_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("SQX_REFERENCE_ROOT", str(fake_sqx))
    broker = SQEquityBroker()
    assert broker.sqx_history_dir == hist_dir


def test_sq_equity_cdn_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify enable_cdn_download=False suppresses remote CDN querying."""
    broker = SQEquityBroker(
        data_dir=tmp_path / "empty_dir",
        sqx_history_dir=None,
        enable_cdn_download=False,
    )
    mock_get = MagicMock()
    monkeypatch.setattr(broker.session, "get", mock_get)

    resp = broker.get_bars("NVDA", timeframe=TimeFrame.D1)
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"
    mock_get.assert_not_called()
