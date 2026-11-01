"""Integration tests connecting BacktestRunner execution results to ResultStore and Databank jobs."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.host.persistence import HostPersistence
from app.core.jobs import (
    AddToDatabankJob,
    JobContext,
    MoveToDatabankJob,
    clear_databank_locks,
)
from app.core.lib.errors import DomainError
from app.core.trading.backtest.contracts import (
    BacktestSettings,
    RunSpec,
)
from app.core.trading.backtest.runner import BacktestRunner
from app.core.trading.results.adapters import from_backtest_result
from app.core.trading.results.contracts import RunResult as StoredRunResult
from app.core.trading.results.store import ResultStore
from app.core.trading.strategy.contracts import (
    ActionKind,
    ConditionDefinition,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    StrategyDocument,
)


@pytest.fixture(autouse=True)
def _reset_locks() -> Generator[None]:
    clear_databank_locks()
    yield
    clear_databank_locks()


@pytest.fixture
def persistence_gateway(tmp_path: Path) -> HostPersistence:
    db_file = tmp_path / "test_runner_integration.db"
    conn = sqlite3.connect(db_file)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS host_jobs (
            job_id TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'default',
            kind TEXT NOT NULL DEFAULT 'compute', status TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0, accepted INTEGER DEFAULT 0,
            rejected INTEGER DEFAULT 0, message TEXT NOT NULL DEFAULT '',
            attempt_id INTEGER DEFAULT 1, submitted_at_utc TEXT NOT NULL DEFAULT '',
            started_at_utc TEXT, finished_at_utc TEXT, error_message TEXT
        );
        CREATE TABLE IF NOT EXISTS host_job_events (
            event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_id TEXT,
            from_state TEXT, to_state TEXT NOT NULL, details_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        );
    """)
    conn.close()
    gateway = HostPersistence(db_file)
    gateway.ensure_databanks_schema()
    return gateway


def _bar(time: int, o: float, h: float, low: float, c: float) -> MarketBar:
    return MarketBar(
        time=time, open=o, high=h, low=low, close=c, tick_volume=100, spread=0
    )


def test_runner_direct_result_incompatible_with_store(
    persistence_gateway: HostPersistence,
) -> None:
    """Directly passing backtest.RunResult into ResultStore.save_result fails because attributes differ."""
    store = ResultStore(persistence_gateway)
    runner = BacktestRunner()
    strategy = StrategyDocument(strategy_id="test-strat", rules=())
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=[],
        settings=BacktestSettings(),
    )
    backtest_result = runner.run(spec)

    with pytest.raises(AttributeError):
        store.save_result("db-test", backtest_result)  # type: ignore[arg-type]


def test_runner_conversion_and_persistence_roundtrip(
    persistence_gateway: HostPersistence,
) -> None:
    """Real BacktestRunner output is converted, saved to ResultStore, and reloaded accurately."""
    store = ResultStore(persistence_gateway)
    runner = BacktestRunner()

    rule_entry = RuleDefinition(
        rule_id="entry_long",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.1010),),
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, volume=1.0),),
    )
    rule_exit = RuleDefinition(
        rule_id="exit_long",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.1050),),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    strategy = StrategyDocument(
        strategy_id="strat-integrated-01",
        rules=(rule_entry, rule_exit),
    )

    bars = [
        _bar(1000, 1.0990, 1.1005, 1.0985, 1.1000),
        _bar(1060, 1.1000, 1.1025, 1.0995, 1.1020),
        _bar(1120, 1.1020, 1.1040, 1.1010, 1.1030),
        _bar(1180, 1.1030, 1.1065, 1.1025, 1.1060),
        _bar(1240, 1.1005, 1.1010, 1.0995, 1.1000),
    ]
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=bars,
        settings=BacktestSettings(initial_capital=50000.0, commission_per_order=2.0),
    )

    raw_result = runner.run(spec)
    assert len(raw_result.trades) == 1
    assert len(raw_result.mae_mfe) == 1

    stored_result = from_backtest_result(
        raw_result,
        result_id="res-integrated-001",
        databank_id="db-verified",
        strategy_name="TrendLong",
        parameters={"fast_period": 10},
        strategy_payload={"rules": ["TrendFollow"]},
    )

    assert isinstance(stored_result, StoredRunResult)
    assert stored_result.result_id == "res-integrated-001"
    assert stored_result.databank_id == "db-verified"
    assert stored_result.strategy_id == "strat-integrated-01"
    assert stored_result.strategy_name == "TrendLong"
    assert len(stored_result.trades) == 1
    assert len(stored_result.mae_mfe) == 1
    assert stored_result.parameters == {"fast_period": 10}

    saved_id = store.save_result("db-verified", stored_result)
    assert saved_id == "res-integrated-001"

    reloaded = store.get_result("res-integrated-001")
    assert reloaded.result_id == "res-integrated-001"
    assert reloaded.databank_id == "db-verified"
    assert len(reloaded.trades) == 1
    assert len(reloaded.mae_mfe) == 1
    assert reloaded.mae_mfe[0]["ticket"] == raw_result.mae_mfe[0].ticket
    assert reloaded.mae_mfe[0]["mae_price"] == pytest.approx(
        raw_result.mae_mfe[0].mae_price
    )
    assert reloaded.mae_mfe[0]["mfe_price"] == pytest.approx(
        raw_result.mae_mfe[0].mfe_price
    )


def test_adapted_result_in_databank_jobs(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    """Adapted StoredRunResult works seamlessly through AddToDatabankJob and MoveToDatabankJob."""
    store = ResultStore(persistence_gateway)
    runner = BacktestRunner()
    strategy = StrategyDocument(strategy_id="strat-job-01", rules=())
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=[],
        settings=BacktestSettings(),
    )
    raw_result = runner.run(spec)
    stored_result = from_backtest_result(
        raw_result,
        result_id="res-job-001",
        databank_id="db-source",
        strategy_name="JobStrategy",
    )

    add_job = AddToDatabankJob("db-source", [stored_result], store=store)
    ctx_add = JobContext("job-add-1", tmp_path / "scratch-add")
    count_added = add_job(ctx_add)
    assert count_added == 1

    # Verify presence in db-source
    res_in_source = store.get_result("res-job-001")
    assert res_in_source.databank_id == "db-source"

    # Move to db-dest
    move_job = MoveToDatabankJob("db-source", "db-dest", ["res-job-001"], store=store)
    ctx_move = JobContext("job-move-1", tmp_path / "scratch-move")
    count_moved = move_job(ctx_move)
    assert count_moved == 1

    res_in_dest = store.get_result("res-job-001")
    assert res_in_dest.databank_id == "db-dest"


def test_conversion_rejects_non_finite_metrics() -> None:
    """Conversion fails closed when metrics contain NaN or Inf values."""
    runner = BacktestRunner()
    strategy = StrategyDocument(strategy_id="strat-nan", rules=())
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=[],
        settings=BacktestSettings(),
    )
    raw_result = runner.run(spec)
    # Inject NaN into metrics
    raw_result.metrics["sharpe_ratio"] = float("nan")

    with pytest.raises(DomainError) as exc_info:
        from_backtest_result(
            raw_result,
            result_id="res-nan-01",
            databank_id="db-test",
            strategy_name="NaNStrategy",
        )
    assert exc_info.value.code == "INVALID_RESULT_PAYLOAD"


def test_conversion_rejects_empty_identifiers() -> None:
    """Conversion fails closed when result_id, databank_id, or strategy_name is blank."""
    runner = BacktestRunner()
    strategy = StrategyDocument(strategy_id="strat-blank", rules=())
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=[],
        settings=BacktestSettings(),
    )
    raw_result = runner.run(spec)

    with pytest.raises(DomainError) as exc:
        from_backtest_result(
            raw_result,
            result_id="   ",
            databank_id="db-test",
            strategy_name="ValidName",
        )
    assert exc.value.code == "INVALID_RESULT_PAYLOAD"

    with pytest.raises(DomainError) as exc:
        from_backtest_result(
            raw_result,
            result_id="res-valid",
            databank_id="",
            strategy_name="ValidName",
        )
    assert exc.value.code == "INVALID_RESULT_PAYLOAD"

    with pytest.raises(DomainError) as exc:
        from_backtest_result(
            raw_result,
            result_id="res-valid",
            databank_id="db-test",
            strategy_name="",
        )
    assert exc.value.code == "INVALID_RESULT_PAYLOAD"
