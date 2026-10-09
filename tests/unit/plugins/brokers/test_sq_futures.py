"""Unit tests for StrategyQuant Continuous Futures broker and symbol catalog plugin."""

from __future__ import annotations

import io
import struct
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
from app.plugins.brokers.sq_futures import (
    CDN_BASE_URL,
    PLUGIN_MANIFEST,
    SQFuturesBroker,
    _clean_symbol,
    _decode_sq_dat_bars,
    _decode_sq_dat_bytes,
    _find_sq_dat_file,
    _normalize_dt,
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


def test_sq_futures_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability flags."""
    broker = create_adapter()
    assert isinstance(broker, SQFuturesBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)
    assert not broker.has_capability(BrokerCapability.ORDERS)

    assert PLUGIN_MANIFEST["id"] == "broker-sq-futures"
    assert PLUGIN_MANIFEST["name"] == "StrategyQuant Continuous Futures Connector"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "SQFutures"
    assert CDN_BASE_URL.startswith("https://cdn.strategyquantcdn.com")


def test_clean_symbol_normalization() -> None:
    """Verify continuous futures symbol cleanup utility handles .D, _limited, and case."""
    assert _clean_symbol("@ES") == "@ES"
    assert _clean_symbol("@es.d") == "@ES"
    assert _clean_symbol("@CL.D") == "@CL"
    assert _clean_symbol("cl") == "CL"
    assert _clean_symbol("@ES_LIMITED.D") == "@ES"
    assert _clean_symbol("@ES_BENCHMARK.D") == "@ES"


def test_normalize_dt_utility() -> None:
    """Verify datetime timezone normalization to UTC."""
    assert _normalize_dt(None) is None
    naive = datetime(2024, 1, 1, 12, 0)  # noqa: DTZ001
    norm = _normalize_dt(naive)
    assert norm is not None
    assert norm.tzinfo == UTC
    aware = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    assert _normalize_dt(aware) == aware


def test_sq_futures_symbol_info_resolution() -> None:
    """Verify resolving canonical SymbolInfo for continuous futures instruments."""
    broker = create_adapter()

    # 1. Standard ticker with @
    resp_es = broker.get_symbol_info("@ES")
    assert resp_es.is_success
    assert resp_es.data is not None
    assert resp_es.data.name == "@ES"
    assert resp_es.data.digits == 2
    assert resp_es.data.point == 0.25
    assert resp_es.data.trade_tick_value == 50.0
    assert resp_es.data.currency_base == "USD"
    assert resp_es.data.category == "Indices"

    # 2. Lookup without @ prefix
    resp_es_no_at = broker.get_symbol_info("ES")
    assert resp_es_no_at.is_success
    assert resp_es_no_at.data is not None
    assert resp_es_no_at.data.name == "@ES"

    # 3. Energy contract
    resp_cl = broker.get_symbol_info("@CL")
    assert resp_cl.is_success
    assert resp_cl.data is not None
    assert resp_cl.data.name == "@CL"
    assert resp_cl.data.category == "Energies"
    assert resp_cl.data.trade_tick_value == 1000.0

    # 4. Suffix variation (.D)
    resp_cl_d = broker.get_symbol_info("@CL.D")
    assert resp_cl_d.is_success
    assert resp_cl_d.data is not None
    assert resp_cl_d.data.name == "@CL"

    # 5. Unknown ticker
    unknown = broker.get_symbol_info("NONEXISTENT_FUTURES_XYZ")
    assert not unknown.is_success
    assert unknown.error is not None
    assert unknown.error.code == "SYMBOL_NOT_FOUND"


def test_sq_futures_get_symbols_and_filtering() -> None:
    """Verify retrieving catalog symbols, counts, and category/exchange filtering."""
    broker = create_adapter()

    # Total count
    count_resp = broker.get_num_of_symbols()
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data >= 70

    # All symbols
    all_syms = broker.get_symbols()
    assert all_syms.is_success
    assert all_syms.data is not None
    assert len(all_syms.data) == count_resp.data

    # Filter by Energies
    energies = broker.get_symbols(group="Energies")
    assert energies.is_success
    assert energies.data is not None
    energy_names = {s.name for s in energies.data}
    assert "@CL" in energy_names
    assert "@NG" in energy_names

    # Filter by Exchange
    cme = broker.get_symbols(group="CME")
    assert cme.is_success
    assert cme.data is not None
    cme_names = {s.name for s in cme.data}
    assert "@ES" in cme_names
    assert "@NQ" in cme_names

    # Filter non-matching
    none_match = broker.get_symbols(group="NonexistentGroup12345")
    assert none_match.is_success
    assert none_match.data == []


def test_sq_futures_missing_catalog_hard_fail(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when catalog CSV is missing."""
    empty_csv = tmp_path / "nonexistent.csv"
    broker = SQFuturesBroker(catalog_path=empty_csv)

    with pytest.raises(
        FileNotFoundError,
        match="StrategyQuant Continuous Futures catalog not found",
    ):
        broker.get_symbol_info("@ES")

    with pytest.raises(
        FileNotFoundError,
        match="StrategyQuant Continuous Futures catalog not found",
    ):
        broker.get_symbols()

    with pytest.raises(
        FileNotFoundError,
        match="StrategyQuant Continuous Futures catalog not found",
    ):
        broker.get_num_of_symbols()


def test_sq_futures_empty_catalog_csv_handling(tmp_path: Path) -> None:
    """Verify ValueError is raised when catalog CSV is empty or has no valid rows."""
    bad_csv = tmp_path / "bad_catalog.csv"
    bad_csv.write_text("invalid;corrupt\nrow1\nrow2\n", encoding="utf-8")

    broker = SQFuturesBroker(catalog_path=bad_csv)
    with pytest.raises(ValueError, match="is empty or contains no valid instruments"):
        broker.get_symbol_info("@ES")


def test_sq_futures_get_bars_from_parquet(tmp_path: Path) -> None:
    """Verify loading, parsing, and filtering historical candlestick bars from Parquet."""
    data_dir = tmp_path / "sq_futures"
    rows = [
        {
            "DateTime": datetime(2024, 1, 3, 9, 30, tzinfo=UTC),
            "Open": 4750.0,
            "High": 4760.0,
            "Low": 4745.0,
            "Close": 4755.0,
            "Volume": 10000,
        },
        {
            "DateTime": datetime(2024, 1, 4, 9, 30, tzinfo=UTC),
            "Open": 4755.0,
            "High": 4775.0,
            "Low": 4750.0,
            "Close": 4770.0,
            "Volume": 12000,
        },
        {
            "DateTime": datetime(2024, 1, 5, 9, 30, tzinfo=UTC),
            "Open": 4770.0,
            "High": 4785.0,
            "Low": 4765.0,
            "Close": 4780.0,
            "Volume": 15000,
        },
        {
            "DateTime": datetime(2024, 1, 8, 9, 30, tzinfo=UTC),
            "Open": 4780.0,
            "High": 4795.0,
            "Low": 4775.0,
            "Close": 4790.0,
            "Volume": 11000,
        },
    ]
    parquet_path = data_dir / "d1" / "@es" / "2024.parquet"
    _create_mock_parquet(parquet_path, rows)

    broker = SQFuturesBroker(data_dir=data_dir)

    # 1. Fetch all bars
    bars_resp = broker.get_bars("@ES", timeframe=TimeFrame.D1)
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 4
    assert bars_resp.data[0].open == 4750.0
    assert bars_resp.data[-1].close == 4790.0

    # 2. Count limit (tail slicing)
    tail_resp = broker.get_bars("@ES", count=2)
    assert tail_resp.is_success
    assert tail_resp.data is not None
    assert len(tail_resp.data) == 2
    assert tail_resp.data[0].close == 4780.0
    assert tail_resp.data[1].close == 4790.0

    # 3. Start pos offset
    offset_resp = broker.get_bars("@ES", start_pos=2)
    assert offset_resp.is_success
    assert offset_resp.data is not None
    assert len(offset_resp.data) == 2
    assert offset_resp.data[0].close == 4780.0

    # 4. Date filtering
    dt_from = datetime(2024, 1, 4, tzinfo=UTC)
    dt_to = datetime(2024, 1, 5, 23, 59, tzinfo=UTC)
    filtered = broker.get_bars("@ES", date_from=dt_from, date_to=dt_to)
    assert filtered.is_success
    assert filtered.data is not None
    assert len(filtered.data) == 2


def test_sq_futures_get_bars_from_sq_dat(tmp_path: Path) -> None:
    """Verify loading, parsing, and filtering historical candlestick bars from SQ .dat."""
    data_dir = tmp_path / "sq_futures"
    rows = [
        {
            "DateTime": datetime(2024, 1, 3, 9, 30, tzinfo=UTC),
            "Open": 4750.0,
            "High": 4760.0,
            "Low": 4745.0,
            "Close": 4755.0,
            "Volume": 10000,
        },
        {
            "DateTime": datetime(2024, 1, 4, 9, 30, tzinfo=UTC),
            "Open": 4755.0,
            "High": 4775.0,
            "Low": 4750.0,
            "Close": 4770.0,
            "Volume": 12000,
        },
        {
            "DateTime": datetime(2024, 1, 5, 9, 30, tzinfo=UTC),
            "Open": 4770.0,
            "High": 4785.0,
            "Low": 4765.0,
            "Close": 4780.0,
            "Volume": 15000,
        },
        {
            "DateTime": datetime(2024, 1, 8, 9, 30, tzinfo=UTC),
            "Open": 4780.0,
            "High": 4795.0,
            "Low": 4775.0,
            "Close": 4790.0,
            "Volume": 11000,
        },
    ]
    # Place .dat file under SQX History folder convention
    dat_path = data_dir / "history" / "@" / "@es" / "@es_d1.dat"
    _create_mock_sq_dat(dat_path, timeframe="D", bars=rows)

    broker = SQFuturesBroker(data_dir=data_dir)

    # 1. Fetch all bars from dat
    direct_bars = _decode_sq_dat_bars(dat_path)
    assert len(direct_bars) == 4

    bars_resp = broker.get_bars("@ES", timeframe=TimeFrame.D1)
    assert bars_resp.is_success
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 4
    assert bars_resp.data[0].open == 4750.0
    assert bars_resp.data[-1].close == 4790.0

    # 2. Count limit (tail slicing)
    tail_resp = broker.get_bars("@ES", count=2)
    assert tail_resp.is_success
    assert tail_resp.data is not None
    assert len(tail_resp.data) == 2
    assert tail_resp.data[0].close == 4780.0
    assert tail_resp.data[1].close == 4790.0

    # 3. Start pos offset
    offset_resp = broker.get_bars("@ES", start_pos=2)
    assert offset_resp.is_success
    assert offset_resp.data is not None
    assert len(offset_resp.data) == 2
    assert offset_resp.data[0].close == 4780.0

    # 4. Date filtering
    dt_from = datetime(2024, 1, 4, tzinfo=UTC)
    dt_to = datetime(2024, 1, 5, 23, 59, tzinfo=UTC)
    filtered = broker.get_bars("@ES", date_from=dt_from, date_to=dt_to)
    assert filtered.is_success
    assert filtered.data is not None
    assert len(filtered.data) == 2


def test_sq_futures_find_sq_dat_file_conventions(tmp_path: Path) -> None:
    """Verify _find_sq_dat_file locates archives in various directory layouts."""
    data_dir = tmp_path / "sq_futures"

    # Layout 1: dat/d1/@es/@es_D1.dat
    l1 = data_dir / "dat" / "d1" / "@es" / "@es_D1.dat"
    _create_mock_sq_dat(l1, bars=[])
    assert _find_sq_dat_file(data_dir, "@ES", TimeFrame.D1) == l1
    l1.unlink()

    # Layout 2: direct file in data_dir
    l2 = data_dir / "@es_D1.dat"
    _create_mock_sq_dat(l2, bars=[])
    assert _find_sq_dat_file(data_dir, "@ES", TimeFrame.D1) == l2
    l2.unlink()

    # Layout 3: direct without @ prefix
    l3 = data_dir / "es_D1.dat"
    _create_mock_sq_dat(l3, bars=[])
    assert _find_sq_dat_file(data_dir, "ES", TimeFrame.D1) == l3
    l3.unlink()

    # Layout 4: history/@/@ew/@ew_d1.dat
    l4 = data_dir / "history" / "@" / "@ew" / "@ew_d1.dat"
    _create_mock_sq_dat(l4, bars=[])
    assert _find_sq_dat_file(data_dir, "@EW", TimeFrame.D1) == l4

    # None match
    assert _find_sq_dat_file(data_dir, "NONEXISTENT", TimeFrame.D1) is None


def test_sq_futures_decode_sq_dat_bytes_corrupt_or_truncated() -> None:
    """Verify error handling on corrupted, truncated, or incomplete SQ .dat buffers."""
    # 1. Short buffer (< 48 bytes)
    with pytest.raises(ValueError, match="Corrupt or incomplete SQ dat archive"):
        _decode_sq_dat_bytes(b"short bytes", source_name="test_short")

    # 2. Incomplete UTF string length (off + 2 > len(buf))
    b_utf_len = struct.pack(">H", 40) + b"A" * 40 + struct.pack(">H", 3) + b"BBB" + b"X"
    with pytest.raises(ValueError, match="reading UTF length"):
        _decode_sq_dat_bytes(b_utf_len, source_name="test_utf_len")

    # 3. Incomplete UTF string content (off + length > len(buf))
    b_utf_str = struct.pack(">H", 100) + b"A" * 46
    with pytest.raises(ValueError, match="reading UTF string"):
        _decode_sq_dat_bytes(b_utf_str, source_name="test_utf_str")

    # 4. Incomplete header size after UTF strings (buffer >= 48 bytes but offset + 12 > len(buf))
    out_hdr = bytearray()

    def write_utf_hdr(s: str) -> None:
        enc = s.encode("utf-8")
        out_hdr.extend(struct.pack(">H", len(enc)) + enc)

    write_utf_hdr("4.2")
    write_utf_hdr("D")
    write_utf_hdr("A" * 30)
    out_hdr.extend(b"P" * 8)  # len is 48, offset is 40, offset + 12 = 52 > 48
    with pytest.raises(ValueError, match="Invalid header size"):
        _decode_sq_dat_bytes(bytes(out_hdr), source_name="test_hdr")

    # 5. Empty blocks returns []
    out = bytearray()

    def write_utf(s: str) -> None:
        enc = s.encode("utf-8")
        out.extend(struct.pack(">H", len(enc)) + enc)

    write_utf("4.2")
    write_utf("D")
    write_utf("ABCDEFGH")
    out.extend(struct.pack(">QI", 0, 8))
    out.extend(b"\x00" * (8 * 7))
    write_utf("SnRbTs")
    # No sync token present
    assert _decode_sq_dat_bytes(bytes(out)) == []

    # 6. Truncated keyframe in block
    out.extend(bytes(range(15)))
    out.extend(b"\x00" * 5)  # Less than 7 prefix + 48 keyframe
    assert _decode_sq_dat_bytes(bytes(out)) == []


def test_sq_futures_get_bars_m1_fallback_to_d1(tmp_path: Path) -> None:
    """Verify fallback to D1 partition when M1 partition is missing."""
    data_dir = tmp_path / "sq_futures"
    rows = [
        {
            "DateTime": datetime(2024, 1, 3, tzinfo=UTC),
            "Open": 5000.0,
            "High": 5020.0,
            "Low": 4990.0,
            "Close": 5010.0,
            "Volume": 5000,
        }
    ]
    parquet_path = data_dir / "d1" / "@nq" / "2024.parquet"
    _create_mock_parquet(parquet_path, rows)

    broker = SQFuturesBroker(data_dir=data_dir)

    # Request M1 when only D1 exists
    resp = broker.get_bars("@NQ", timeframe=TimeFrame.M1)
    assert resp.is_success
    assert resp.data is not None
    assert len(resp.data) == 1
    assert resp.data[0].close == 5010.0


def test_sq_futures_get_bars_with_and_without_at_symbol(tmp_path: Path) -> None:
    """Verify partition directory lookup works when stored without @ prefix."""
    data_dir = tmp_path / "sq_futures"
    rows = [
        {
            "DateTime": datetime(2024, 1, 3, tzinfo=UTC),
            "Open": 70.0,
            "High": 72.0,
            "Low": 69.5,
            "Close": 71.5,
            "Volume": 8000,
        }
    ]
    # Directory stored as 'cl' rather than '@cl'
    parquet_path = data_dir / "d1" / "cl" / "2024.parquet"
    _create_mock_parquet(parquet_path, rows)

    broker = SQFuturesBroker(data_dir=data_dir)

    # Request with @CL
    resp_with = broker.get_bars("@CL")
    assert resp_with.is_success
    assert resp_with.data is not None
    assert len(resp_with.data) == 1
    assert resp_with.data[0].close == 71.5

    # Request without @ (CL)
    resp_without = broker.get_bars("CL")
    assert resp_without.is_success
    assert resp_without.data is not None
    assert len(resp_without.data) == 1
    assert resp_without.data[0].close == 71.5


def test_sq_futures_get_bars_missing_symbol(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify failure response when target symbol directory does not exist."""
    data_dir = tmp_path / "sq_futures"
    broker = SQFuturesBroker(data_dir=data_dir)
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""
    monkeypatch.setattr(broker.session, "get", MagicMock(return_value=mock_resp))

    resp = broker.get_bars("UNKNOWN_TICKER")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_futures_get_bars_empty_partition_directory(tmp_path: Path) -> None:
    """Verify failure response when target directory exists but has no parquet files."""
    empty_dir = tmp_path / "sq_futures" / "d1" / "@empty_sym"
    empty_dir.mkdir(parents=True, exist_ok=True)

    broker = SQFuturesBroker(data_dir=tmp_path / "sq_futures")
    resp = broker.get_bars("@EMPTY_SYM")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NO_DATA"


def test_sq_futures_get_bars_read_error(tmp_path: Path) -> None:
    """Verify failure response when parquet file reading raises an exception."""
    corrupt_file = tmp_path / "sq_futures" / "d1" / "@corrupt" / "bad.parquet"
    corrupt_file.parent.mkdir(parents=True, exist_ok=True)
    corrupt_file.write_bytes(b"not a valid parquet file contents")

    broker = SQFuturesBroker(data_dir=tmp_path / "sq_futures")
    resp = broker.get_bars("@CORRUPT")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "READ_ERROR"


def test_sq_futures_get_bars_dat_read_error(tmp_path: Path) -> None:
    """Verify failure response when SQ dat archive file reading raises an exception."""
    corrupt_dat = tmp_path / "sq_futures" / "dat" / "d1" / "@bad" / "@bad_d1.dat"
    corrupt_dat.parent.mkdir(parents=True, exist_ok=True)
    corrupt_dat.write_bytes(b"corrupt dat file contents")

    broker = SQFuturesBroker(data_dir=tmp_path / "sq_futures")
    resp = broker.get_bars("@BAD")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "READ_ERROR"


def test_sq_futures_cdn_fetch_mock_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify remote CDN fetch unzips and parses SQ .dat files into bars."""
    data_dir = tmp_path / "sq_futures"

    # Create mock zip containing a valid .dat file
    rows = [
        {
            "DateTime": datetime(2024, 1, 3, tzinfo=UTC),
            "Open": 4800.0,
            "High": 4820.0,
            "Low": 4790.0,
            "Close": 4810.0,
            "Volume": 9000,
        }
    ]
    temp_dat = tmp_path / "temp.dat"
    _create_mock_sq_dat(temp_dat, bars=rows)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("2024.dat", temp_dat.read_bytes())
    zip_bytes = zip_buf.getvalue()

    broker = SQFuturesBroker(data_dir=data_dir)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = zip_bytes
    monkeypatch.setattr(broker.session, "get", MagicMock(return_value=mock_resp))

    resp = broker.get_bars("@REMOTE_FUT", count=5)
    assert resp.is_success
    assert resp.data is not None
    assert len(resp.data) == 1
    assert resp.data[0].close == 4810.0


def test_sq_futures_cdn_fetch_pre2019_data00(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify date_from prior to 2019 requests data00.zip as well as data01.zip."""
    data_dir = tmp_path / "sq_futures"

    rows = [
        {
            "DateTime": datetime(2015, 6, 1, tzinfo=UTC),
            "Open": 2100.0,
            "High": 2110.0,
            "Low": 2095.0,
            "Close": 2105.0,
            "Volume": 5000,
        }
    ]
    temp_dat = tmp_path / "temp.dat"
    _create_mock_sq_dat(temp_dat, bars=rows)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("2015.dat", temp_dat.read_bytes())
    zip_bytes = zip_buf.getvalue()

    broker = SQFuturesBroker(data_dir=data_dir)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = zip_bytes
    mock_get = MagicMock(return_value=mock_resp)
    monkeypatch.setattr(broker.session, "get", mock_get)

    dt_from = datetime(2015, 1, 1, tzinfo=UTC)
    resp = broker.get_bars("@PRE2019", date_from=dt_from)
    assert resp.is_success
    assert resp.data is not None
    calls = [call.args[0] for call in mock_get.call_args_list]
    assert any("data00.zip" in url for url in calls)


def test_sq_futures_cdn_fetch_mock_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify CDN download HTTP failure falls back to NOT_FOUND."""
    data_dir = tmp_path / "sq_futures"
    broker = SQFuturesBroker(data_dir=data_dir)
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""
    monkeypatch.setattr(broker.session, "get", MagicMock(return_value=mock_resp))

    resp = broker.get_bars("@NONEXISTENT_FUT")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_futures_ticks_unsupported() -> None:
    """Verify tick data retrieval returns unsupported capability failure."""
    broker = create_adapter()
    resp = broker.get_ticks("@ES")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "UNSUPPORTED_CAPABILITY"
    assert "Tick data is not supported" in resp.message


def test_sq_futures_trading_rejections() -> None:
    """Verify all trading and execution operations reject as unsupported."""
    broker = create_adapter()

    req = TradeRequest(symbol="@ES", volume=1.0)
    trade_resp = broker.trade(req)
    assert not trade_resp.is_success
    assert trade_resp.error is not None
    assert trade_resp.error.code == "CAPABILITY_NOT_SUPPORTED"
    assert "doesn't have trading capabilities" in trade_resp.message

    chk_resp = broker.check_order(req)
    assert not chk_resp.is_success
    assert "doesn't have trading capabilities" in chk_resp.message


def test_sq_futures_connection_rejections() -> None:
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
