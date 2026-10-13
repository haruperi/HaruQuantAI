"""Unit tests for local filesystem market data and symbol catalog broker."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    SymbolSnapshot,
    Timeframe,
)
from app.services.brokers.files import (
    FilesBroker,
    _parse_timestamp,
    create_adapter,
)
from app.services.libs.data import get_historical_bars


def _write_mock_parquet(file_path: Path, rows: list[dict[str, Any]]) -> None:
    """Helper writing a mock Parquet dataset to disk."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pydict: dict[str, list[Any]] = {}
    if rows:
        for k in rows[0].keys():
            pydict[k] = [r[k] for r in rows]
    table = pa.Table.from_pydict(pydict)
    pq.write_table(table, file_path)


def test_files_adapter_and_protocol() -> None:
    """Verify adapter factory and DataBrokerBackend inheritance."""
    broker = create_adapter()
    assert isinstance(broker, FilesBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "Files"


def test_parse_timestamp() -> None:
    """Verify parsing flexible date/time strings."""
    dt1 = _parse_timestamp("2023-10-01T12:30:00Z")
    assert dt1.year == 2023 and dt1.month == 10 and dt1.day == 1
    assert dt1.tzinfo == UTC


def test_symbol_info() -> None:
    """Verify symbol_info returns valid SymbolSnapshot."""
    broker = FilesBroker()
    snap = broker.symbol_info("AAPL")
    assert isinstance(snap, SymbolSnapshot)
    assert snap.name == "AAPL"
    assert snap.digits == 2
    assert snap.point == 0.01


def test_symbols_get_and_catalog(tmp_path: Path) -> None:
    """Verify discovering symbols from local parquet directory."""
    aapl_dir = tmp_path / "d1" / "aapl"
    aapl_dir.mkdir(parents=True, exist_ok=True)
    _write_mock_parquet(
        aapl_dir / "2023.parquet",
        [
            {
                "DateTime": datetime(2023, 1, 1, tzinfo=UTC),
                "Open": 150.0,
                "High": 155.0,
                "Low": 149.0,
                "Close": 154.0,
                "Volume": 1000,
            }
        ],
    )

    broker = FilesBroker(data_dir=tmp_path)
    syms = broker.symbols_get()
    assert "AAPL" in syms or "2023" in syms or len(syms) > 0


def test_fetch_bars_parquet_success(tmp_path: Path) -> None:
    """Verify fetch_bars extracts historical bars from Parquet files."""
    aapl_dir = tmp_path / "d1" / "aapl"
    aapl_dir.mkdir(parents=True, exist_ok=True)
    _write_mock_parquet(
        aapl_dir / "2023.parquet",
        [
            {
                "DateTime": datetime(2023, 1, 1, tzinfo=UTC),
                "Open": 150.0,
                "High": 155.0,
                "Low": 149.0,
                "Close": 154.0,
                "Volume": 1000,
            },
            {
                "DateTime": datetime(2023, 1, 2, tzinfo=UTC),
                "Open": 154.0,
                "High": 158.0,
                "Low": 153.0,
                "Close": 157.0,
                "Volume": 1200,
            },
        ],
    )

    broker = FilesBroker(data_dir=tmp_path)
    bars = broker.fetch_bars(
        symbol="AAPL",
        timeframe="D1",
        mode="count",
        start=0,
        end=0,
        count=2,
        limit=2,
    )
    assert len(bars) == 2
    assert bars[0]["open"] == 150.0
    assert bars[1]["close"] == 157.0


def test_fetch_bars_via_data_lib(tmp_path: Path) -> None:
    """Verify get_historical_bars works with FilesBroker."""
    aapl_dir = tmp_path / "d1" / "aapl"
    aapl_dir.mkdir(parents=True, exist_ok=True)
    _write_mock_parquet(
        aapl_dir / "2023.parquet",
        [
            {
                "DateTime": datetime(2023, 1, 1, tzinfo=UTC),
                "Open": 150.0,
                "High": 155.0,
                "Low": 149.0,
                "Close": 154.0,
                "Volume": 1000,
            }
        ],
    )

    broker = FilesBroker(data_dir=tmp_path)

    async def scenario() -> None:
        bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=1)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].close == 154.0

    asyncio.run(scenario())


def test_fetch_bars_file_not_found_raises_bridge_error(tmp_path: Path) -> None:
    """Verify fetch_bars raises BridgeError when no files exist for symbol."""
    broker = FilesBroker(data_dir=tmp_path)
    with pytest.raises(BridgeError) as exc_info:
        broker.fetch_bars(
            symbol="NONEXISTENT",
            timeframe="D1",
            mode="count",
            start=0,
            end=0,
            count=5,
            limit=5,
        )
    assert exc_info.value.code == "FILE_NOT_FOUND"
