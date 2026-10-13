"""Unit tests for Darwinex broker and symbol catalog."""

from __future__ import annotations

import asyncio
import io
import struct
import zipfile
from datetime import UTC, datetime
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
from app.services.brokers.darwinex import (
    DarwinexBroker,
    create_adapter,
)
from app.services.libs.data import get_historical_bars


def _make_mock_dat(
    timestamp_ms: int,
    ask_int: int,
    bid_int: int,
    cols: int = 8,
) -> bytes:
    """Build a mock SQ 4.2 binary .dat file with a valid base record."""
    buf = bytearray()
    buf += struct.pack(">h", 3) + b"4.2"
    buf += struct.pack(">h", 1) + b"D"
    buf += struct.pack(">h", 6) + b"EURUSD"
    buf += struct.pack(">q", 1)  # rows
    buf += struct.pack(">i", cols)  # cols

    for _ in range(cols):
        buf += struct.pack(">h", 1) + b"_"
        buf += struct.pack(">i", 0)

    buf += b"\x00\x06SnRbTs\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x00\x00\x00\x00\xbb\xbb"

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


def test_create_adapter_and_protocol() -> None:
    """Verify adapter factory and DataBrokerBackend inheritance."""
    broker = create_adapter()
    assert isinstance(broker, DarwinexBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "Darwinex"


def test_default_catalog_loading() -> None:
    """Verify loading real instruments from darwinex.csv."""
    broker = DarwinexBroker()
    symbols = broker.symbols_get()
    assert len(symbols) >= 300

    # Forex
    fx = broker.symbol_info("EURUSD")
    assert isinstance(fx, SymbolSnapshot)
    assert fx.digits == 5

    # Stock
    aapl = broker.symbol_info("AAPL")
    assert isinstance(aapl, SymbolSnapshot)
    assert aapl.digits == 3


def test_symbol_fallback() -> None:
    """Verify unknown symbol returns fallback SymbolSnapshot."""
    broker = DarwinexBroker()
    snap = broker.symbol_info("NONEXISTENT_XYZ")
    assert isinstance(snap, SymbolSnapshot)
    assert snap.name == "NONEXISTENTXYZ"


def test_custom_catalog_path(tmp_path: Path) -> None:
    """Verify parsing a custom catalog file."""
    custom_csv = tmp_path / "custom_darwinex.csv"
    content = (
        "EURUSD;01.10.2017;5;100000;3;0.0001;0.00001;3\n"
        "AUS200;01.10.2017;3;25;3;1;1;6\n"
        "AAPL;01.10.2017;3;1;0;0.01;0.01;1\n"
        "CORRUPT_LINE_TEST\n"
    )
    custom_csv.write_text(content, encoding="latin1")

    broker = DarwinexBroker(catalog_path=custom_csv)
    symbols = broker.symbols_get()
    assert len(symbols) == 3

    aus = broker.symbol_info("AUS200")
    assert aus.name == "AUS200"
    assert aus.digits == 3


def test_get_bars_cdn_success() -> None:
    """Verify fetch_bars parses in-memory binary records into bar dicts."""
    broker = DarwinexBroker()
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
        bars = broker.fetch_bars(
            symbol="EURUSD",
            timeframe="D1",
            mode="count",
            start=0,
            end=0,
            count=2,
            limit=2,
        )
        assert len(bars) == 2

        bar1 = bars[0]
        assert bar1["open"] == 1.06997
        assert bar1["close"] == 1.06997
        assert bar1["high"] == 1.07142
        assert bar1["low"] == 1.06997
        assert bar1["tick_volume"] == 1

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "EURUSD" in called_url


def test_fetch_bars_via_data_lib() -> None:
    """Verify get_historical_bars works with DarwinexBroker."""
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

    async def scenario() -> None:
        with patch.object(broker.session, "get", return_value=mock_resp):
            bars = await get_historical_bars(
                broker, "EURUSD", Timeframe.PERIOD_D1, count=1
            )
            assert len(bars) == 1
            assert isinstance(bars[0], MarketBar)
            assert bars[0].close == 1.06997

    asyncio.run(scenario())


def test_fetch_bars_date_filtering() -> None:
    """Verify fetch_bars filters daily records by date_from and date_to."""
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

    d_from = int(datetime(2023, 1, 3, tzinfo=UTC).timestamp())
    d_to = int(datetime(2023, 1, 8, tzinfo=UTC).timestamp())

    with patch.object(broker.session, "get", return_value=mock_resp):
        bars = broker.fetch_bars(
            symbol="EURUSD",
            timeframe="D1",
            mode="range",
            start=d_from,
            end=d_to,
            count=10,
            limit=10,
        )
        assert len(bars) == 1
        assert bars[0]["open"] == 1.071


def test_fetch_bars_http_404_raises_bridge_error() -> None:
    """Verify fetch_bars raises BridgeError when CDN returns 404."""
    broker = DarwinexBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b"Not found"

    with patch.object(broker.session, "get", return_value=mock_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="EURUSD",
                timeframe="D1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "NO_DATA"


def test_fetch_bars_empty_archive() -> None:
    """Verify fetch_bars raises BridgeError on archive without .dat files."""
    broker = DarwinexBroker()
    empty_zip = _make_mock_zip({"readme.txt": b"Just text"})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = empty_zip

    with patch.object(broker.session, "get", return_value=mock_resp):
        with pytest.raises(BridgeError) as exc_info:
            broker.fetch_bars(
                symbol="EURUSD",
                timeframe="D1",
                mode="count",
                start=0,
                end=0,
                count=5,
                limit=5,
            )
        assert exc_info.value.code == "NO_DATA"
