"""Historical terminal conversion, failure, parity and immutable-publication checks."""

import asyncio
import datetime
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import JobAccess, MarketAccess
from app.host.contracts import BrokerTimeProvenance, ClockPolicy
from app.host.jobs import JobManager
from app.persistence.market import (
    MarketDataStore,
    create_isolated_schema,
    migrate_broker_clock_schema,
)
from app.plugin.DataSource.mt5 import (
    EMBEDDED_SYMBOL_CATALOG,
    MT5Definition,
    MT5Runtime,
    QDMAnalyzer,
    _main,
    broker_time_frame,
    classify_terminal_metadata,
    convert_history,
    dataframe_to_canonical_table,
    estimate_terminal_offset,
    get_price_symbol_info,
    load_overrides,
    normalize_terminal_history,
    resample_candles,
    resolve_override,
    ticks_to_m1,
)
from pydantic import JsonValue


@pytest.fixture(autouse=True)
def isolated_native_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never discover or launch an installed terminal from offline unit tests."""
    monkeypatch.setattr("app.plugin.DataSource.mt5.MT5_AVAILABLE", False)
    monkeypatch.setattr("app.plugin.DataSource.mt5.mt5", None)


def provision_test_clock(store: MarketDataStore) -> None:
    """Explicitly provide assessed synthetic UTC inputs in an isolated store."""
    with closing(sqlite3.connect(store.database_path)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.execute("INSERT INTO datamgr_broker VALUES (2,'Test','','UTC',1,1)")
    migrate_broker_clock_schema(store.database_path)
    policy = ClockPolicy.model_validate(
        {
            "revision": 1,
            "effective_from_utc": "2020-01-01T00:00:00Z",
            "effective_to_utc": "2030-01-01T00:00:00Z",
            "standard_offset_minutes": 0,
            "initial_offset_minutes": 0,
            "tick_time_basis": "utc",
            "bar_time_basis": "utc",
            "request_time_basis": "utc",
            "verified": True,
            "evidence_references": ["synthetic-fixture"],
            "assessed_at": "2026-10-02T00:00:00Z",
            "limitations": "Synthetic test only",
        }
    )
    store.replace_broker_clock_policy("2", 0, policy)


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
    provision_test_clock(store)

    class Terminal:
        def __init__(self) -> None:
            self.closed = False
            self.calls: list[str] = []

        async def call(self, operation: Any, arguments: Any) -> Any:
            self.calls.append(operation)
            if operation == "connect":
                return True
            if operation == "tick":
                return {"time_msc": None}
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
            "Any",
            await runtime.invoke(
                "add", {"symbol": "EURUSD", "timeframe": "D1", "broker": "2"}
            ),
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
    provision_test_clock(store)

    call_count = 0

    class EmptyChunkTerminal:
        def __init__(self) -> None:
            self.closed = False

        async def call(self, operation: Any, arguments: Any) -> Any:
            nonlocal call_count
            if operation == "connect":
                return True
            if operation == "tick":
                return {"time_msc": None}
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
            await runtime.invoke(
                "add", {"symbol": "EURUSD", "timeframe": "TICK", "broker": "2"}
            ),
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


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"trade_calc_mode": 2, "path": "Forex\\GOLD"}, ("CFD", "calculation_mode")),
        ({"trade_calc_mode": 5}, ("Forex", "calculation_mode")),
        ({"trade_calc_mode": 33}, ("Futures", "calculation_mode")),
        ({"trade_calc_mode": 32}, ("Stock", "calculation_mode")),
        ({"trade_calc_mode": 34}, ("Unknown", "unknown")),
        ({"path": "Markets\\Futures\\ES"}, ("Futures", "folder")),
        ({"path": "CFDs\\Forex\\EURUSD"}, ("Unknown", "unknown")),
        ({"path": "Markets\\Commodities\\Gold\\XAUUSD"}, ("Unknown", "unknown")),
    ],
)
def test_terminal_type_classification(
    info: dict[str, Any], expected: tuple[str, str]
) -> None:
    assert classify_terminal_metadata(info) == expected


def seasonal_test_policy() -> ClockPolicy:
    return ClockPolicy.model_validate(
        {
            "revision": 1,
            "effective_from_utc": "2026-01-01T00:00:00Z",
            "effective_to_utc": "2027-01-01T00:00:00Z",
            "standard_offset_minutes": 120,
            "initial_offset_minutes": 120,
            "dst_increment_minutes": 60,
            "dst_rule": "us",
            "tick_time_basis": "server_wall_clock",
            "bar_time_basis": "server_wall_clock",
            "request_time_basis": "utc",
            "verified": True,
            "evidence_references": ["synthetic-transition-test"],
            "assessed_at": "2026-10-02T00:00:00Z",
            "limitations": "Synthetic schedule; not an assertion about live broker transitions",
            "transitions": [
                {
                    "transition_utc": "2026-03-08T07:00:00Z",
                    "offset_before_minutes": 120,
                    "offset_after_minutes": 180,
                },
                {
                    "transition_utc": "2026-11-01T06:00:00Z",
                    "offset_before_minutes": 180,
                    "offset_after_minutes": 120,
                },
            ],
        }
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-01-02T12:00:00Z", "2026-01-02T10:00:00Z"),
        ("2026-07-02T12:00:00Z", "2026-07-02T09:00:00Z"),
        ("2026-03-15T12:00:00Z", "2026-03-15T09:00:00Z"),
        ("2026-10-28T12:00:00Z", "2026-10-28T09:00:00Z"),
        ("2026-03-08T10:00:00Z", "2026-03-08T07:00:00Z"),
    ],
)
def test_historical_event_offset_uses_pinned_schedule(raw: str, expected: str) -> None:
    result = normalize_terminal_history(
        pd.DataFrame({"DateTime": [pd.Timestamp(raw)]}), seasonal_test_policy(), "m1"
    )
    assert result["DateTime"].iloc[0] == pd.Timestamp(expected)
    assert result["RawTimeMs"].iloc[0] == int(pd.Timestamp(raw).timestamp() * 1000)


@pytest.mark.parametrize(
    "raw", ["2026-03-08T09:30:00Z", "2026-11-01T08:30:00Z", "2025-07-01T12:00:00Z"]
)
def test_historical_clock_refuses_gap_fold_or_missing_coverage(raw: str) -> None:
    with pytest.raises(ValueError, match="Ambiguous"):
        normalize_terminal_history(
            pd.DataFrame({"DateTime": [pd.Timestamp(raw)]}),
            seasonal_test_policy(),
            "ticks",
        )


def test_historical_clock_utc_is_not_shifted_and_unknown_is_rejected() -> None:
    policy = seasonal_test_policy()
    frame = pd.DataFrame({"DateTime": [pd.Timestamp("2026-07-01T12:00:00Z")]})
    assert (
        normalize_terminal_history(
            frame, policy.model_copy(update={"bar_time_basis": "utc"}), "m1"
        )["DateTime"].iloc[0]
        == frame["DateTime"].iloc[0]
    )
    with pytest.raises(ValueError, match="unverified"):
        normalize_terminal_history(
            frame, policy.model_copy(update={"verified": False}), "m1"
        )


@pytest.mark.parametrize("offset", [-5, 0, 3])
def test_clock_estimate_advancing_quotes(offset: int) -> None:
    samples = [
        {
            "time_msc": (100000 + i * 2 + offset * 3600) * 1000,
            "utc_before": 100000 + i * 2,
            "utc_after": 100000 + i * 2 + 0.01,
            "monotonic_before": 200 + i * 2,
            "monotonic_after": 200 + i * 2 + 0.01,
        }
        for i in range(3)
    ]
    assert estimate_terminal_offset(samples) == offset
    static = [{**row, "time_msc": samples[0]["time_msc"]} for row in samples]
    assert estimate_terminal_offset(static) is None
    delayed = [{**row, "time_msc": row["time_msc"] - 90000} for row in samples]
    assert estimate_terminal_offset(delayed) is None
    jumped = [*samples[:2], {**samples[2], "utc_after": samples[2]["utc_after"] + 3600}]
    assert estimate_terminal_offset(jumped) is None


def prepare_download_policy(
    store: MarketDataStore, policy_state: str
) -> dict[str, Any] | None:
    """Prepare optional synthetic policies; never touch the operational database."""
    if policy_state != "absent":
        provision_test_clock(store)
        if policy_state != "verified":
            with (
                closing(sqlite3.connect(store.database_path)) as connection,
                connection,
            ):
                value = store.broker_clock_policy("2")
                document = value["revisions"][0]
                if policy_state == "unverified":
                    document["verified"] = False
                else:
                    document["effective_from_utc"] = "2025-01-01T00:00:00Z"
                connection.execute(
                    "UPDATE datamgr_broker SET clock_policy_json=? WHERE id=2",
                    (json.dumps({"revisions": [document]}),),
                )
        return store.broker_clock_policy("2")
    return None


@pytest.mark.parametrize(
    "policy_state", ["absent", "verified", "unverified", "outside_range"]
)
def test_download_preserves_broker_time_without_policy_admission(
    tmp_path: Path, policy_state: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    before_policy = prepare_download_policy(store, policy_state)
    source = MarketAccess("plugin.data_manager.meta_trader", store)
    parameters = MT5Definition(symbol="TEST", broker="2")
    legacy = source.register_source(
        source="MT5",
        symbol="TEST",
        underlying="TEST",
        instrument="TEST",
        timeframe="M1",
        broker="2",
        options={"parameters": parameters.model_dump(mode="json")},
    )

    def no_policy_read(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Policy must not gate original-time downloads")

    original_policy_read = store.broker_clock_policy
    monkeypatch.setattr(store, "broker_clock_policy", no_policy_read)

    class Terminal:
        async def call(self, operation: Any, arguments: Any) -> Any:
            assert operation == "history", "No automatic tick/clock probe"
            return {
                "columns": ["time", "open", "high", "low", "close", "tick_volume"],
                "rows": [[1704078000, 1, 2, 1, 1.5, 10]],
            }

        async def close(self) -> None:
            pass

    async def scenario() -> None:
        jobs = JobManager(1, 512 * 1024 * 1024)
        runtime = MT5Runtime(
            source, JobAccess(source.owner, jobs), cast("Any", Terminal())
        )
        runtime.connected = True
        payload: JsonValue = {
            "dataset_id": legacy,
            "date_from": "2024-01-01",
            "date_to": "2024-01-01",
        }
        result = cast("Any", await runtime.invoke("download.start", payload))
        await asyncio.wait_for(jobs.tasks[result["job_id"]], timeout=3)
        assert jobs.records[result["job_id"]].state == "succeeded"
        raw_id = result["dataset_id"]
        assert raw_id != legacy
        assert source.source_definition(legacy)["timezone"] == "UTC"
        assert source.source_definition(raw_id)["timezone"] == "Exchange/Broker"
        partition = store.source_partitions(raw_id)[0]
        table = store.read_source_partition(partition)
        assert table.schema.field("DateTime").type.tz is None
        assert table.column("DateTime").to_pylist() == [
            datetime.datetime(2024, 1, 1, 3, tzinfo=datetime.UTC).replace(tzinfo=None)
        ]
        provenance = store.source_clock_provenance(partition)
        assert isinstance(provenance, BrokerTimeProvenance)
        assert provenance.raw_timestamps_ms == (1704078000000,)
        assert "broker_time" in partition["relative_path"]
        repeat = cast("Any", await runtime.invoke("download.start", payload))
        await asyncio.wait_for(jobs.tasks[repeat["job_id"]], timeout=3)
        assert repeat["dataset_id"] == raw_id
        assert store.source_partitions(raw_id)[0]["revision"] == partition["revision"]
        if policy_state != "absent":
            assert original_policy_read("2") == before_policy
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())


def test_broker_ticks_retain_distinct_records_at_repeated_wall_time() -> None:
    document = {
        "columns": ["time_msc", "bid", "ask", "volume", "flags"],
        "rows": [[1704078000000, 1.2, 1.3, 1, 2], [1704078000000, 1.2, 1.3, 1, 4]],
    }
    frame = broker_time_frame(document, "TICK")
    assert frame["DateTime"].dt.tz is None
    assert frame["DateTime"].nunique() == 1
    assert frame["SourceRecord"].nunique() == 2
    with pytest.raises(ValueError, match="native timestamp"):
        broker_time_frame({**document, "rows": [[0, 1.2, 1.3, 1, 2]]}, "TICK")


def test_metadata_reads_saved_terminal_info_without_connecting(tmp_path: Path) -> None:
    database = tmp_path / "offline-info.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    source = MarketAccess("plugin.data_manager.meta_trader", store)
    dataset_id = source.register_source(
        source="MT5",
        symbol="GOLD",
        underlying="GOLD",
        instrument="GOLD",
        timeframe="M1",
        broker="2",
        options={"metadata": {"trade_calc_mode": 2, "path": "Forex\\GOLD"}},
    )
    foreign = MarketAccess("plugin.other", store).register_source(
        source="Other",
        symbol="OTHER",
        underlying="OTHER",
        instrument="OTHER",
        timeframe="M1",
    )

    class OfflineTerminal:
        async def call(self, operation: Any, arguments: Any) -> Any:
            raise AssertionError("No terminal read belongs to metadata inspection")

        async def close(self) -> None:
            pass

    async def scenario() -> None:
        jobs = JobManager(1, 512 * 1024 * 1024)
        runtime = MT5Runtime(
            source,
            JobAccess("plugin.data_manager.meta_trader", jobs),
            cast("Any", OfflineTerminal()),
        )
        result = cast(
            "Any",
            await runtime.invoke("dataset_metadata", {"dataset_ids": [dataset_id]}),
        )
        assert result["datasets"][0]["data_type"] == "CFD"
        assert result["datasets"][0]["bar_type"] == "start"
        assert result["datasets"][0]["clock_status"] == "unknown"
        for age, expected in [(1, "estimated"), (301, "expired"), (-60, "expired")]:
            runtime.clock_estimates[dataset_id] = (
                3,
                datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=age),
            )
            inspected = cast(
                "Any",
                await runtime.invoke("dataset_metadata", {"dataset_ids": [dataset_id]}),
            )["datasets"][0]
            assert inspected["clock_status"] == expected
            assert inspected["broker_utc_offset"] == (
                3 if expected == "estimated" else None
            )
        with pytest.raises(ValueError):
            await runtime.invoke("dataset_metadata", {"dataset_ids": [foreign]})
        await runtime.close()

    asyncio.run(scenario())


def test_mt5_canonical_operations_parity_and_storage(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    owner = "plugin.data_manager.meta_trader"
    source = MarketAccess(owner, store)

    class FakeTerminal:
        async def call(self, operation: Any, arguments: Any) -> Any:
            if operation == "connect":
                return True
            if operation == "history":
                stamp = int(pd.Timestamp(arguments["start"]).timestamp())
                return {
                    "columns": ["time", "open", "high", "low", "close", "tick_volume"],
                    "rows": [[stamp, 1.0950, 1.0960, 1.0940, 1.0955, 12]],
                }
            raise ValueError(operation)

        async def close(self) -> None:
            pass

    async def scenario() -> None:
        jobs = JobManager(1, 512 * 1024 * 1024)
        terminal = FakeTerminal()
        runtime = MT5Runtime(source, JobAccess(owner, jobs), cast("Any", terminal))
        await runtime.invoke("connect", {})

        added = cast(
            "Any",
            await runtime.invoke(
                "definitions.add",
                {"symbols": ["EURUSD"], "kind": "m1", "broker": "-1"},
            ),
        )
        assert added["added"] == 1
        target_id = added["ids"][0]

        datasets = cast("Any", await runtime.invoke("catalog", {}))["datasets"]
        target = next(
            d for d in datasets if d["symbol"].upper() == "EURUSD" and d["kind"] == "m1"
        )
        assert target["id"] == target_id
        assert "options" in target
        assert "metadata" in target["options"]
        assert "date_from" in target
        assert "date_to" in target

        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": target_id,
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

        expected_file = tmp_path / "market" / "mt5" / "m1" / "eurusd" / "2024.parquet"
        assert expected_file.exists()

        files = cast(
            "Any",
            await runtime.invoke("files.list", {"symbol": "eurusd", "kind": "m1"}),
        )
        assert len(files) == 1
        assert files[0]["relative_path"] == "market/mt5/m1/eurusd/2024.parquet"
        assert files[0]["source"] == "mt5"

        rows = cast(
            "Any",
            await runtime.invoke(
                "rows.read",
                {"dataset_id": target_id, "start_ms": 0, "end_ms": 2000000000000},
            ),
        )
        assert len(rows) == 1
        assert rows[0]["Close"] == 1.0955

        cleared = cast("Any", await runtime.invoke("clear", {"symbol": "eurusd"}))
        assert cleared["cleared"] is True
        assert not expected_file.exists()

        deleted = cast("Any", await runtime.invoke("delete", {"symbol": "eurusd"}))
        assert deleted["deleted"] is True
        assert len(source.list_datasets()) == 0

        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())


def test_mt5_no_direct_sqlite3_in_plugin() -> None:
    plugin_path = Path("app/plugin/DataSource/mt5.py")
    source_code = plugin_path.read_text(encoding="utf-8")
    assert "sqlite3.connect" not in source_code
    assert "resolve_unified_db_path" not in source_code
