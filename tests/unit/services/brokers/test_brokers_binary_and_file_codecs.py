"""Unit tests for binary and file historical data codecs.

Description:
    Tests binary decoders and encoders for Dukascopy BI5 (ticks and bars),
    MetaTrader 4 HST (v400 and v401), MetaTrader 4 FXT (v405), StrategyQuant 4.2 .dat,
    and Darwinex tick archives. Verifies delimited CSV/TSV parsers (including separated
    Date/Time MT format), Parquet columnar readers, and exact partition discovery.
    Validates boundary conditions including truncated headers, corrupted magic markers,
    and structural validation errors.

Purpose:
    FEAT-BROKER-CODECS-TEST: Verification of binary and file codecs for market data.

Key Capabilities:
    - FR-TEST-CODECS-BINARY: Assert decode and encode fidelity across binary formats.
      Associated: `test_bi5_ticks_fixture_decoding()`, `test_hst_v400_fixture_decoding()`,
      `test_fxt_v405_fixture_decoding()`, `test_sq_dat_fixture_decoding()`
      Logging: Validates structured logs and output invariants.
    - FR-TEST-CODECS-FILES: Assert delimited text and Parquet parsing fidelity.
      Associated: `test_delimited_csv_standard_fixture()`, `test_parquet_fixture_reading()`,
      `test_partition_discovery_exact_symbol_matching()`
      Logging: Validates schema normalization and partition discovery.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_binary_and_file_codecs.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_binary_and_file_codecs.py --no-cov
    ```
"""

from __future__ import annotations

import struct
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.brokers._file_history import (
    export_bars_to_csv,
    export_bars_to_parquet,
    find_matching_partitions,
    parse_delimited_bars,
    parse_delimited_ticks,
    read_parquet_bars,
)
from app.services.brokers._native_history import (
    decode_bi5_bars,
    decode_bi5_ticks,
    decode_darwinex_dat,
    decode_fxt_bytes,
    decode_hst_bytes,
    decode_sq_dat_bytes,
    decompress_bi5,
    encode_fxt_bytes,
    encode_hst_bytes,
)
from app.services.brokers.capabilities import ProviderValidationError

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "brokers" / "stage2c"


# ============================================================================
# BI5 Codecs (Dukascopy LZMA)
# ============================================================================


def test_bi5_ticks_fixture_decoding() -> None:
    """Verify Dukascopy BI5 tick decoding from versioned fixture."""
    fixture_path = FIXTURES_DIR / "bi5" / "eurusd_ticks.bi5"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    decomp = decompress_bi5(data)
    assert len(decomp) > 0

    base_time = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
    ticks = decode_bi5_ticks(decomp, base_time, digits=5)

    assert len(ticks) > 0
    for tick in ticks:
        assert tick["bid"] > 1.0 and tick["bid"] < 2.0
        assert tick["ask"] >= tick["bid"]
        assert tick["volume"] > 0
        assert "time_msc" in tick


def test_bi5_bars_fixture_decoding() -> None:
    """Verify Dukascopy BI5 M1 bar decoding from versioned fixture."""
    fixture_path = FIXTURES_DIR / "bi5" / "eurusd_m1.bi5"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    decomp = decompress_bi5(data)
    assert len(decomp) > 0

    base_time = datetime(2026, 1, 15, 0, 0, 0, tzinfo=UTC)
    bars = decode_bi5_bars(decomp, base_time, digits=5)

    assert len(bars) > 0
    for bar in bars:
        assert bar["high"] >= bar["low"]
        assert bar["open"] >= bar["low"] and bar["open"] <= bar["high"]
        assert bar["close"] >= bar["low"] and bar["close"] <= bar["high"]
        assert bar["tick_volume"] >= 0
        assert "time" in bar


def test_bi5_empty_and_truncated_safety() -> None:
    """Verify BI5 decoder handles empty payload safely without unhandled exception."""
    assert decompress_bi5(b"") == b""
    assert decompress_bi5(b"short") == b""
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    assert decode_bi5_ticks(b"", base_time) == []
    assert decode_bi5_bars(b"", base_time) == []


# ============================================================================
# MetaTrader 4 HST Codecs (v400 and v401)
# ============================================================================


def test_hst_v400_fixture_decoding() -> None:
    """Verify MT4 HST version 400 fixture parsing."""
    fixture_path = FIXTURES_DIR / "hst" / "eurusd_m1_v400.hst"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    bars = decode_hst_bytes(data)
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["high"] == 1.0520
    assert bars[0]["low"] == 1.0490
    assert bars[0]["close"] == 1.0510
    assert bars[0]["tick_volume"] == 150


def test_hst_v401_fixture_decoding() -> None:
    """Verify MT4 HST version 401 fixture parsing."""
    fixture_path = FIXTURES_DIR / "hst" / "eurusd_m1_v401.hst"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    bars = decode_hst_bytes(data)
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["high"] == 1.0520
    assert bars[0]["low"] == 1.0490
    assert bars[0]["close"] == 1.0510
    assert bars[0]["tick_volume"] == 150


def test_hst_round_trip_encode_decode() -> None:
    """Verify HST encoding and decoding round-trip preserves fidelity."""
    original_bars = [
        {
            "time": 1768478400,
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0990,
            "close": 1.1020,
            "tick_volume": 200,
        },
        {
            "time": 1768478460,
            "open": 1.1020,
            "high": 1.1060,
            "low": 1.1010,
            "close": 1.1040,
            "tick_volume": 250,
        },
    ]
    encoded_v401 = encode_hst_bytes(original_bars, "GBPUSD", period=1, version=401)
    decoded = decode_hst_bytes(encoded_v401)

    assert len(decoded) == 2
    assert decoded[0]["open"] == 1.1000
    assert decoded[0]["high"] == 1.1050
    assert decoded[0]["low"] == 1.0990
    assert decoded[0]["close"] == 1.1020

    # Test v400 encoding
    encoded_v400 = encode_hst_bytes(original_bars, "GBPUSD", period=1, version=400)
    decoded_v400 = decode_hst_bytes(encoded_v400)
    assert len(decoded_v400) == 2
    assert decoded_v400[0]["open"] == 1.1000


def test_hst_truncated_header_rejects() -> None:
    """Verify HST rejects truncated header with ProviderValidationError."""
    with pytest.raises(ProviderValidationError, match="HST file too small"):
        decode_hst_bytes(b"\x91\x01\x00\x00" + b"\x00" * 20)


# ============================================================================
# MetaTrader 4 FXT Codecs (v405)
# ============================================================================


def test_fxt_v405_fixture_decoding() -> None:
    """Verify MT4 FXT version 405 fixture parsing."""
    fixture_path = FIXTURES_DIR / "fxt" / "eurusd_m1_v405.fxt"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    bars = decode_fxt_bytes(data)
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["high"] == 1.0520
    assert bars[0]["low"] == 1.0490
    assert bars[0]["close"] == 1.0510
    assert bars[0]["volume"] == 150


def test_fxt_round_trip_encode_decode() -> None:
    """Verify FXT encoding and decoding round-trip preserves fidelity."""
    original_bars = [
        {
            "time": 1768478400,
            "open": 1.2000,
            "high": 1.2050,
            "low": 1.1980,
            "close": 1.2010,
            "volume": 500,
            "tick_time": 1768478400,
            "flag": 1,
        }
    ]
    encoded = encode_fxt_bytes(original_bars, "USDJPY", period=1)
    decoded = decode_fxt_bytes(encoded)

    assert len(decoded) == 1
    assert decoded[0]["open"] == 1.2000
    assert decoded[0]["high"] == 1.2050


def test_fxt_truncated_header_rejects() -> None:
    """Verify FXT rejects truncated header with ProviderValidationError."""
    with pytest.raises(ProviderValidationError, match="FXT file too small"):
        decode_fxt_bytes(b"\x95\x01\x00\x00" + b"\x00" * 100)


# ============================================================================
# StrategyQuant 4.2 .dat Codec
# ============================================================================


def test_sq_dat_fixture_decoding() -> None:
    """Verify StrategyQuant 4.2 .dat fixture parsing."""
    fixture_path = FIXTURES_DIR / "sq_dat" / "aapl_d1.dat"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    data = fixture_path.read_bytes()

    bars = decode_sq_dat_bytes(data)
    assert len(bars) == 1
    assert bars[0]["open"] == 150.0
    assert bars[0]["high"] == 152.0
    assert bars[0]["low"] == 149.0
    assert bars[0]["close"] == 151.0
    assert bars[0]["tick_volume"] == 100


def test_sq_dat_corrupted_magic_returns_empty() -> None:
    """Verify SQ .dat returns empty list when magic marker is absent."""
    corrupt_data = b"INVALID_HEADER_PREFIX" + b"\x00" * 100
    bars = decode_sq_dat_bytes(corrupt_data)
    assert bars == []


# ============================================================================
# Darwinex .dat Codec
# ============================================================================


def test_darwinex_dat_decoding() -> None:
    """Verify Darwinex tick archive decoding."""
    epoch_ms1 = 1768478400000
    bid_micro1 = 108500
    ask_micro1 = 108510
    epoch_ms2 = 1768478401000
    bid_micro2 = 108505
    ask_micro2 = 108515

    raw = (
        b"\xbb\xbb"
        + struct.pack(">qqq", epoch_ms1, ask_micro1, bid_micro1)
        + struct.pack(">qqq", epoch_ms2, ask_micro2, bid_micro2)
    )
    ticks = decode_darwinex_dat(raw)

    assert len(ticks) == 2
    assert round(ticks[0]["bid"], 5) == 1.08500
    assert round(ticks[0]["ask"], 5) == 1.08510
    assert ticks[1]["bid"] == 1.08505


def test_darwinex_dat_missing_magic_returns_empty() -> None:
    """Verify Darwinex .dat returns empty list when magic marker is absent."""
    assert decode_darwinex_dat(b"\x00\x00\x00\x00") == []


# ============================================================================
# Delimited File Codecs (CSV / TSV / Semicolon)
# ============================================================================


def test_delimited_csv_standard_fixture() -> None:
    """Verify standard CSV fixture with ISO timestamp is parsed correctly."""
    fixture_path = FIXTURES_DIR / "csv" / "sample_bars_standard.csv"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    content = fixture_path.read_text(encoding="utf-8")

    bars = parse_delimited_bars(content, symbol="EURUSD", timeframe="M1")
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["high"] == 1.0520
    assert bars[0]["low"] == 1.0490
    assert bars[0]["close"] == 1.0510
    assert bars[0]["tick_volume"] == 150


def test_delimited_csv_metatrader_fixture() -> None:
    """Verify MetaTrader CSV fixture with separate Date and Time columns."""
    fixture_path = FIXTURES_DIR / "csv" / "sample_bars_metatrader.csv"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    content = fixture_path.read_text(encoding="utf-8")

    bars = parse_delimited_bars(content, symbol="EURUSD", timeframe="M1")
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["tick_volume"] == 150
    assert bars[0]["time"] > 0


def test_delimited_ticks_fixture() -> None:
    """Verify delimited ticks CSV fixture."""
    fixture_path = FIXTURES_DIR / "csv" / "sample_ticks.csv"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    content = fixture_path.read_text(encoding="utf-8")

    ticks = parse_delimited_ticks(content, symbol="EURUSD")
    assert len(ticks) == 2
    assert ticks[0]["bid"] == 1.0500
    assert ticks[0]["ask"] == 1.0502
    assert ticks[0]["time_msc"] > 0


def test_delimited_semicolon_and_tab_bars() -> None:
    """Verify semicolon and tab delimited bars parsing."""
    semicolon_data = (
        "Date;Time;Open;High;Low;Close;Volume\n"
        "2026.01.15;10:00:00;1.0850;1.0860;1.0845;1.0855;150\n"
    )
    bars = parse_delimited_bars(semicolon_data, symbol="EURUSD")
    assert len(bars) == 1
    assert bars[0]["open"] == 1.0850

    tab_data = (
        "Timestamp\tOpen\tHigh\tLow\tClose\tVolume\n"
        "2026-01-15 10:00:00\t1.0850\t1.0860\t1.0845\t1.0855\t150\n"
    )
    bars_tab = parse_delimited_bars(tab_data, symbol="EURUSD")
    assert len(bars_tab) == 1
    assert bars_tab[0]["open"] == 1.0850


def test_export_bars_to_csv_round_trip(tmp_path: Path) -> None:
    """Verify CSV export and subsequent re-parsing round-trip."""
    original_bars = [
        {
            "timestamp": "2026-01-15T12:00:00+00:00",
            "open": 100.5,
            "high": 102.0,
            "low": 99.8,
            "close": 101.2,
            "tick_volume": 5000,
        }
    ]
    target_csv = tmp_path / "bars.csv"
    export_bars_to_csv(original_bars, target_csv)
    assert target_csv.exists()

    reparsed = parse_delimited_bars(
        target_csv.read_text(encoding="utf-8"), symbol="TEST"
    )
    assert len(reparsed) == 1
    assert reparsed[0]["open"] == 100.5
    assert reparsed[0]["tick_volume"] == 5000


# ============================================================================
# Parquet Codecs
# ============================================================================


def test_parquet_fixture_reading() -> None:
    """Verify reading Parquet partition fixture."""
    fixture_path = FIXTURES_DIR / "parquet" / "sample_bars.parquet"
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"

    bars = read_parquet_bars(fixture_path)
    assert len(bars) == 2
    assert bars[0]["open"] == 1.0500
    assert bars[0]["tick_volume"] == 150


def test_parquet_export_and_read_round_trip(tmp_path: Path) -> None:
    """Verify Parquet export and reading round-trip."""
    original_bars = [
        {
            "timestamp": "2026-01-15T12:00:00+00:00",
            "open": 50.0,
            "high": 52.0,
            "low": 49.5,
            "close": 51.5,
            "tick_volume": 2000,
        }
    ]
    target_parquet = tmp_path / "test.parquet"
    export_bars_to_parquet(original_bars, target_parquet)
    assert target_parquet.exists()

    reparsed = read_parquet_bars(target_parquet)
    assert len(reparsed) == 1
    assert reparsed[0]["open"] == 50.0
    assert reparsed[0]["tick_volume"] == 2000


# ============================================================================
# Partition Selection & No-Collision
# ============================================================================


def test_partition_discovery_exact_symbol_matching(tmp_path: Path) -> None:
    """Verify find_matching_partitions matches exact symbol without prefix collision."""
    (tmp_path / "EURUSD").mkdir()
    (tmp_path / "EURUSD" / "2026.csv").write_text("dummy", encoding="utf-8")

    (tmp_path / "EURUSD_PRO").mkdir()
    (tmp_path / "EURUSD_PRO" / "2026.csv").write_text("dummy", encoding="utf-8")

    (tmp_path / "EURUSD_M1.csv").write_text("dummy", encoding="utf-8")

    matched_exact = find_matching_partitions(tmp_path, "EURUSD", "M1")
    matched_stems = [p.name for p in matched_exact]

    assert "2026.csv" in matched_stems or "EURUSD_M1.csv" in matched_stems
    # Ensure EURUSD_PRO partition is NOT included in EURUSD partitions
    for p in matched_exact:
        assert "EURUSD_PRO" not in str(p)
