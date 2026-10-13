"""Unit tests for StrategyQuant US Equity broker and symbol catalog."""

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
from app.services.brokers.sq_equity import (
    SQEquityBroker,
    _clean_symbol,
    create_adapter,
)
from app.services.libs.data import get_historical_bars


def _create_mock_parquet(file_path: Path, rows: list[dict[str, Any]]) -> None:
    """Helper creating a real Parquet file on disk for isolated testing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pydict: dict[str, list[Any]] = {}
    if rows:
        for k in rows[0].keys():
            pydict[k] = [r[k] for r in rows]
    table = pa.Table.from_pydict(pydict)
    pq.write_table(table, file_path)


def test_sq_equity_adapter_and_protocol() -> None:
    """Verify SQEquityBroker creates adapter and inherits DataBrokerBackend."""
    broker = create_adapter()
    assert isinstance(broker, SQEquityBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "SQ_Equity"


def test_clean_symbol() -> None:
    """Verify symbol cleaning logic."""
    assert _clean_symbol("AAPL_US") == "AAPL"
    assert _clean_symbol("AAPL.US") == "AAPL"
    assert _clean_symbol("AAPL") == "AAPL"


def test_symbol_info_and_catalog() -> None:
    """Verify symbol_info returns valid SymbolSnapshot for US equities."""
    broker = SQEquityBroker()
    snap = broker.symbol_info("AAPL")
    assert isinstance(snap, SymbolSnapshot)
    assert snap.name == "AAPL"
    assert snap.digits == 2
    assert snap.point == 0.01

    symbols = broker.symbols_get()
    assert "AAPL" in symbols or len(symbols) > 0


def test_fetch_bars_from_local_parquet(tmp_path: Path) -> None:
    """Verify fetch_bars extracts historical bars from local Parquet files."""
    aapl_dir = tmp_path / "d1" / "aapl"
    aapl_dir.mkdir(parents=True, exist_ok=True)
    _create_mock_parquet(
        aapl_dir / "2023.parquet",
        [
            {
                "DateTime": datetime(2023, 1, 3, tzinfo=UTC),
                "Open": 128.0,
                "High": 129.0,
                "Low": 125.0,
                "Close": 127.0,
                "Volume": 1000000,
            },
            {
                "DateTime": datetime(2023, 1, 4, tzinfo=UTC),
                "Open": 127.0,
                "High": 130.0,
                "Low": 126.0,
                "Close": 129.0,
                "Volume": 1100000,
            },
        ],
    )

    broker = SQEquityBroker(data_dir=tmp_path, enable_cdn_download=False)
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
    assert bars[0]["open"] == 128.0
    assert bars[1]["close"] == 129.0


def test_fetch_bars_via_data_lib(tmp_path: Path) -> None:
    """Verify get_historical_bars works with SQEquityBroker."""
    aapl_dir = tmp_path / "d1" / "aapl"
    aapl_dir.mkdir(parents=True, exist_ok=True)
    _create_mock_parquet(
        aapl_dir / "2023.parquet",
        [
            {
                "DateTime": datetime(2023, 1, 3, tzinfo=UTC),
                "Open": 128.0,
                "High": 129.0,
                "Low": 125.0,
                "Close": 127.0,
                "Volume": 1000000,
            }
        ],
    )

    broker = SQEquityBroker(data_dir=tmp_path, enable_cdn_download=False)

    async def scenario() -> None:
        bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=1)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].close == 127.0

    asyncio.run(scenario())


def test_fetch_bars_no_data_raises_bridge_error(tmp_path: Path) -> None:
    """Verify fetch_bars raises BridgeError when no data is found."""
    broker = SQEquityBroker(data_dir=tmp_path, enable_cdn_download=False)
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
    assert exc_info.value.code == "NO_DATA"
