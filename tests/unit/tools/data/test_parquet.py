"""Unit tests for HaruQuantAI Parquet data tools."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import pytest

from tools.data import parquet as parquet_module
from tools.data.parquet import (
    MEDIUM_RISK,
    PARQUET_DATA_LOAD_TOOL,
    PARQUET_DATA_SAVER_FILE_EXISTS_TOOL,
    PARQUET_DATA_SAVER_LOAD_TOOL,
    PARQUET_DATA_SAVER_SAVE_TOOL,
    load_parquet,
    parquet_data_load,
    parquet_data_saver_file_exists,
    parquet_data_saver_load,
    parquet_data_saver_save,
)


def _sample_frame() -> pd.DataFrame:
    """Return a small OHLCVS DataFrame for tests."""

    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=3, freq="h"),
            "open": [1.0, 1.1, 1.2],
            "high": [1.2, 1.3, 1.4],
            "low": [0.9, 1.0, 1.1],
            "close": [1.1, 1.2, 1.3],
            "volume": [100, 110, 120],
            "spread": [10, 11, 12],
        }
    )


def _assert_standard_response(
    result: Dict[str, Any],
    *,
    expected_status: str,
    expected_tool_name: str,
) -> None:
    """Assert the standard HaruQuantAI tool response shape."""

    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["status"] == expected_status
    assert isinstance(result["message"], str)
    assert isinstance(result["metadata"], dict)
    assert result["metadata"]["tool_name"] == expected_tool_name
    assert result["metadata"]["tool_version"] == "1.0.0"
    assert result["metadata"]["tool_category"] == "data"
    assert isinstance(result["metadata"]["execution_ms"], float)
    assert result["metadata"]["modifies_database"] is False
    assert result["metadata"]["places_trade"] is False
    assert result["metadata"]["requires_network"] is False
    if expected_status == "success":
        assert result["error"] is None
        assert result["data"] is not None
    else:
        assert result["data"] is None
        assert isinstance(result["error"], dict)
        assert "code" in result["error"]
        assert "details" in result["error"]


@pytest.fixture(name="parquet_path")
def fixture_parquet_path(tmp_path):
    """Create a sample Parquet file, skipping if no Parquet engine exists."""

    pytest.importorskip("pyarrow")
    path = tmp_path / "eurusd_h1.parquet"
    _sample_frame().to_parquet(path)
    return path


def test_load_parquet_success(parquet_path) -> None:
    """load_parquet should return a normalized DataFrame."""

    frame = load_parquet(parquet_path)

    assert list(frame.columns) == [
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "spread",
    ]
    assert len(frame) == 3


def test_load_parquet_missing_file_raises(tmp_path) -> None:
    """load_parquet should fail clearly when the file is missing."""

    with pytest.raises(FileNotFoundError):
        load_parquet(tmp_path / "missing.parquet")


def test_load_parquet_rejects_invalid_extension(tmp_path) -> None:
    """load_parquet should reject non-Parquet paths."""

    invalid_path = tmp_path / "bad.csv"
    invalid_path.write_text("open,high,low,close\n", encoding="utf-8")

    with pytest.raises(ValueError, match=".parquet"):
        load_parquet(invalid_path)


def test_parquet_data_load_success(parquet_path) -> None:
    """parquet_data_load should return serialized market data."""

    result = parquet_data_load(parquet_path, request_id="test-load-001")

    _assert_standard_response(
        result,
        expected_status="success",
        expected_tool_name=PARQUET_DATA_LOAD_TOOL,
    )
    assert result["data"]["symbol"] == "EURUSD_H1"
    assert result["data"]["rows"] == 3
    assert result["metadata"]["read_only"] is True
    assert result["metadata"]["writes_file"] is False


def test_parquet_data_load_missing_path_returns_invalid_input() -> None:
    """Missing path should return INVALID_INPUT."""

    result = parquet_data_load("", request_id="test-load-002")

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_LOAD_TOOL,
    )
    assert result["error"]["code"] == "INVALID_INPUT"


def test_parquet_data_load_missing_file_returns_data_not_found(tmp_path) -> None:
    """Missing Parquet file should return DATA_NOT_FOUND."""

    result = parquet_data_load(tmp_path / "missing.parquet")

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_LOAD_TOOL,
    )
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_parquet_data_load_rejects_missing_ohlc(monkeypatch, tmp_path) -> None:
    """Parquet files missing OHLC columns should fail with structured error."""

    pytest.importorskip("pyarrow")
    path = tmp_path / "invalid.parquet"
    pd.DataFrame({"close": [1.0]}).to_parquet(path)

    result = parquet_data_load(path)

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_LOAD_TOOL,
    )
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_parquet_data_saver_file_exists_with_explicit_path(tmp_path) -> None:
    """File-exists tool should return false for an absent explicit path."""

    result = parquet_data_saver_file_exists(
        path=tmp_path / "saved.parquet",
        request_id="test-exists-001",
    )

    _assert_standard_response(
        result,
        expected_status="success",
        expected_tool_name=PARQUET_DATA_SAVER_FILE_EXISTS_TOOL,
    )
    assert result["data"]["exists"] is False
    assert result["data"]["path"].endswith("saved.parquet")


def test_parquet_data_saver_file_exists_rejects_bad_symbol() -> None:
    """Invalid symbol should return INVALID_INPUT."""

    result = parquet_data_saver_file_exists(symbol="bad symbol")

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_SAVER_FILE_EXISTS_TOOL,
    )
    assert result["error"]["code"] == "INVALID_INPUT"


def test_parquet_data_saver_save_success(monkeypatch, tmp_path) -> None:
    """Save tool should return medium-risk file-writing metadata."""

    output_path = tmp_path / "saved.parquet"

    def fake_save_data(*args, **kwargs):
        return {"path": str(output_path), "rows": 3}

    monkeypatch.setattr(parquet_module, "_save_data", fake_save_data)

    result = parquet_data_saver_save(
        data={"df": _sample_frame(), "symbol": "EURUSD", "timeframe": "H1"},
        path=output_path,
        request_id="test-save-001",
    )

    _assert_standard_response(
        result,
        expected_status="success",
        expected_tool_name=PARQUET_DATA_SAVER_SAVE_TOOL,
    )
    assert result["metadata"]["tool_risk_level"] == MEDIUM_RISK
    assert result["metadata"]["read_only"] is False
    assert result["metadata"]["writes_file"] is True


def test_parquet_data_saver_save_rejects_missing_data() -> None:
    """Save tool should reject missing payloads."""

    result = parquet_data_saver_save(data=None)

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_SAVER_SAVE_TOOL,
    )
    assert result["error"]["code"] == "INVALID_INPUT"
    assert result["metadata"]["read_only"] is False
    assert result["metadata"]["writes_file"] is True


def test_parquet_data_saver_load_success(monkeypatch, tmp_path) -> None:
    """Saved-load tool should return candles and sidecar metadata."""

    target_path = tmp_path / "saved.parquet"
    data_obj = SimpleNamespace(
        df=_sample_frame(),
        symbol="EURUSD",
        timeframe="H1",
        metadata={"source": "unit-test"},
    )

    monkeypatch.setattr(parquet_module, "_load_saved_data", lambda **kwargs: data_obj)
    monkeypatch.setattr(
        parquet_module, "_saved_data_path", lambda **kwargs: target_path
    )
    monkeypatch.setattr(
        parquet_module,
        "_data_to_metadata",
        lambda data: {"symbol": data.symbol, "timeframe": data.timeframe},
    )

    result = parquet_data_saver_load(path=target_path, request_id="test-load-saved-001")

    _assert_standard_response(
        result,
        expected_status="success",
        expected_tool_name=PARQUET_DATA_SAVER_LOAD_TOOL,
    )
    assert result["data"]["rows"] == 3
    assert result["data"]["metadata"] == {"symbol": "EURUSD", "timeframe": "H1"}


def test_parquet_data_saver_load_missing_file(monkeypatch, tmp_path) -> None:
    """Missing saved artifact should return DATA_NOT_FOUND."""

    def fake_load_saved_data(**kwargs):
        raise FileNotFoundError("not found")

    monkeypatch.setattr(parquet_module, "_load_saved_data", fake_load_saved_data)

    result = parquet_data_saver_load(path=tmp_path / "missing.parquet")

    _assert_standard_response(
        result,
        expected_status="error",
        expected_tool_name=PARQUET_DATA_SAVER_LOAD_TOOL,
    )
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_parquet_tools_never_return_none(tmp_path) -> None:
    """Official tools should always return structured dictionaries."""

    results = [
        parquet_data_load(tmp_path / "missing.parquet"),
        parquet_data_saver_file_exists(path=tmp_path / "missing.parquet"),
        parquet_data_saver_save(data=None),
        parquet_data_saver_load(path=tmp_path / "missing.parquet"),
    ]

    assert all(isinstance(result, dict) for result in results)
    assert all(result is not None for result in results)
