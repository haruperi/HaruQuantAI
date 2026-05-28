"""Unit tests for tools.data.dukascopy."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import pytest
import requests

from tools.data import dukascopy as dukascopy_module
from tools.data import (
    dukascopy_data_list_symbols,
    dukascopy_data_load,
    dukascopy_data_resolve_instrument,
)
from tools.data.dukascopy import DUKASCOPY_MAX_LIMIT, _fetch_jsonp
from tools.utils.normalization import evaluate_freshness, format_timestamp_z, to_utc
from tools.utils.validators import prepare_ohlcv_data


class FakeResponse:
    """Minimal requests.Response test double."""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _standard_schema(result: dict[str, Any]) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["status"] in {"success", "error"}
    assert isinstance(result["message"], str)
    assert isinstance(result["metadata"], dict)
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
    assert metadata["tool_category"] == "data"
    assert metadata["tool_risk_level"] == "low"
    assert metadata["read_only"] is True
    assert metadata["writes_file"] is False
    assert metadata["modifies_database"] is False
    assert metadata["places_trade"] is False
    assert metadata["requires_network"] is True


def _fake_dukascopy_get(url: str, **kwargs: Any) -> FakeResponse:
    jsonp = kwargs["params"]["jsonp"]
    rows = [
        [1704067200000, 1.1000, 1.1010, 1.0990, 1.1005, 100],
        [1704067260000, 1.1005, 1.1020, 1.1000, 1.1015, 120],
    ]
    return FakeResponse(f"{jsonp}({json.dumps(rows)});")


def _fake_empty_get(url: str, **kwargs: Any) -> FakeResponse:
    jsonp = kwargs["params"]["jsonp"]
    return FakeResponse(f"{jsonp}([]);")


def test_resolve_instrument_success() -> None:
    result = dukascopy_data_resolve_instrument("EURUSD", request_id="req-1")

    _standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["instrument"] == "EUR/USD"
    assert result["metadata"]["request_id"] == "req-1"


def test_resolve_instrument_invalid_symbol() -> None:
    result = dukascopy_data_resolve_instrument("", request_id="req-2")

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_list_symbols_success() -> None:
    result = dukascopy_data_list_symbols(pattern="EUR*", request_id="req-3")

    _standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["count"] >= 1
    assert any("EUR" in symbol for symbol in result["data"]["symbols"])


def test_list_symbols_invalid_pattern() -> None:
    result = dukascopy_data_list_symbols(pattern=123, request_id="req-4")  # type: ignore[arg-type]

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_fetch_jsonp_rejects_malformed_response() -> None:
    def bad_get(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse("not-jsonp")

    with pytest.raises(ValueError, match="JSONP"):
        _fetch_jsonp(
            instrument="EUR/USD",
            interval="1MIN",
            offer_side="B",
            last_update=0,
            limit=1,
            timeout=1,
            request_get=bad_get,  # type: ignore[arg-type]
        )


def test_load_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tools.data.dukascopy.requests.get", _fake_dukascopy_get)

    result = dukascopy_data_load(
        symbol="EURUSD",
        timeframe="M1",
        start_date="2024-01-01",
        end_date="2024-01-02",
        count=2,
        cache=False,
        request_id="req-5",
    )

    _standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["source"] == "dukascopy"
    assert result["data"]["symbol"] == "EURUSD"
    assert result["data"]["instrument"] == "EUR/USD"
    assert result["data"]["row_count"] == 2
    assert len(result["data"]["bars"]) == 2


def test_load_invalid_timeframe() -> None:
    result = dukascopy_data_load("EURUSD", timeframe="BAD", request_id="req-6")

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_load_invalid_date_range() -> None:
    result = dukascopy_data_load(
        "EURUSD",
        start_date="2024-02-01",
        end_date="2024-01-01",
        request_id="req-7",
    )

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_load_invalid_count() -> None:
    result = dukascopy_data_load("EURUSD", count=DUKASCOPY_MAX_LIMIT + 1)

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_load_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout_get(url: str, **kwargs: Any) -> FakeResponse:
        raise requests.Timeout("timed out")

    monkeypatch.setattr("tools.data.dukascopy.requests.get", timeout_get)
    result = dukascopy_data_load("EURUSD", cache=False, max_retries=0)

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TIMEOUT"


def test_load_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def network_get(url: str, **kwargs: Any) -> FakeResponse:
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("tools.data.dukascopy.requests.get", network_get)
    result = dukascopy_data_load("EURUSD", cache=False, max_retries=0)

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "NETWORK_ERROR"


def test_load_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tools.data.dukascopy.requests.get", _fake_empty_get)

    result = dukascopy_data_load("EURUSD", cache=False)

    _standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_tools_never_return_none() -> None:
    assert dukascopy_data_resolve_instrument("EURUSD") is not None
    assert dukascopy_data_list_symbols() is not None


def test_snapshot_payload_empty_and_freshness() -> None:
    snapshot = dukascopy_module.DukascopyBarsSnapshot(
        symbol="EURUSD",
        timeframe="M1",
        bars=pd.DataFrame(
            columns=["open", "high", "low", "close"],
            index=pd.DatetimeIndex([], name="timestamp"),
        ),
        observed_at=datetime.now(timezone.utc),
        max_age_seconds=60,
    )

    payload = snapshot.to_payload(include_bars=False)

    assert payload["row_count"] == 0
    assert payload["start_at"] is None
    assert payload["end_at"] is None
    assert snapshot.freshness()["is_fresh"] is True


def test_dukascopy_validation_edge_cases() -> None:
    assert dukascopy_module._validate_timeframe(None) == (
        "timeframe must be a non-empty string."
    )
    assert dukascopy_module._validate_optional_date(123, "start_date") == (
        "start_date must be a YYYY-MM-DD string or None."
    )
    assert dukascopy_module._validate_optional_date("bad-date", "start_date") == (
        "start_date must use YYYY-MM-DD format."
    )
    assert dukascopy_module._validate_optional_positive_int(True, "count") == (
        "count must be a positive integer when provided."
    )
    assert dukascopy_module._validate_positive_number(False, "timeout") == (
        "timeout must be a positive number."
    )
    assert dukascopy_module._validate_bool("true", "cache") == (
        "cache must be a boolean."
    )
    assert dukascopy_module._validate_offer_side("X") == (
        "offer_side must be 'B' for bid or 'A' for ask."
    )
    assert "timezone_name is not recognized" in str(
        dukascopy_module._validate_timezone("Not/A_Zone")
    )


def test_dukascopy_helpers_cover_resolution_and_rows() -> None:
    assert dukascopy_module._resolve_dukascopy_instrument("EUR/USD") == "EUR/USD"
    assert dukascopy_module._resolve_dukascopy_instrument("ABCDEF") == "ABC/DEF"
    assert dukascopy_module._resolve_dukascopy_instrument("BTCUSD") == "BTC/USD"
    assert dukascopy_module._columns_for_interval(dukascopy_module.INTERVAL_TICK) == [
        "timestamp",
        "bidprice",
        "askprice",
        "bidvolume",
        "askvolume",
    ]

    empty = dukascopy_module._rows_to_frame([], dukascopy_module.INTERVAL_MIN_1)
    assert empty.empty
    assert list(empty.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]


def test_apply_timezone_handles_empty_naive_and_non_utc() -> None:
    empty = pd.DataFrame(index=pd.DatetimeIndex([], name="timestamp"))
    assert dukascopy_module._apply_timezone(empty, "UTC") is empty

    frame = pd.DataFrame(
        {"open": [1.0]},
        index=pd.DatetimeIndex([datetime(2026, 1, 1)], name="timestamp"),
    )

    utc_frame = dukascopy_module._apply_timezone(frame, "UTC")
    dubai_frame = dukascopy_module._apply_timezone(frame, "Asia/Dubai")

    assert str(utc_frame.index.tz) == "UTC"
    assert "Dubai" in str(dubai_frame.index.tz)


def test_normalize_dukascopy_bars_validation_paths() -> None:
    valid = pd.DataFrame(
        {
            "Open": ["1.0"],
            "High": ["1.1"],
            "Low": ["0.9"],
            "Close": ["1.05"],
        },
        index=pd.DatetimeIndex([datetime(2026, 1, 1)], name="timestamp"),
    )
    snapshot = dukascopy_module._normalize_dukascopy_bars(
        valid,
        symbol="eurusd",
        timeframe="m1",
        observed_at=datetime(2026, 1, 1),
    )

    assert snapshot.symbol == "EURUSD"
    assert snapshot.timeframe == "M1"
    assert snapshot.observed_at.tzinfo is timezone.utc

    with pytest.raises(ValueError, match="max_age"):
        dukascopy_module._normalize_dukascopy_bars(
            valid, symbol="EURUSD", timeframe="M1", max_age_seconds=-1
        )
    with pytest.raises(TypeError, match="DataFrame"):
        dukascopy_module._normalize_dukascopy_bars(
            object(), symbol="EURUSD", timeframe="M1"  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="no bars"):
        dukascopy_module._normalize_dukascopy_bars(
            pd.DataFrame(), symbol="EURUSD", timeframe="M1"
        )


def test_aliases_and_normalize_public_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("tools.data.dukascopy.requests.get", _fake_dukascopy_get)

    loaded = dukascopy_module.load_dukascopy(
        "EURUSD",
        timeframe="M1",
        count=1,
        cache=False,
    )
    fetched = dukascopy_module.fetch(
        "EURUSD",
        timeframe="M1",
        count=1,
        request_id="alias",
    )
    resolved = dukascopy_module.get_instrument("EURUSD")
    stream = dukascopy_module.live_fetch(request_id="stream")
    normalized = dukascopy_module.normalize_dukascopy_bars(
        pd.DataFrame(
            {
                "open": [1.0],
                "high": [1.1],
                "low": [0.9],
                "close": [1.05],
            },
            index=pd.DatetimeIndex([datetime(2026, 1, 1)], name="timestamp"),
        ),
        symbol="EURUSD",
        timeframe="M1",
    )
    invalid = dukascopy_module.normalize_dukascopy_bars(
        pd.DataFrame(), symbol="", timeframe="M1"
    )

    assert loaded["status"] == "success"
    assert fetched["status"] == "success"
    assert resolved["status"] == "success"
    assert stream["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert normalized["status"] == "success"
    assert invalid["error"]["code"] == "INVALID_INPUT"


def test_dukascopy_load_validation_and_failure_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_cache = dukascopy_data_load("EURUSD", cache="yes")  # type: ignore[arg-type]
    bad_timeout = dukascopy_data_load("EURUSD", timeout=0)
    bad_retry = dukascopy_data_load("EURUSD", max_retries=-1)
    bad_side = dukascopy_data_load("EURUSD", offer_side="X")
    bad_zone = dukascopy_data_load("EURUSD", timezone_name="Not/A_Zone")

    def explode_get(url: str, **kwargs: Any) -> FakeResponse:
        raise RuntimeError("boom")

    monkeypatch.setattr("tools.data.dukascopy.requests.get", explode_get)
    failed = dukascopy_data_load("EURUSD", cache=False, max_retries=0)

    for result in (bad_cache, bad_timeout, bad_retry, bad_side, bad_zone):
        _standard_schema(result)
        assert result["error"]["code"] == "INVALID_INPUT"
    assert failed["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_normalization_helpers() -> None:
    naive = datetime(2026, 1, 1)
    aware = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert to_utc(naive).tzinfo is timezone.utc
    assert format_timestamp_z(None) is None
    assert format_timestamp_z(aware).endswith("Z")
    with pytest.raises(TypeError):
        to_utc("not-a-date")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative"):
        evaluate_freshness(aware, max_age_seconds=-1)

    class Clock:
        @staticmethod
        def now(tz: timezone) -> datetime:
            return datetime(2026, 1, 1, 0, 2, tzinfo=tz)

    stale = evaluate_freshness(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        max_age_seconds=60,
        clock=Clock(),
    )
    assert stale["is_fresh"] is False


def test_prepare_ohlcv_data_validation_and_numeric_conversion() -> None:
    frame = pd.DataFrame(
        {
            "Open": ["1.0"],
            "High": ["1.1"],
            "Low": ["0.9"],
            "Close": ["1.05"],
            "Volume": ["100"],
        }
    )

    normalized = prepare_ohlcv_data(frame)

    assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]
    assert normalized["volume"].iloc[0] == 100
    with pytest.raises(TypeError):
        prepare_ohlcv_data(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="empty"):
        prepare_ohlcv_data(pd.DataFrame())
    with pytest.raises(ValueError, match="missing"):
        prepare_ohlcv_data(pd.DataFrame({"open": [1.0]}))
