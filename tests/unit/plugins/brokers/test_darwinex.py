"""Unit tests for Darwinex broker and symbol catalog plugin."""

from __future__ import annotations

import io
import struct
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.plugins.brokers.contracts import BrokerCapability, TradeRequest
from app.plugins.brokers.darwinex import (
    DarwinexBroker,
    create_adapter,
)


def _make_mock_dat(
    timestamp_ms: int,
    ask_int: int,
    bid_int: int,
    cols: int = 8,
) -> bytes:
    """Build a mock SQ 4.2 binary .dat file with a valid base record."""
    buf = bytearray()
    # Header: "4.2", "D", "EURUSD", count=1, cols=8
    buf += struct.pack(">h", 3) + b"4.2"
    buf += struct.pack(">h", 1) + b"D"
    buf += struct.pack(">h", 6) + b"EURUSD"
    buf += struct.pack(">q", 1)  # rows
    buf += struct.pack(">i", cols)  # cols

    for _ in range(cols):
        buf += struct.pack(">h", 1) + b"_"
        buf += struct.pack(">i", 0)

    # Sync sequence
    buf += b"\x00\x06SnRbTs\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x00\x00\x00\x00\xbb\xbb"

    # Base record: 8 int64 values
    # base_ts, ask_raw, bid_raw, v1, v2, v3, v4, v5
    buf += struct.pack(
        ">8q",
        timestamp_ms,
        ask_int,
        bid_int,
        100000,
        200000,
        300000,
        400000,
        500000,
    )
    return bytes(buf)


def _make_mock_zip(files: dict[str, bytes]) -> bytes:
    """Pack in-memory files into a zip archive."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname, content in files.items():
            z.writestr(fname, content)
    return bio.getvalue()


def test_create_adapter_and_manifest() -> None:
    """Verify adapter factory and capability bitmask."""
    broker = create_adapter()
    assert isinstance(broker, DarwinexBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)


def test_default_catalog_loading() -> None:
    """Verify loading the real 328 instruments from darwinex.csv."""
    broker = DarwinexBroker()
    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 328

    # Forex
    fx_resp = broker.get_symbol_info("EURUSD")
    assert fx_resp.is_success
    assert fx_resp.data is not None
    assert fx_resp.data.digits == 5
    assert fx_resp.data.category == "Forex"
    assert fx_resp.data.currency_base == "EUR"
    assert fx_resp.data.currency_profit == "USD"

    # Stock
    aapl_resp = broker.get_symbol_info("AAPL")
    assert aapl_resp.is_success
    assert aapl_resp.data is not None
    assert aapl_resp.data.digits == 3
    assert aapl_resp.data.category == "Stocks"
    assert aapl_resp.data.currency_profit == "USD"

    # Commodity
    oil_resp = broker.get_symbol_info("XTIUSD")
    assert oil_resp.is_success
    assert oil_resp.data is not None
    assert oil_resp.data.category == "Commodities"
    assert oil_resp.data.currency_base == "XTI"
    assert oil_resp.data.currency_profit == "USD"

    # Index
    sp_resp = broker.get_symbol_info("SP500")
    assert sp_resp.is_success
    assert sp_resp.data is not None
    assert sp_resp.data.category == "Indices"
    assert sp_resp.data.currency_profit == "USD"

    # Crypto
    btc_resp = broker.get_symbol_info("XBTUSD")
    assert btc_resp.is_success
    assert btc_resp.data is not None
    assert btc_resp.data.category == "Crypto"
    assert btc_resp.data.currency_base == "XBT"
    assert btc_resp.data.currency_profit == "USD"


def test_symbol_not_found() -> None:
    """Verify unknown symbol returns SYMBOL_NOT_FOUND error."""
    broker = DarwinexBroker()
    resp = broker.get_symbol_info("NONEXISTENT_XYZ")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "SYMBOL_NOT_FOUND"


def test_get_symbols_group_filtering() -> None:
    """Verify get_symbols filtering by category or subcategory."""
    broker = DarwinexBroker()
    all_syms = broker.get_symbols()
    assert all_syms.is_success
    assert len(all_syms.data) == 328

    forex_syms = broker.get_symbols(group="Forex")
    assert forex_syms.is_success
    assert len(forex_syms.data) > 30
    for s in forex_syms.data:
        assert s.category == "Forex"

    crypto_syms = broker.get_symbols(group="Crypto")
    assert crypto_syms.is_success
    assert len(crypto_syms.data) > 0


def test_custom_catalog_path(tmp_path: Path) -> None:
    """Verify parsing a custom catalog file with various instrument types."""
    custom_csv = tmp_path / "custom_darwinex.csv"
    content = (
        "EURUSD;01.10.2017;5;100000;3;0.0001;0.00001;3\n"
        "AUS200;01.10.2017;3;25;3;1;1;6\n"
        "AAPL;01.10.2017;3;1;0;0.01;0.01;1\n"
        "CORRUPT_LINE_TEST\n"
    )
    custom_csv.write_text(content, encoding="latin1")

    broker = DarwinexBroker(catalog_path=custom_csv)
    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 3

    aus = broker.get_symbol_info("AUS200")
    assert aus.is_success
    assert aus.data is not None
    assert aus.data.currency_profit == "AUD"


def test_missing_catalog_file(tmp_path: Path) -> None:
    """Verify handling when catalog file does not exist."""
    missing = tmp_path / "does_not_exist.csv"
    broker = DarwinexBroker(catalog_path=missing)
    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 0


def test_catalog_exception_handling(tmp_path: Path) -> None:
    """Verify handling when opening catalog file raises an exception."""
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("DATA", encoding="utf-8")
    broker = DarwinexBroker(catalog_path=bad_file)

    with patch("builtins.open", side_effect=OSError("Read error")):
        num_resp = broker.get_num_of_symbols()
        assert num_resp.is_success
        assert num_resp.data == 0


def test_get_bars_cdn_success() -> None:
    """Verify get_bars parses in-memory binary records into canonical Bar entities."""
    broker = DarwinexBroker()
    # Decimals = 5 -> scale = 10 ** 6 = 1000000.0
    # Ask = 1071420 -> 1.07142, Bid = 1069970 -> 1.06997
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_02.dat": _make_mock_dat(
                1672617674585, ask_int=1071420, bid_int=1069970
            ),
            "2023_01_03.dat": _make_mock_dat(
                1672704074585, ask_int=1073000, bid_int=1072000
            ),
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_zip_bytes

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        resp = broker.get_bars("EURUSD", count=2)
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 2

        bar1 = resp.data[0]
        assert bar1.open == 1.06997
        assert bar1.close == 1.06997
        assert bar1.high == 1.07142
        assert bar1.low == 1.06997
        assert bar1.tick_volume == 1

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert (
            called_url
            == "https://cdn.strategyquantcdn.com/data/darwinex/EURUSD/2023.zip"
        )


def test_get_bars_date_filtering() -> None:
    """Verify get_bars filters daily files by date_from and date_to."""
    broker = DarwinexBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_01.dat": _make_mock_dat(
                1672531200000, ask_int=1071000, bid_int=1070000
            ),
            "2023_01_05.dat": _make_mock_dat(
                1672876800000, ask_int=1072000, bid_int=1071000
            ),
            "2023_01_10.dat": _make_mock_dat(
                1673308800000, ask_int=1073000, bid_int=1072000
            ),
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_zip_bytes

    with patch.object(broker.session, "get", return_value=mock_resp):
        # Range: Jan 3 to Jan 8 (should include only 2023_01_05.dat)
        resp = broker.get_bars(
            "EURUSD",
            date_from=datetime(2023, 1, 3, tzinfo=UTC),
            date_to=datetime(2023, 1, 8, tzinfo=UTC),
        )
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 1
        assert resp.data[0].open == 1.071


def test_get_bars_target_year_derivation() -> None:
    """Verify target year is derived from date_to when date_from is None."""
    broker = DarwinexBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = _make_mock_zip(
        {
            "2022_12_30.dat": _make_mock_dat(
                1672358400000, ask_int=1068000, bid_int=1067000
            )
        }
    )

    with patch.object(broker.session, "get", return_value=mock_resp) as mock_get:
        resp = broker.get_bars(
            "EURUSD",
            date_to=datetime(2022, 12, 31, tzinfo=UTC),
            start_pos=0,
        )
        assert resp.is_success
        called_url = mock_get.call_args[0][0]
        assert "2022.zip" in called_url


def test_get_bars_http_non_200() -> None:
    """Verify get_bars handles HTTP 404 or other non-200 responses cleanly."""
    broker = DarwinexBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b"Not found"

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"


def test_get_bars_empty_archive() -> None:
    """Verify get_bars handles zip archive without valid .dat files."""
    broker = DarwinexBroker()
    empty_zip = _make_mock_zip({"readme.txt": b"Just text"})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = empty_zip

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"


def test_get_bars_corrupt_dat_content() -> None:
    """Verify get_bars skips .dat files missing sync marker or truncated."""
    broker = DarwinexBroker()
    corrupt_zip = _make_mock_zip(
        {
            "2023_01_01.dat": b"INVALID_DAT_BYTES_WITHOUT_SYNC",
            "2023_01_02.dat": b"\xbb\xbbSHORT",
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = corrupt_zip

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"


def test_get_bars_network_exception() -> None:
    """Verify get_bars returns FETCH_ERROR on network exceptions."""
    broker = DarwinexBroker()

    with patch.object(
        broker.session, "get", side_effect=ConnectionError("Network down")
    ):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "FETCH_ERROR"


def test_get_ticks_success() -> None:
    """Verify get_ticks extracts canonical Tick entities."""
    broker = DarwinexBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_02.dat": _make_mock_dat(
                1672617674585, ask_int=1071420, bid_int=1069970
            )
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_zip_bytes

    with patch.object(broker.session, "get", return_value=mock_resp):
        ticks_resp = broker.get_ticks("EURUSD", count=1)
        assert ticks_resp.is_success
        assert ticks_resp.data is not None
        assert len(ticks_resp.data) == 1
        tick = ticks_resp.data[0]
        assert tick.bid == 1.06997
        assert tick.ask == 1.07142
        assert tick.volume == 1.0


def test_get_ticks_failure_propagation() -> None:
    """Verify get_ticks returns empty list when get_bars fails."""
    broker = DarwinexBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.content = b"Server error"

    with patch.object(broker.session, "get", return_value=mock_resp):
        ticks_resp = broker.get_ticks("EURUSD", count=1)
        assert ticks_resp.is_success
        assert ticks_resp.data == []


def test_trade_rejection() -> None:
    """Verify trade execution capability rejection."""
    broker = DarwinexBroker()
    trade_res = broker.trade(TradeRequest(symbol="EURUSD", volume=1.0))
    assert not trade_res.is_success
    assert trade_res.error is not None
    assert trade_res.error.code == "CAPABILITY_NOT_SUPPORTED"
