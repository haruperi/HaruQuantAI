import app.agentic.tools.data
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agentic.tools.data.tools import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    clear_data_cache,
    create_data_update_job,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    get_data_availability,
    get_data_update_job_status,
    get_feed_status,
    get_historical_volume,
    get_market_data,
    get_market_hours,
    get_spread_data,
    get_symbol_metadata,
    get_tick_data,
    get_trading_sessions,
    label_market_data,
    list_symbols,
    load_local_dataset,
    resample_ohlcv,
    run_data_update_job_once,
    save_market_data,
    start_data_update_job,
    stop_data_update_job,
)


@pytest.fixture
def mock_standard_response() -> dict[str, Any]:
    return {"status": "success", "data": "mock_data"}


@patch("app.agentic.tools.data.tools._get_data")
def test_get_market_data_success(mock_get_data: MagicMock) -> None:
    mock_get_data.return_value = [{"time": "2026-01-01T00:00:00Z", "close": 1.0}]
    result = get_market_data(
        symbol="EURUSD",
        timeframe="H1",
        start_time="2026-01-01",
        end_time="2026-01-02",
        source="csv",
    )
    assert result["status"] == "success"
    assert len(result["data"]) == 1
    mock_get_data.assert_called_once_with(
        symbol="EURUSD",
        timeframe="H1",
        start_time="2026-01-01",
        end_time="2026-01-02",
        data_kind="ohlcv",
        source="csv",
        limit=None,
        stale_data_behavior="refresh_and_return",
        workflow_context="research",
        fallback_sources=None,
        request_id=None,
    )


@patch("app.agentic.tools.data.tools._get_data")
def test_get_market_data_error(mock_get_data: MagicMock) -> None:
    mock_get_data.side_effect = ValueError("Invalid inputs")
    result = get_market_data(
        symbol="EURUSD", timeframe="INVALID", start_time="2026-01-01", end_time="2026-01-02"
    )
    assert result["status"] == "error"
    assert "Invalid inputs" in str(result)


@patch("app.agentic.tools.data.tools._get_data")
def test_get_tick_data(mock_get_data: MagicMock) -> None:
    mock_get_data.return_value = [{"time": "2026-01-01T00:00:00Z", "price": 1.0}]
    result = get_tick_data("EURUSD", "2026-01-01", "2026-01-02", source="csv")
    assert result["status"] == "success"
    mock_get_data.assert_called_once_with(
        symbol="EURUSD",
        start_time="2026-01-01",
        end_time="2026-01-02",
        data_kind="ticks",
        source="csv",
        limit=None,
        stale_data_behavior="refresh_and_return",
        workflow_context="research",
        fallback_sources=None,
        request_id=None,
    )


@patch("app.agentic.tools.data.tools._get_data")
def test_get_spread_data(mock_get_data: MagicMock) -> None:
    mock_get_data.return_value = [{"time": "2026-01-01T00:00:00Z", "spread": 0.5}]
    result = get_spread_data("EURUSD", "2026-01-01", "2026-01-02", source="csv")
    assert result["status"] == "success"
    mock_get_data.assert_called_once_with(
        symbol="EURUSD",
        start_time="2026-01-01",
        end_time="2026-01-02",
        data_kind="spreads",
        source="csv",
        limit=None,
        stale_data_behavior="refresh_and_return",
        workflow_context="research",
        fallback_sources=None,
        request_id=None,
    )


@patch("app.agentic.tools.data.tools._get_data")
def test_get_historical_volume(mock_get_data: MagicMock) -> None:
    mock_get_data.return_value = [{"time": "2026-01-01T00:00:00Z", "volume": 100}]
    result = get_historical_volume(
        "EURUSD", "H1", "2026-01-01", "2026-01-02", source="csv"
    )
    assert result["status"] == "success"
    mock_get_data.assert_called_once_with(
        symbol="EURUSD",
        timeframe="H1",
        start_time="2026-01-01",
        end_time="2026-01-02",
        data_kind="volume",
        source="csv",
        limit=None,
        stale_data_behavior="refresh_and_return",
        workflow_context="research",
        fallback_sources=None,
        request_id=None,
    )


@patch("app.agentic.tools.data.tools._resample_ohlcv")
def test_resample_ohlcv(mock_resample: MagicMock) -> None:
    mock_resample.return_value = [{"time": "2026-01-01T00:00:00Z", "close": 1.0}]
    result = resample_ohlcv([{"time": "2026-01-01", "close": 1}], "H1", "H4")
    assert result["status"] == "success"
    mock_resample.assert_called_once()


@patch("app.agentic.tools.data.tools._align_multitimeframe_data")
def test_align_multitimeframe_data(mock_align: MagicMock) -> None:
    mock_align.return_value = {"H1": [], "H4": []}
    result = align_multitimeframe_data(
        {"H1": [{"timestamp": "2026-01-01"}]}, "H1"
    )
    assert result["status"] == "success"
    mock_align.assert_called_once()


@patch("app.agentic.tools.data.tools._aggregate_ticks_to_bars")
def test_aggregate_ticks_to_bars(mock_agg: MagicMock) -> None:
    mock_agg.return_value = [{"close": 1.0}]
    result = aggregate_ticks_to_bars([{"price": 1}], "M1")
    assert result["status"] == "success"
    mock_agg.assert_called_once()


@patch("app.agentic.tools.data.tools._generate_synthetic_ticks")
def test_generate_synthetic_ticks(mock_gen: MagicMock) -> None:
    mock_gen.return_value = [{"price": 1.0}]
    result = generate_synthetic_ticks("EURUSD", "2026-01-01")
    assert result["status"] == "success"
    mock_gen.assert_called_once()


@patch("app.agentic.tools.data.tools._generate_synthetic_bars")
def test_generate_synthetic_bars(mock_gen: MagicMock) -> None:
    mock_gen.return_value = [{"close": 1.0}]
    result = generate_synthetic_bars("EURUSD", "M1", "2026-01-01")
    assert result["status"] == "success"
    mock_gen.assert_called_once()


@patch("app.agentic.tools.data.tools._list_symbols")
def test_list_symbols(mock_list: MagicMock) -> None:
    mock_list.return_value = ["EURUSD", "GBPUSD"]
    result = list_symbols(source="csv")
    assert result["status"] == "success"
    assert len(result["data"]) == 2
    mock_list.assert_called_once()


@patch("app.agentic.tools.data.tools._get_data_availability")
def test_get_data_availability(mock_avail: MagicMock) -> None:
    mock_avail.return_value = {"EURUSD": "Available"}
    result = get_data_availability("EURUSD", "H1", source="csv")
    assert result["status"] == "success"
    mock_avail.assert_called_once()


@patch("app.agentic.tools.data.tools._get_symbol_metadata")
def test_get_symbol_metadata(mock_meta: MagicMock) -> None:
    mock_meta.return_value = {"point": 0.0001}
    result = get_symbol_metadata("EURUSD", source="csv")
    assert result["status"] == "success"
    mock_meta.assert_called_once()


@patch("app.agentic.tools.data.tools._get_market_hours")
def test_get_market_hours(mock_hours: MagicMock) -> None:
    mock_hours.return_value = {"open": "00:00", "close": "23:59"}
    result = get_market_hours("EURUSD")
    assert result["status"] == "success"
    mock_hours.assert_called_once()


@patch("app.agentic.tools.data.tools._get_trading_sessions")
def test_get_trading_sessions(mock_sess: MagicMock) -> None:
    mock_sess.return_value = ["london", "ny"]
    result = get_trading_sessions("2026-01-01", "2026-01-02")
    assert result["status"] == "success"
    mock_sess.assert_called_once()


@patch("app.agentic.tools.data.tools._get_feed_status")
def test_get_feed_status(mock_feed: MagicMock) -> None:
    mock_feed.return_value = {"status": "active"}
    result = get_feed_status("feed1")
    assert result["status"] == "success"
    mock_feed.assert_called_once()


@patch("app.agentic.tools.data.tools._create_data_update_job")
def test_create_data_update_job(mock_create: MagicMock) -> None:
    mock_create.return_value = {"name": "job1", "job_id": "job_id_1"}
    result = create_data_update_job(
        "job1", "csv", ["EURUSD"], ["H1"], "ohlcv", "parquet", "/data"
    )
    assert result["status"] == "success"
    mock_create.assert_called_once()


@patch("app.agentic.tools.data.tools._start_data_update_job")
def test_start_data_update_job(mock_start: MagicMock) -> None:
    mock_start.return_value = {"job_id": "job1"}
    result = start_data_update_job("job1")
    assert result["status"] == "success"
    mock_start.assert_called_once()


@patch("app.agentic.tools.data.tools._stop_data_update_job")
def test_stop_data_update_job(mock_stop: MagicMock) -> None:
    mock_stop.return_value = {"job_id": "job1"}
    result = stop_data_update_job("job1")
    assert result["status"] == "success"
    mock_stop.assert_called_once()


@patch("app.agentic.tools.data.tools._run_data_update_job_once")
def test_run_data_update_job_once(mock_run: MagicMock) -> None:
    mock_run.return_value = {"name": "job1"}
    result = run_data_update_job_once("job1")
    assert result["status"] == "success"
    mock_run.assert_called_once()


@patch("app.agentic.tools.data.tools._get_data_update_job_status")
def test_get_data_update_job_status(mock_status: MagicMock) -> None:
    mock_status.return_value = {"status": "running"}
    result = get_data_update_job_status("job1")
    assert result["status"] == "success"
    mock_status.assert_called_once()


@patch("app.agentic.tools.data.tools._clear_data_cache")
def test_clear_data_cache(mock_clear: MagicMock) -> None:
    mock_clear.return_value = {"cleared_count": 10}
    result = clear_data_cache(namespace="data")
    assert result["status"] == "success"
    mock_clear.assert_called_once()


@patch("app.agentic.tools.data.tools._label_market_data")
def test_label_market_data(mock_label: MagicMock) -> None:
    mock_label.return_value = [{"label": 1}]
    result = label_market_data([{"close": 1}], "fixed_horizon")
    assert result["status"] == "success"
    mock_label.assert_called_once()


@patch("app.agentic.tools.data.tools._save_market_data")
def test_save_market_data(mock_save: MagicMock) -> None:
    mock_save.return_value = {"record_count": 1}
    result = save_market_data([{"close": 1}], "/data.csv")
    assert result["status"] == "success"
    mock_save.assert_called_once()


@patch("app.agentic.tools.data.tools._load_local_dataset")
def test_load_local_dataset(mock_load: MagicMock) -> None:
    mock_load.return_value = [{"close": 1}]
    result = load_local_dataset("data.csv")
    assert result["status"] == "success"
    mock_load.assert_called_once()
