"""Unit tests for ResultStore service and databank persistence."""

import sqlite3
from pathlib import Path

import pytest
from app.core.host.persistence import HostPersistence, PersistenceTransactionError
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import ResultSummary, RunResult
from app.core.trading.results.store import ResultStore


@pytest.fixture
def persistence_gateway(tmp_path: Path) -> HostPersistence:
    """Provide a fresh isolated SQLite persistence instance."""
    db_file = tmp_path / "test_databanks.db"
    conn = sqlite3.connect(db_file)
    conn.close()
    gateway = HostPersistence(db_file)
    gateway.ensure_databanks_schema()
    return gateway


def _make_sample_result(
    result_id: str = "res-001",
    databank_id: str = "db-alpha",
    strategy_id: str = "strat-100",
    strategy_name: str = "MomentumBreakout",
    net_profit: float = 12500.50,
) -> RunResult:
    return RunResult(
        result_id=result_id,
        databank_id=databank_id,
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        metrics={
            "net_profit": net_profit,
            "profit_factor": 1.85,
            "drawdown": 8.2,
            "sharpe_ratio": 2.15,
            "trades_count": 142,
            "win_rate": 0.62,
        },
        trades=(
            {
                "ticket": 1,
                "symbol": "EURUSD",
                "side": "BUY",
                "profit": 150.0,
                "open_time": "2026-01-01T10:00:00Z",
                "close_time": "2026-01-01T14:00:00Z",
            },
        ),
        equity_curve=(
            {"time": "2026-01-01T10:00:00Z", "equity": 10000.0},
            {"time": "2026-01-01T14:00:00Z", "equity": 10150.0},
        ),
        parameters={"fast_period": 14, "slow_period": 50},
        strategy_payload={"rules": ["CrossOver(SMA14, SMA50)"]},
    )


def test_save_and_get_result(persistence_gateway: HostPersistence) -> None:
    """ResultStore persists a RunResult and reloads identical data."""
    store = ResultStore(persistence_gateway)
    original = _make_sample_result()

    saved_id = store.save_result("db-alpha", original)
    assert saved_id == "res-001"

    loaded = store.get_result("res-001")
    assert loaded.result_id == "res-001"
    assert loaded.databank_id == "db-alpha"
    assert loaded.strategy_id == "strat-100"
    assert loaded.strategy_name == "MomentumBreakout"
    assert loaded.metrics["net_profit"] == 12500.50
    assert loaded.metrics["sharpe_ratio"] == 2.15
    assert len(loaded.trades) == 1
    assert loaded.trades[0]["profit"] == 150.0
    assert len(loaded.equity_curve) == 2
    assert loaded.parameters == {"fast_period": 14, "slow_period": 50}
    assert loaded.strategy_payload == {"rules": ["CrossOver(SMA14, SMA50)"]}


def test_list_results_and_pagination(
    persistence_gateway: HostPersistence,
) -> None:
    """ResultStore lists candidate summaries filtered by databank with pagination."""
    store = ResultStore(persistence_gateway)

    for i in range(5):
        res = _make_sample_result(
            result_id=f"res-{i:03d}",
            databank_id="db-target",
            strategy_name=f"Strategy-{i}",
            net_profit=1000.0 * (i + 1),
        )
        store.save_result("db-target", res)

    # Save one to another databank
    other_res = _make_sample_result(
        result_id="res-other",
        databank_id="db-other",
        strategy_name="OtherStrat",
    )
    store.save_result("db-other", other_res)

    # Query db-target
    all_target = store.list_results("db-target", limit=10)
    assert len(all_target) == 5
    assert all(isinstance(r, ResultSummary) for r in all_target)
    assert {r.result_id for r in all_target} == {f"res-{i:03d}" for i in range(5)}

    # Pagination: limit 2, offset 0
    p1 = store.list_results("db-target", limit=2, offset=0)
    assert len(p1) == 2

    # Pagination: limit 2, offset 2
    p2 = store.list_results("db-target", limit=2, offset=2)
    assert len(p2) == 2
    assert p1[0].result_id != p2[0].result_id


def test_update_existing_result(persistence_gateway: HostPersistence) -> None:
    """Saving a result with existing ID updates the stored row."""
    store = ResultStore(persistence_gateway)
    initial = _make_sample_result(net_profit=5000.0)
    store.save_result("db-alpha", initial)

    updated = _make_sample_result(net_profit=9999.0)
    store.save_result("db-alpha", updated)

    loaded = store.get_result("res-001")
    assert loaded.metrics["net_profit"] == 9999.0

    summaries = store.list_results("db-alpha")
    assert len(summaries) == 1
    assert summaries[0].net_profit == 9999.0


def test_delete_result(persistence_gateway: HostPersistence) -> None:
    """Deleting a result removes it from databank; subsequent get raises RESULT_NOT_FOUND."""
    store = ResultStore(persistence_gateway)
    res = _make_sample_result()
    store.save_result("db-alpha", res)

    deleted = store.delete_result("res-001")
    assert deleted is True

    # Confirm get_result raises RESULT_NOT_FOUND
    with pytest.raises(DomainError) as exc_info:
        store.get_result("res-001")
    assert exc_info.value.code == "RESULT_NOT_FOUND"

    # Deleting again returns False
    deleted_again = store.delete_result("res-001")
    assert deleted_again is False


def test_get_missing_result_raises(
    persistence_gateway: HostPersistence,
) -> None:
    """Querying non-existent result raises RESULT_NOT_FOUND."""
    store = ResultStore(persistence_gateway)
    with pytest.raises(DomainError) as exc_info:
        store.get_result("non_existent_id")

    assert exc_info.value.code == "RESULT_NOT_FOUND"
    assert exc_info.value.details == {"result_id": "non_existent_id"}


def test_transactional_rollback(persistence_gateway: HostPersistence) -> None:
    """Failed transaction rolls back results; uncommitted results are not visible."""
    res = _make_sample_result()

    with pytest.raises(PersistenceTransactionError):
        with persistence_gateway.transaction() as tx:
            tx_store = ResultStore(tx)
            tx_store.save_result("db-alpha", res)
            # Force failure in transaction
            tx.delete_record("databank_results", filters={"id": "does_not_exist"})

    root_store = ResultStore(persistence_gateway)
    with pytest.raises(DomainError) as exc_info:
        root_store.get_result("res-001")
    assert exc_info.value.code == "RESULT_NOT_FOUND"
