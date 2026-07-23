"""Unit tests for historical data access orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.data.contracts import MarketDataset
from app.services.data.market_data.pipeline import fetch_market_dataset
from app.services.data.market_data.requests import MarketDataRequest
from app.services.data.persistence.contracts import DatasetSaveRequest
from app.services.data.persistence.dataset_writer import save_dataset
from app.services.data.sources.policy import _reset_policy_registry
from app.services.data.sources.registry import _reset_registry

from tests.data.helpers import make_dataset, register_local_test_source

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)


def _configure_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_historical_access.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.persistence.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _reset_registry()
    _reset_policy_registry()
    _configure_database(monkeypatch, tmp_path)


def test_fetch_market_dataset_reports_actual_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify source reporting and multi-million-bar request acceptance."""
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    register_local_test_source(raw_root, ("AAPL",))

    dataset = make_dataset().model_copy(
        update={
            "symbol": "AAPL",
            "records": (
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "source": "local_csv",
                        "source_symbol": "AAPL",
                        "timestamp": START,
                    }
                ),
            ),
            "start": START,
            "end": START,
            "request_id": (
                "req-9e79c6ea45b572dd655e077ea534a48a4593ad8eacf1dbd3edfe0d4dc6bb2859"
            ),
        }
    )

    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/AAPL.csv"),
        format="csv",
        overwrite=True,
        request_id="req-9e79c6ea45b572dd655e077ea534a48a4593ad8eacf1dbd3edfe0d4dc6bb2859",
    )
    save_dataset(save_req)

    # 1. Successful retrieval
    req = MarketDataRequest(
        source_id="local_csv",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=10,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-12273c6b83cd2187ad2952ac03f30810a02043fe67f88d81fa02ef4053aa64e4",
    )

    res = fetch_market_dataset(req)
    assert isinstance(res, MarketDataset)
    assert res.symbol == "AAPL"
    assert res.records[0].source == "local_csv"

    # 2. OHLCV requests are not capped by an app-wide record-count limit.
    large_req = req.model_copy(update={"limit": 8_000_000})
    large_result = fetch_market_dataset(large_req)
    assert isinstance(large_result, MarketDataset)
    assert large_result.records
