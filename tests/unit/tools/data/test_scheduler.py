"""Unit tests for tools.data.scheduler."""

from __future__ import annotations

import pandas as pd
import pytest

from tools.data.scheduler import (
    clear_scheduled_update_functions,
    clear_scheduled_updater_states,
    register_scheduled_update_function,
    scheduled_data_updater_create,
    scheduled_data_updater_delete,
    scheduled_data_updater_run_cycles,
    scheduled_data_updater_run_once,
    scheduled_data_updater_status,
    scheduled_data_updater_stop,
)


@pytest.fixture(autouse=True)
def clear_state() -> None:
    clear_scheduled_update_functions()
    clear_scheduled_updater_states()


def assert_standard_response(result: dict) -> None:
    assert set(result) >= {"status", "message", "data", "error", "metadata"}
    assert result["status"] in {"success", "error"}
    metadata = result["metadata"]
    for key in (
        "tool_name",
        "tool_version",
        "tool_category",
        "tool_risk_level",
        "request_id",
        "execution_ms",
        "read_only",
        "writes_file",
        "modifies_database",
        "places_trade",
        "requires_network",
    ):
        assert key in metadata


def make_payload(values=None) -> dict:
    values = values or [1.0, 2.0]
    frame = pd.DataFrame(
        {
            "open": values,
            "high": values,
            "low": values,
            "close": values,
            "volume": [100] * len(values),
        },
        index=pd.date_range("2024-01-01", periods=len(values), freq="D"),
    )
    return {
        "symbol": "EURUSD",
        "timeframe": "D1",
        "data": [
            {"timestamp": idx.isoformat(), **row.to_dict()}
            for idx, row in frame.iterrows()
        ],
    }


def test_create_requires_registered_update_function() -> None:
    result = scheduled_data_updater_create(make_payload(), "missing")

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_create_success_returns_state_id_not_callable_or_dataframe() -> None:
    register_scheduled_update_function("noop", lambda data: None)

    result = scheduled_data_updater_create(
        make_payload(), "noop", interval_sec=1, request_id="sched-001"
    )

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["metadata"]["tool_risk_level"] == "medium"
    assert result["metadata"]["read_only"] is False
    assert "state_id" in result["data"]
    assert "update_func" not in result["data"]
    assert "df" not in result["data"]


def test_run_once_adds_new_rows() -> None:
    def updater(data):
        return make_payload([3.0])

    register_scheduled_update_function("append", updater)
    created = scheduled_data_updater_create(
        make_payload([1.0, 2.0]), "append", interval_sec=1
    )
    state_id = created["data"]["state_id"]

    result = scheduled_data_updater_run_once(state_id)

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"]["total_rows"] >= 2


def test_run_cycles_is_bounded() -> None:
    register_scheduled_update_function("noop", lambda data: None)
    created = scheduled_data_updater_create(make_payload(), "noop", interval_sec=1)
    state_id = created["data"]["state_id"]

    result = scheduled_data_updater_run_cycles(state_id, cycles=2)

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"]["cycles_completed"] == 2


def test_run_cycles_rejects_excessive_cycles() -> None:
    register_scheduled_update_function("noop", lambda data: None)
    created = scheduled_data_updater_create(make_payload(), "noop", interval_sec=1)
    state_id = created["data"]["state_id"]

    result = scheduled_data_updater_run_cycles(state_id, cycles=101)

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_status_and_stop_success() -> None:
    register_scheduled_update_function("noop", lambda data: None)
    created = scheduled_data_updater_create(make_payload(), "noop", interval_sec=1)
    state_id = created["data"]["state_id"]

    status = scheduled_data_updater_status(state_id)
    stop = scheduled_data_updater_stop(state_id)

    assert_standard_response(status)
    assert status["status"] == "success"
    assert_standard_response(stop)
    assert stop["status"] == "success"
    assert stop["data"]["running"] is False


def test_delete_removes_state() -> None:
    register_scheduled_update_function("noop", lambda data: None)
    created = scheduled_data_updater_create(make_payload(), "noop", interval_sec=1)
    state_id = created["data"]["state_id"]

    deleted = scheduled_data_updater_delete(state_id)
    status = scheduled_data_updater_status(state_id)

    assert_standard_response(deleted)
    assert deleted["status"] == "success"
    assert status["status"] == "error"


def test_invalid_interval_is_rejected() -> None:
    register_scheduled_update_function("noop", lambda data: None)

    result = scheduled_data_updater_create(make_payload(), "noop", interval_sec=0)

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
