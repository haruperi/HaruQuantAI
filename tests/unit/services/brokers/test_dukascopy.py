"""Unit tests for Dukascopy market data and symbol catalog broker."""

from __future__ import annotations

import asyncio
import io
import struct
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    SymbolSnapshot,
    Timeframe,
)
from app.services.brokers.dukascopy import (
    DukascopyBroker,
    create_adapter,
)
from app.services.libs.data import get_historical_bars


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


def test_dukascopy_adapter_and_protocol() -> None:
    """Verify DukascopyBroker creates adapter and inherits DataBrokerBackend."""
    broker = create_adapter()
    assert isinstance(broker, DukascopyBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "Dukascopy"


def test_get_symbol_info_authoritative_csv() -> None:
    """Verify symbol metadata resolution from authoritative dukascopy.csv catalog."""
    broker = DukascopyBroker()

    # Major Forex pair
    eur = broker.symbol_info("EURUSD")
    assert isinstance(eur, SymbolSnapshot)
    assert eur.name == "EURUSD"
    assert eur.digits == 5
    assert eur.point == 0.00001

    # Clean symbol formatting tolerance
    eur_slash = broker.symbol_info("EUR/USD")
    assert isinstance(eur_slash, SymbolSnapshot)
    assert eur_slash.name == "EURUSD"

    # Commodity / Metal
    xau = broker.symbol_info("XAUUSD")
    assert isinstance(xau, SymbolSnapshot)
    assert xau.digits == 3

    # Crypto
    btc = broker.symbol_info("BTCUSD")
    assert isinstance(btc, SymbolSnapshot)
    assert btc.digits == 1


def test_get_symbols_and_count() -> None:
    """Verify catalog total symbol count and discovery."""
    broker = DukascopyBroker()
    symbols = broker.symbols_get()
    assert len(symbols) >= 700
    assert "EURUSD" in symbols
    assert "BTCUSD" in symbols


def test_symbol_fallback() -> None:
    """Verify unknown symbol returns fallback SymbolSnapshot."""
    broker = DukascopyBroker()
    snap = broker.symbol_info("NONEXISTENT_XYZ")
    assert isinstance(snap, SymbolSnapshot)
    assert snap.name == "NONEXISTENT_XYZ"


def test_catalog_parsing_resilience(tmp_path: Path) -> None:
    """Verify catalog parsing handles custom csv lines."""
    custom_csv = tmp_path / "test_dukascopy.csv"
    content = (
        "\n"  # Empty line
        "INVALID;SHORT\n"  # Short line
        "BADDEC;BAD;Forex;Majors;01.01.2020;01.01.2020;XYZ;100000;3;0.0001;0.00001;3\n"
        "EURUSD;EURUSD;Forex;Majors;05.05.2003;05.05.2003;5;100000;3;0.0001;0.00001;3\n"
        "BUNDTREUR;German bond;Bond;common;03.05.2018;03.05.2018;3;1;0;0.01;0.01;8\n"
        "MISCINST;Misc;Indices;US;01.01.2020;01.01.2020;2;1;0;0.1;0.1;5\n"
    )
    custom_csv.write_text(content, encoding="latin1")

    broker = DukascopyBroker(catalog_path=custom_csv)
    symbols = broker.symbols_get()
    assert len(symbols) == 3

    bund = broker.symbol_info("BUNDTREUR")
    assert bund.digits == 3
    assert bund.name == "BUNDTREUR"


def test_fetch_bars_cdn_success() -> None:
    """Verify fetch_bars parses in-memory binary records into bar dicts."""
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
        bars = broker.fetch_bars(
            symbol="EURUSD",
            timeframe="M1",
            mode="count",
            start=0,
            end=0,
            count=2,
            limit=2,
        )
        assert len(bars) == 2

        bar1 = bars[0]
        assert bar1["open"] == 1.07
        assert bar1["high"] == 1.075
        assert bar1["low"] == 1.069
        assert bar1["close"] == 1.072
        assert bar1["tick_volume"] == 5000

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "EURUSD" in called_url


def test_fetch_bars_via_data_lib() -> None:
    """Verify get_historical_bars works with DukascopyBroker."""
    broker = DukascopyBroker()
    mock_zip_bytes = _make_mock_zip(
        {
            "2023_01_01.dat": _make_mock_dat(
                1672531200000, (1070000, 1075000, 1069000, 1072000, 5000)
            )
        }
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_zip_bytes

    async def scenario() -> None:
        with patch.object(broker.session, "get", return_value=mock_resp):
            bars = await get_historical_bars(
                broker, "EURUSD", Timeframe.PERIOD_M1, count=1
            )
            assert len(bars) == 1
            assert isinstance(bars[0], MarketBar)
            assert bars[0].close == 1.072

    asyncio.run(scenario())


def test_fetch_bars_http_404_raises_bridge_error() -> None:
    """Verify fetch_bars raises BridgeError when CDN returns 404."""
    broker = DukascopyBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b"Not found"

    with patch.object(broker.session, "get", return_value=mock_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="EURUSD",
                timeframe="M1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "NO_DATA"
