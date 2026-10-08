"""Unit tests for StrategyQuant Continuous Futures broker and symbol catalog plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from app.plugins.brokers.contracts import (
    BrokerCapability,
    TimeFrame,
    TradeRequest,
)
from app.plugins.brokers.sq_futures import (
    PLUGIN_MANIFEST,
    SQFuturesBroker,
    _clean_symbol,
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


def test_clean_symbol_normalization() -> None:
    """Verify continuous futures symbol cleanup utility handles .D and case."""
    assert _clean_symbol("@ES") == "@ES"
    assert _clean_symbol("@es.d") == "@ES"
    assert _clean_symbol("@CL.D") == "@CL"
    assert _clean_symbol("cl") == "CL"


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
    """Verify loading, parsing, and filtering historical candlestick bars."""
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


def test_sq_futures_get_bars_missing_symbol(tmp_path: Path) -> None:
    """Verify failure response when target symbol directory does not exist."""
    data_dir = tmp_path / "sq_futures"
    broker = SQFuturesBroker(data_dir=data_dir)

    resp = broker.get_bars("UNKNOWN_TICKER")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"


def test_sq_futures_get_bars_empty_partition_directory(tmp_path: Path) -> None:
    """Verify failure response when target directory exists but has no parquet files."""
    empty_dir = tmp_path / "sq_futures" / "d1" / "empty_sym"
    empty_dir.mkdir(parents=True, exist_ok=True)

    broker = SQFuturesBroker(data_dir=tmp_path / "sq_futures")
    resp = broker.get_bars("EMPTY_SYM")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "NO_DATA"


def test_sq_futures_get_bars_read_error(tmp_path: Path) -> None:
    """Verify failure response when parquet file reading raises an exception."""
    corrupt_file = tmp_path / "sq_futures" / "d1" / "corrupt" / "bad.parquet"
    corrupt_file.parent.mkdir(parents=True, exist_ok=True)
    corrupt_file.write_bytes(b"not a valid parquet file contents")

    broker = SQFuturesBroker(data_dir=tmp_path / "sq_futures")
    resp = broker.get_bars("CORRUPT")
    assert not resp.is_success
    assert resp.error is not None
    assert resp.error.code == "READ_ERROR"


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
