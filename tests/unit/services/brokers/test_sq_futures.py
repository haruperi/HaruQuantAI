"""Unit tests for StrategyQuant Continuous Futures broker and symbol catalog."""

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
from app.services.brokers.sq_futures import (
    SQFuturesBroker,
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


def test_sq_futures_adapter_and_protocol() -> None:
    """Verify SQFuturesBroker creates adapter and inherits DataBrokerBackend."""
    broker = create_adapter()
    assert isinstance(broker, SQFuturesBroker)
    assert isinstance(broker, DataBrokerBackend)
    assert broker.name == "SQ_Futures"


def test_clean_symbol() -> None:
    """Verify symbol cleaning for continuous futures."""
    assert _clean_symbol("@ES.D") == "@ES"
    assert _clean_symbol("@ES_LIMITED") == "@ES"
    assert _clean_symbol("@ES") == "@ES"


def test_symbol_info_and_catalog() -> None:
    """Verify symbol_info returns valid SymbolSnapshot for futures."""
    broker = SQFuturesBroker()
    snap = broker.symbol_info("@ES")
    assert isinstance(snap, SymbolSnapshot)
    assert snap.name == "@ES"
    assert snap.digits == 2
    assert snap.point in {0.01, 0.25}

    symbols = broker.symbols_get()
    assert "@ES" in symbols or len(symbols) > 0


def test_fetch_bars_from_local_parquet(tmp_path: Path) -> None:
    """Verify fetch_bars extracts historical bars from local Parquet files."""
    es_dir = tmp_path / "d1" / "@es"
    es_dir.mkdir(parents=True, exist_ok=True)
    _create_mock_parquet(
        es_dir / "2024.parquet",
        [
            {
                "DateTime": datetime(2024, 1, 2, tzinfo=UTC),
                "Open": 4800.0,
                "High": 4820.0,
                "Low": 4790.0,
                "Close": 4810.0,
                "Volume": 500000,
            },
            {
                "DateTime": datetime(2024, 1, 3, tzinfo=UTC),
                "Open": 4810.0,
                "High": 4830.0,
                "Low": 4805.0,
                "Close": 4825.0,
                "Volume": 600000,
            },
        ],
    )

    broker = SQFuturesBroker(data_dir=tmp_path, enable_cdn_download=False)
    bars = broker.fetch_bars(
        symbol="@ES",
        timeframe="D1",
        mode="count",
        start=0,
        end=0,
        count=2,
        limit=2,
    )
    assert len(bars) == 2
    assert bars[0]["open"] == 4800.0
    assert bars[1]["close"] == 4825.0


def test_fetch_bars_via_data_lib(tmp_path: Path) -> None:
    """Verify get_historical_bars works with SQFuturesBroker."""
    es_dir = tmp_path / "d1" / "@es"
    es_dir.mkdir(parents=True, exist_ok=True)
    _create_mock_parquet(
        es_dir / "2024.parquet",
        [
            {
                "DateTime": datetime(2024, 1, 2, tzinfo=UTC),
                "Open": 4800.0,
                "High": 4820.0,
                "Low": 4790.0,
                "Close": 4810.0,
                "Volume": 500000,
            }
        ],
    )

    broker = SQFuturesBroker(data_dir=tmp_path, enable_cdn_download=False)

    async def scenario() -> None:
        bars = await get_historical_bars(broker, "@ES", Timeframe.PERIOD_D1, count=1)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].close == 4810.0

    asyncio.run(scenario())


def test_fetch_bars_no_data_raises_bridge_error(tmp_path: Path) -> None:
    """Verify fetch_bars raises BridgeError when no futures data is found."""
    broker = SQFuturesBroker(data_dir=tmp_path, enable_cdn_download=False)
    with pytest.raises(BridgeError) as exc_info:
        broker.fetch_bars(
            symbol="@NONEXISTENT",
            timeframe="D1",
            mode="count",
            start=0,
            end=0,
            count=5,
            limit=5,
        )
    assert exc_info.value.code == "NO_DATA"
