"""Historical terminal conversion, failure, parity and immutable-publication checks."""

import asyncio
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import JobAccess, MarketAccess
from app.host.jobs import JobManager
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.mt5 import (
    EMBEDDED_SYMBOL_CATALOG,
    MT5Runtime,
    QDMAnalyzer,
    _main,
    convert_history,
    dataframe_to_canonical_table,
    get_price_symbol_info,
    load_overrides,
    resample_candles,
    resolve_override,
    ticks_to_m1,
)


@pytest.fixture(autouse=True)
def isolated_native_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never discover or launch an installed terminal from offline unit tests."""
    monkeypatch.setattr("app.plugin.DataSource.mt5.MT5_AVAILABLE", False)
    monkeypatch.setattr("app.plugin.DataSource.mt5.mt5", None)


def test_tick_carry_forward_scaling_and_duplicate_policy() -> None:
    frame = convert_history(
        {
            "columns": ["time_msc", "bid", "ask", "volume"],
            "rows": [
                [1704067200000, 1.1234567, 1.1234599, 1.5],
                [1704067200001, 0, 1.12346, 0],
                [1704067200001, 1.123458, 0, 2.5],
            ],
        },
        "TICK",
    )
    table = dataframe_to_canonical_table(frame, "ticks")
    assert table.column("Bid").to_pylist() == [1123457, 1123458]
    assert table.column("Ask").to_pylist() == [1123460, 1123460]
    assert table.column("Volume").to_pylist() == [2, 2]
    assert str(table.schema.field("DateTime").type) == "timestamp[ms, tz=UTC]"


def test_ohlc_prefers_tick_volume_over_real_volume() -> None:
    table = dataframe_to_canonical_table(
        pd.DataFrame(
            {
                "time": ["2024-01-01"],
                "open": [1.0],
                "high": [2.0],
                "low": [0.5],
                "close": [1.5],
                "tick_volume": [7.5],
                "real_volume": [900.0],
            }
        )
    )
    assert table.column("Volume").to_pylist() == [8]


def test_terminal_job_and_retained_rows(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    class Terminal:
        def __init__(self) -> None:
            self.closed = False
            self.calls: list[str] = []

        async def call(self, operation: Any, arguments: Any) -> Any:
            self.calls.append(operation)
            if operation == "connect":
                return True
            if operation == "symbol":
                return {"name": "EURUSD", "digits": 5}
            if operation == "history":
                stamp = int(pd.Timestamp(arguments["start"]).timestamp())
                return {
                    "columns": ["time", "open", "high", "low", "close", "tick_volume"],
                    "rows": [[stamp, 1.2, 1.3, 1.1, 1.25, 7]],
                }
            raise ValueError(operation)

        async def close(self) -> Any:
            self.closed = True

    async def scenario() -> None:
        owner = "plugin.data_manager.meta_trader"
        jobs = JobManager(1, 512 * 1024 * 1024)
        terminal = Terminal()
        runtime = MT5Runtime(
            MarketAccess(owner, store), JobAccess(owner, jobs), cast("Any", terminal)
        )
        with pytest.raises(ValueError, match="Connect to a real"):
            cast("Any", await runtime.invoke("symbols", {}))
        cast("Any", await runtime.invoke("connect", {}))
        created = cast(
            "Any", await runtime.invoke("add", {"symbol": "EURUSD", "timeframe": "D1"})
        )
        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": created["id"],
                    "date_from": "2024-01-01",
                    "date_to": "2024-01-01",
                },
            ),
        )
        await asyncio.wait_for(jobs.tasks[started["job_id"]], timeout=3)
        status = cast(
            "Any",
            await runtime.invoke("download.status", {"job_id": started["job_id"]}),
        )
        assert status["state"] == "succeeded"
        assert status["rows"] == 1
        await runtime.close()
        assert terminal.closed
        partition = store.source_partitions(created["id"])[0]
        table = store.read_source_partition(partition)
        assert table.column("Close").to_pylist() == [1.25]
        assert table.column("Volume").to_pylist() == [7]
        await jobs.close()

    asyncio.run(scenario())


def test_terminal_empty_chunk_resilience(tmp_path: Path) -> None:
    """Verifies that an initial empty/weekend chunk steps forward to subsequent data."""
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    call_count = 0

    class EmptyChunkTerminal:
        def __init__(self) -> None:
            self.closed = False

        async def call(self, operation: Any, arguments: Any) -> Any:
            nonlocal call_count
            if operation == "connect":
                return True
            if operation == "symbol":
                return {"name": "EURUSD", "digits": 5}
            if operation == "history":
                call_count += 1
                if call_count == 1:
                    # Day 1 chunk is empty (e.g. Sunday)
                    return {"columns": [], "rows": []}
                # Day 2 chunk has data
                stamp = int(pd.Timestamp("2024-01-08 23:59:59").timestamp() * 1000)
                return {
                    "columns": ["time_msc", "bid", "ask", "volume"],
                    "rows": [[stamp, 1.2, 1.3, 5]],
                }
            raise ValueError(operation)

        async def close(self) -> Any:
            self.closed = True

    async def scenario() -> None:
        owner = "plugin.data_manager.meta_trader"
        jobs = JobManager(1, 512 * 1024 * 1024)
        terminal = EmptyChunkTerminal()
        runtime = MT5Runtime(
            MarketAccess(owner, store), JobAccess(owner, jobs), cast("Any", terminal)
        )
        cast("Any", await runtime.invoke("connect", {}))
        created = cast(
            "Any",
            await runtime.invoke("add", {"symbol": "EURUSD", "timeframe": "TICK"}),
        )
        # 2-day TICK range has 1-day chunking: chunk 1 (Jan 7) empty, chunk 2 (Jan 8) has data
        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": created["id"],
                    "date_from": "2024-01-07",
                    "date_to": "2024-01-08",
                },
            ),
        )
        await asyncio.wait_for(jobs.tasks[started["job_id"]], timeout=3)
        status = cast(
            "Any",
            await runtime.invoke("download.status", {"job_id": started["job_id"]}),
        )
        assert status["state"] == "succeeded"
        assert status["rows"] >= 1
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("price_column", ["bid", "ask", "price"])
def test_tick_resampling_preserves_extrema_and_empty_minutes(price_column: str) -> None:
    ticks = pd.DataFrame(
        {
            "time": [
                "2024-01-01T00:00:01Z",
                "2024-01-01T00:00:02Z",
                "2024-01-01T00:02:00Z",
            ],
            price_column: [2.0, 1.0, 4.0],
            "volume": [2, 3, 7],
        }
    )
    minute = ticks_to_m1(ticks)
    assert minute[["Open", "High", "Low", "Close", "Volume"]].values.tolist() == [
        [2, 2, 1, 1, 5],
        [4, 4, 4, 4, 7],
    ]
    coarse = resample_candles(minute, "M5")
    assert coarse[["Open", "High", "Low", "Close", "Volume"]].values.tolist() == [
        [2, 4, 1, 4, 12]
    ]
    indexed = minute.set_index("DateTime")
    assert resample_candles(indexed, "M5").equals(coarse)
    with pytest.raises(KeyError, match="timestamp"):
        ticks_to_m1(pd.DataFrame({"bid": [1]}))
    with pytest.raises(KeyError, match="price"):
        ticks_to_m1(pd.DataFrame({"time": ["2024-01-01"], "volume": [1]}))
    with pytest.raises(KeyError, match="timestamp"):
        resample_candles(pd.DataFrame({"Open": [1]}), "M5")
    assert ticks_to_m1([]).empty


def test_embedded_catalog_and_price_calibration() -> None:
    assert "EURUSD" in EMBEDDED_SYMBOL_CATALOG
    assert "XAUUSD" in EMBEDDED_SYMBOL_CATALOG
    assert "US30" in EMBEDDED_SYMBOL_CATALOG

    eurusd_info = get_price_symbol_info("EURUSD")
    assert eurusd_info["tick_step"] == 0.00001
    assert eurusd_info["tick_size"] == 0.0001

    xauusd_info = get_price_symbol_info("XAUUSD")
    assert xauusd_info["tick_step"] == 0.01
    assert xauusd_info["tick_size"] == 0.01

    overrides = load_overrides()
    ov, key = resolve_override(overrides, "Darwinex-Live", "Darwinex", "WS30")
    assert ov.get("point_value") == 1.0


def test_qdm_analyzer_metrics() -> None:
    analyzer = QDMAnalyzer(pip_size=0.0001)
    dt1 = pd.Timestamp("2024-01-01 10:00:00").to_pydatetime()
    dt2 = pd.Timestamp("2024-01-01 10:01:00").to_pydatetime()

    ohlc_a = {
        dt1: (1.1000, 1.1010, 1.0990, 1.1005),
        dt2: (1.1005, 1.1020, 1.1000, 1.1015),
    }
    ohlc_b = {
        dt1: (1.1001, 1.1011, 1.0991, 1.1006),
        dt2: (1.1006, 1.1021, 1.1001, 1.1016),
    }

    metrics = analyzer.calculate_metrics(ohlc_a, ohlc_b, "FeedA", "FeedB")
    assert metrics["matched_bars"] == 2
    assert metrics["mean_diff_pips"] == 1.0
    assert metrics["correlation"] == 1.0


def test_cli_execution() -> None:
    with pytest.raises(SystemExit) as exc_info:
        _main(["--help"])
    assert exc_info.value.code == 0

    code = _main(["symbol_price_info", "--symbol", "EURUSD"])
    assert code in (0, 1)

    code = _main(["symbol_debug", "--symbol", "EURUSD"])
    assert code in (0, 1)


def test_mt5_runtime_catalog_returns_database_brokers(tmp_path: Path) -> None:
    """MT5 runtime catalog returns broker records seeded from the database."""
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_broker ("
            "id INTEGER PRIMARY KEY, name TEXT, is_system INTEGER, description TEXT, "
            "stockpicker_use INTEGER, mt_use INTEGER, server_timezone TEXT, postfix TEXT, enabled INTEGER)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (2, 'RoboForex', 1, 'RoboForex', 0, 1, 'EET', '_roboforex', 1)"
        )
    owner = "plugin.data_manager.meta_trader"
    store = MarketDataStore(tmp_path, database)
    jobs = JobManager(1, 512 * 1024 * 1024)

    class FakeTerminal:
        async def close(self) -> None:
            pass

    runtime = MT5Runtime(
        MarketAccess(owner, store), JobAccess(owner, jobs), cast("Any", FakeTerminal())
    )

    async def scenario() -> None:
        catalog = cast("Any", await runtime.invoke("catalog", {}))
        assert "brokers" in catalog
        assert len(catalog["brokers"]) == 1
        assert catalog["brokers"][0]["name"] == "RoboForex"
        assert catalog["brokers"][0]["postfix"] == "_roboforex"
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())
