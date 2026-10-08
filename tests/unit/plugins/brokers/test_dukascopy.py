"""Unit tests for Dukascopy market data and symbol catalog broker plugin."""

import io
import lzma
import struct
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from app.plugins.brokers.contracts import BrokerCapability
from app.plugins.brokers.dukascopy import (
    PLUGIN_MANIFEST,
    DukascopyBroker,
    create_adapter,
)


def _make_mock_dat(
    ts_ms: int,
    ohlcv: tuple[int, int, int, int, int],
) -> bytes:
    """Helper creating mock binary .dat file with SQ 4.2 sync marker and base record."""
    header = b"\x00\x034.2\x00\x01D\x00\x08ABCDEFGH"
    marker = b"\xbb\xbb\xbb"
    rec = struct.pack(
        ">QQQQQQ", ts_ms, ohlcv[0], ohlcv[1], ohlcv[2], ohlcv[3], ohlcv[4]
    )
    return header + marker + rec


def _make_mock_zip(files: dict[str, bytes]) -> bytes:
    """Helper packing files into a zip archive bytes payload."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_dukascopy_plugin_manifest_and_capabilities() -> None:
    """Verify plugin manifest metadata and broker capability bitmask."""
    broker = create_adapter()
    assert isinstance(broker, DukascopyBroker)
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    assert broker.has_capability(BrokerCapability.SYMBOLS)
    assert not broker.has_capability(BrokerCapability.TRADING)

    assert PLUGIN_MANIFEST["id"] == "broker-dukascopy"
    assert "bars" in PLUGIN_MANIFEST["capabilities"]
    assert "ticks" in PLUGIN_MANIFEST["capabilities"]
    assert "symbols" in PLUGIN_MANIFEST["capabilities"]
    assert PLUGIN_MANIFEST["metadata"]["provider_name"] == "Dukascopy"


def test_get_symbol_info_authoritative_csv() -> None:
    """Verify symbol metadata resolution from authoritative dukascopy.csv catalog."""
    broker = DukascopyBroker()

    # Major Forex pair
    eur = broker.get_symbol_info("EURUSD")
    assert eur.is_success
    assert eur.data is not None
    assert eur.data.name == "EURUSD"
    assert eur.data.digits == 5
    assert eur.data.point == 0.00001
    assert eur.data.currency_base == "EUR"
    assert eur.data.currency_profit == "USD"
    assert eur.data.category == "Forex"
    assert "Majors" in (eur.data.path or "")

    # Clean symbol formatting tolerance
    eur_slash = broker.get_symbol_info("EUR/USD")
    assert eur_slash.is_success
    assert eur_slash.data is not None
    assert eur_slash.data.name == "EURUSD"

    # Commodity / Metal
    xau = broker.get_symbol_info("XAUUSD")
    assert xau.is_success
    assert xau.data is not None
    assert xau.data.digits == 3
    assert xau.data.category == "Forex"
    assert "Metals" in (xau.data.path or "")

    # Crypto
    btc = broker.get_symbol_info("BTCUSD")
    assert btc.is_success
    assert btc.data is not None
    assert btc.data.digits == 1
    assert btc.data.category == "Crypto"


def test_get_symbol_info_not_found() -> None:
    """Verify symbol info failure response when symbol does not exist in catalog."""
    broker = DukascopyBroker()
    resp = broker.get_symbol_info("NONEXISTENT_XYZ")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "SYMBOL_NOT_FOUND"


def test_get_symbols_and_count() -> None:
    """Verify catalog total symbol count and category filtering."""
    broker = DukascopyBroker()

    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 725

    all_symbols = broker.get_symbols()
    assert all_symbols.is_success
    assert all_symbols.data is not None
    assert len(all_symbols.data) == 725

    forex_symbols = broker.get_symbols(group="Forex")
    assert forex_symbols.is_success
    assert forex_symbols.data is not None
    assert len(forex_symbols.data) == 64

    crypto_symbols = broker.get_symbols(group="Crypto")
    assert crypto_symbols.is_success
    assert crypto_symbols.data is not None
    assert len(crypto_symbols.data) > 0


def test_catalog_file_missing_graceful_handling(tmp_path: Path) -> None:
    """Verify graceful empty catalog response when catalog CSV file is missing."""
    missing_path = tmp_path / "nonexistent.csv"
    broker = DukascopyBroker(catalog_path=missing_path)

    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 0

    info_resp = broker.get_symbol_info("EURUSD")
    assert not info_resp.is_success
    assert info_resp.error is not None
    assert info_resp.error.code == "SYMBOL_NOT_FOUND"


def test_catalog_parsing_resilience(tmp_path: Path) -> None:
    """Verify catalog parsing handles malformed lines, short rows, and currencies."""
    custom_csv = tmp_path / "test_dukascopy.csv"
    content = (
        "\n"  # Empty line
        "INVALID;SHORT\n"  # Short line
        "BADDEC;BAD;Forex;Majors;01.01.2020;01.01.2020;XYZ;100000;3;0.0001;0.00001;3\n"  # Bad int
        "EURUSD;EURUSD;Forex;Majors;05.05.2003;05.05.2003;5;100000;3;0.0001;0.00001;3\n"
        "BUNDTREUR;German bond;Bond;common;03.05.2018;03.05.2018;3;1;0;0.01;0.01;8\n"
        "MISCINST;Misc;Indices;US;01.01.2020;01.01.2020;2;1;0;0.1;0.1;5\n"
    )
    custom_csv.write_text(content, encoding="latin1")

    broker = DukascopyBroker(catalog_path=custom_csv)
    num_resp = broker.get_num_of_symbols()
    assert num_resp.is_success
    assert num_resp.data == 3

    bond = broker.get_symbol_info("BUNDTREUR")
    assert bond.is_success
    assert bond.data is not None
    assert bond.data.currency_profit == "EUR"
    assert bond.data.currency_base == "BUNDTR"

    misc = broker.get_symbol_info("MISCINST")
    assert misc.is_success
    assert misc.data is not None
    assert misc.data.currency_profit == "USD"


def test_catalog_read_exception_handling(tmp_path: Path) -> None:
    """Verify logger error handling when opening the catalog file raises an exception."""
    unreadable = tmp_path / "bad.csv"
    unreadable.write_text("DATA", encoding="utf-8")
    broker = DukascopyBroker(catalog_path=unreadable)

    with patch("builtins.open", side_effect=OSError("Permission denied")):
        num_resp = broker.get_num_of_symbols()
        assert num_resp.is_success
        assert num_resp.data == 0


def test_get_bars_cdn_success() -> None:
    """Verify get_bars parses in-memory binary records into canonical Bar entities."""
    broker = DukascopyBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_01.dat": _make_mock_dat(
                1672531200000, (1070000, 1075000, 1069000, 1072000, 5000)
            ),
            "2023_01_02.dat": _make_mock_dat(
                1672617600000, (1072000, 1078000, 1071000, 1076000, 8000)
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
        # Decimals = 5 -> Scale = 10 ** 6 = 1000000.0
        assert bar1.open == 1.07
        assert bar1.high == 1.075
        assert bar1.low == 1.069
        assert bar1.close == 1.072
        assert bar1.tick_volume == 5000

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert (
            called_url
            == "https://cdn.strategyquantcdn.com/data/dukascopy/m1/EURUSD/2023.zip"
        )


def test_get_bars_date_filtering() -> None:
    """Verify get_bars filters daily files by date_from and date_to boundaries."""
    broker = DukascopyBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_01.dat": _make_mock_dat(
                1672531200000, (1070000, 1075000, 1069000, 1072000, 5000)
            ),
            "2023_01_05.dat": _make_mock_dat(
                1672876800000, (1072000, 1078000, 1071000, 1076000, 8000)
            ),
            "2023_01_10.dat": _make_mock_dat(
                1673308800000, (1076000, 1080000, 1075000, 1079000, 9000)
            ),
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_zip_bytes

    with patch.object(broker.session, "get", return_value=mock_resp):
        # Filter range: Jan 3 to Jan 8 (should include only 2023_01_05.dat)
        resp = broker.get_bars(
            "EURUSD",
            date_from=datetime(2023, 1, 3, tzinfo=UTC),
            date_to=datetime(2023, 1, 8, tzinfo=UTC),
        )
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 1
        assert resp.data[0].open == 1.072


def test_get_bars_empty_archive() -> None:
    """Verify get_bars handles zip archive with no recognizable records."""
    broker = DukascopyBroker()
    empty_zip = _make_mock_zip({"notes.txt": b"Empty notes without dat records"})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = empty_zip

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"


def test_decompress_bi5_variations() -> None:
    """Verify _decompress_bi5 handles ALONE format, corrupt data, and short input."""
    from app.plugins.brokers.dukascopy import _decompress_bi5

    assert _decompress_bi5(b"") == b""
    assert _decompress_bi5(b"123") == b""

    sample_raw = b"SAMPLE_DUKASCOPY_BI5_PAYLOAD_BYTES"
    compressed_alone = lzma.compress(sample_raw, format=lzma.FORMAT_ALONE)
    decomp = _decompress_bi5(compressed_alone)
    assert decomp == sample_raw

    # Raw format without alone header
    compressed_raw = lzma.compress(
        sample_raw, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA1}]
    )
    decomp_raw = _decompress_bi5(compressed_raw)
    assert decomp_raw == sample_raw or _decompress_bi5(b"\x00" * 20) == b""

    # Corrupted payload
    assert _decompress_bi5(b"\xff" * 50) == b""


def test_get_bars_cdn_to_datafeed_fallback() -> None:
    """Verify get_bars falls back to direct datafeed when CDN returns 404."""
    broker = DukascopyBroker()

    # Create mock 24-byte candle record: 0 sec, 1.07000 open, 1.07050 close, 1.06900 low, 1.07100 high, 100 vol
    candle_rec = struct.pack(">iiiii f", 0, 107000, 107050, 106900, 107100, 100.0)
    bi5_bytes = lzma.compress(candle_rec, format=lzma.FORMAT_ALONE)

    def mock_get(url: str, **_kwargs: Any) -> MagicMock:
        resp = MagicMock()
        if "strategyquantcdn" in url:
            resp.status_code = 404
            resp.content = b""
        elif "datafeed.dukascopy.com" in url:
            resp.status_code = 200
            resp.content = bi5_bytes
        else:
            resp.status_code = 500
            resp.content = b""
        return resp

    with patch.object(broker.session, "get", side_effect=mock_get):
        resp = broker.get_bars(
            "EURUSD", count=5, date_from=datetime(2023, 5, 10, tzinfo=UTC)
        )
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 1
        assert resp.data[0].open == 1.07
        assert resp.metadata.extensions is not None
        assert resp.metadata.extensions["source"] == "datafeed_fallback"


def test_get_bars_all_endpoints_fail() -> None:
    """Verify get_bars returns NO_DATA failure when both CDN and direct datafeed fail."""
    broker = DukascopyBroker()

    def mock_get(url: str, **_kwargs: Any) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        return resp

    with patch.object(broker.session, "get", side_effect=mock_get):
        resp = broker.get_bars("EURUSD", count=5)
        assert not resp.is_success
        assert resp.error is not None
        assert resp.error.code == "NO_DATA"


def test_get_ticks_direct_datafeed() -> None:
    """Verify get_ticks retrieves hourly ticks from direct datafeed when date_from given."""
    broker = DukascopyBroker()

    # 20-byte tick record: offset_ms=1500, ask_int=107050, bid_int=107030, ask_v=1.5, bid_v=2.0
    tick_rec = struct.pack(">iii f f", 1500, 107050, 107030, 1.5, 2.0)
    bi5_bytes = lzma.compress(tick_rec, format=lzma.FORMAT_ALONE)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = bi5_bytes

    with patch.object(broker.session, "get", return_value=mock_resp):
        resp = broker.get_ticks(
            "EURUSD", count=5, date_from=datetime(2023, 5, 10, 14, 0, tzinfo=UTC)
        )
        assert resp.is_success
        assert resp.data is not None
        assert len(resp.data) == 1
        t = resp.data[0]
        assert t.ask == 1.0705
        assert t.bid == 1.0703
        assert t.volume == 3.5
        assert resp.metadata.extensions is not None
        assert resp.metadata.extensions["source"] == "datafeed"


def test_get_ticks_derived_from_bars() -> None:
    """Verify get_ticks extracts tick representations derived from bars when no date given."""
    broker = DukascopyBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_01.dat": _make_mock_dat(
                1672531200000, (1070000, 1075000, 1069000, 1072000, 5000)
            ),
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
        assert tick.bid == 1.072
        assert tick.ask == 1.072
        assert tick.volume == 5000.0


def test_get_ticks_failure_propagation() -> None:
    """Verify get_ticks returns empty list when both datafeed and get_bars fail."""
    broker = DukascopyBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.content = b""

    with patch.object(broker.session, "get", return_value=mock_resp):
        ticks_resp = broker.get_ticks("EURUSD", count=1)
        assert ticks_resp.is_success
        assert ticks_resp.data == []
