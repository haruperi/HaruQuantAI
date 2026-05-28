"""Unit tests for tools.data.csv."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from tools.data import _common as data_common
from tools.data import csv as csv_tools
from tools.utils import common as utils_common

REQUIRED_METADATA_KEYS = {
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
}


def _write_sample_csv(path: Path) -> Path:
    path.write_text(
        "time,open,high,low,close,volume,spread\n"
        "2026-01-01 00:00:00,1.1000,1.1010,1.0990,1.1005,100,12\n"
        "2026-01-01 00:01:00,1.1005,1.1020,1.1000,1.1010,120,10\n"
        "2026-01-01 00:02:00,1.1010,1.1030,1.1005,1.1025,140,11\n",
        encoding="utf-8",
    )
    return path


def _assert_tool_schema(result: Dict[str, Any]) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["status"] in {"success", "error"}
    assert isinstance(result["message"], str)
    assert isinstance(result["metadata"], dict)
    assert REQUIRED_METADATA_KEYS <= set(result["metadata"])
    assert isinstance(result["metadata"]["execution_ms"], float)
    if result["status"] == "success":
        assert result["error"] is None
    else:
        assert result["data"] is None
        assert isinstance(result["error"], dict)
        assert {"code", "details"} <= set(result["error"])


def test_load_csv_success_lowercases_columns(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    frame = csv_tools.load_csv(csv_path, index_col=None)

    assert isinstance(frame, pd.DataFrame)
    assert {"open", "high", "low", "close"} <= set(frame.columns)
    assert "volume" in frame.columns
    assert len(frame) == 3


def test_load_csv_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        csv_tools.load_csv(tmp_path / "missing.csv")


def test_load_csv_missing_ohlc_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("time,bid,ask\n2026-01-01,1.1,1.2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required OHLC"):
        csv_tools.load_csv(csv_path, index_col=None)


def test_csv_data_source_fetch_data_success(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")
    source = csv_tools.CSVDataSource(csv_path, cache=False)

    frame = source.fetch_data("EURUSD", "M1", 0, 2)

    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 2
    assert isinstance(frame.index, pd.DatetimeIndex)


def test_csv_data_source_fetch_data_out_of_range_returns_none(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")
    source = csv_tools.CSVDataSource(csv_path, cache=False)

    assert source.fetch_data("EURUSD", "M1", 0, 99) is None


def test_csv_data_source_missing_date_column_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "EURUSD.csv"
    csv_path.write_text(
        "open,high,low,close\n1.0,1.1,0.9,1.05\n",
        encoding="utf-8",
    )

    source = csv_tools.CSVDataSource(csv_path, cache=False)

    with pytest.raises(ValueError, match="No date/time column"):
        source.fetch_data("EURUSD", "M1", 0, 1)


def test_csv_data_load_success_response_schema(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_load(
        csv_path, index_col=None, request_id="test-load-001"
    )

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["metadata"]["tool_name"] == "csv_data_load"
    assert result["metadata"]["tool_risk_level"] == "low"
    assert result["metadata"]["read_only"] is True
    assert result["data"]["rows"] == 3


def test_csv_data_load_invalid_path_returns_invalid_input(tmp_path: Path) -> None:
    result = csv_tools.csv_data_load(tmp_path / "not_csv.txt", request_id="bad-path")

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_fetch_range_success(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_fetch_range(
        csv_path,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=1,
        end_pos=3,
        request_id="test-fetch-001",
        cache=False,
    )

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["metadata"]["tool_name"] == "csv_data_fetch_range"
    assert result["data"]["rows"] == 2


def test_csv_data_fetch_range_invalid_range_returns_invalid_input(
    tmp_path: Path,
) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_fetch_range(
        csv_path,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=5,
        end_pos=5,
        request_id="bad-range",
    )

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_fetch_range_out_of_bounds_returns_data_not_found(
    tmp_path: Path,
) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_fetch_range(
        csv_path,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=0,
        end_pos=99,
        request_id="missing-range",
        cache=False,
    )

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_csv_data_saver_file_exists_with_explicit_path(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_saver_file_exists(path=csv_path, request_id="exists")

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["exists"] is True


def test_csv_data_saver_file_exists_invalid_symbol_returns_invalid_input() -> None:
    result = csv_tools.csv_data_saver_file_exists(symbol="", timeframe="M1")

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_saver_save_invalid_data_returns_invalid_input(tmp_path: Path) -> None:
    result = csv_tools.csv_data_saver_save(None, path=tmp_path / "out.csv")  # type: ignore[arg-type]

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["metadata"]["tool_risk_level"] == "medium"
    assert result["metadata"]["read_only"] is False
    assert result["metadata"]["writes_file"] is True
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_saver_save_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    out_path = tmp_path / "saved.csv"

    def fake_save_data(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "path": str(out_path),
            "metadata_path": str(tmp_path / "saved.metadata.json"),
        }

    monkeypatch.setattr(csv_tools, "_save_data", fake_save_data)

    result = csv_tools.csv_data_saver_save(
        {"symbol": "EURUSD", "timeframe": "M1", "data": []},
        path=out_path,
        request_id="save-ok",
    )

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["metadata"]["tool_risk_level"] == "medium"
    assert result["metadata"]["read_only"] is False
    assert result["metadata"]["writes_file"] is True


@dataclass
class DummyData:
    df: pd.DataFrame
    symbol: str = "EURUSD"
    timeframe: str = "M1"


def test_csv_data_saver_load_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    csv_path = tmp_path / "saved.csv"
    frame = pd.DataFrame(
        {
            "open": [1.0],
            "high": [1.1],
            "low": [0.9],
            "close": [1.05],
            "volume": [100],
        }
    )

    monkeypatch.setattr(
        csv_tools, "_load_saved_data", lambda **kwargs: DummyData(df=frame)
    )
    monkeypatch.setattr(csv_tools, "_saved_data_path", lambda **kwargs: csv_path)
    monkeypatch.setattr(
        csv_tools, "_data_to_metadata", lambda data: {"symbol": data.symbol}
    )

    result = csv_tools.csv_data_saver_load(path=csv_path, request_id="load-saved")

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["rows"] == 1
    assert result["data"]["metadata"]["symbol"] == "EURUSD"


def test_csv_data_saver_load_missing_returns_data_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    csv_path = tmp_path / "missing.csv"

    def fake_load_saved_data(**kwargs: Any) -> DummyData:
        raise FileNotFoundError("missing saved csv")

    monkeypatch.setattr(csv_tools, "_load_saved_data", fake_load_saved_data)

    result = csv_tools.csv_data_saver_load(path=csv_path, request_id="missing-saved")

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_get_cached_data_rejects_non_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        csv_tools, "get_cached_dataframe", lambda key, loader: {"status": "error"}
    )

    with pytest.raises(TypeError):
        csv_tools.get_cached_data("bad-cache", lambda: pd.DataFrame({"x": [1]}))


def test_saved_data_path_uses_default_symbol_and_timeframe() -> None:
    path = data_common._saved_data_path(
        extension=".csv",
        symbol="eurusd",
        timeframe="m5",
    )

    assert path == Path("data/saved/EURUSD_M5.csv")


def test_save_and_load_data_round_trip_with_sidecar(tmp_path: Path) -> None:
    target = tmp_path / "roundtrip.csv"
    source = data_common.Data(
        df=pd.DataFrame({"open": [1.0], "close": [1.1]}),
        symbol="GBPUSD",
        timeframe="H1",
        metadata={"source": "unit-test"},
    )

    saved = data_common._save_data(
        source,
        extension="csv",
        path=target,
        is_initial=True,
    )
    loaded = data_common._load_saved_data(extension="csv", path=target)

    assert Path(saved["path"]) == target
    assert Path(saved["metadata_path"]).exists()
    assert loaded.symbol == "GBPUSD"
    assert loaded.timeframe == "H1"
    assert loaded.metadata["is_initial"] is True
    assert loaded.df.to_dict("records") == [{"open": 1.0, "close": 1.1}]


def test_save_data_accepts_mapping_payload_and_candles(tmp_path: Path) -> None:
    target = tmp_path / "candles.csv"

    saved = data_common._save_data(
        {
            "symbol": "usdjpy",
            "timeframe": "m15",
            "candles": [{"time": "2026-01-01", "open": 150.0}],
        },
        extension="csv",
        path=target,
    )

    assert saved["metadata"]["symbol"] == "USDJPY"
    assert saved["metadata"]["timeframe"] == "M15"
    assert target.exists()


def test_frame_from_payload_rejects_unsupported_payloads() -> None:
    with pytest.raises(TypeError):
        data_common._frame_from_payload(object())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="list"):
        data_common._frame_from_payload({"data": "not-records"})

    with pytest.raises(ValueError, match="no records"):
        data_common._frame_from_payload({"data": []})


def test_load_saved_data_without_sidecar_uses_defaults(tmp_path: Path) -> None:
    target = tmp_path / "bare.csv"
    target.write_text("open,close\n1.0,1.1\n", encoding="utf-8")

    loaded = data_common._load_saved_data(
        extension="csv",
        path=target,
        symbol="audusd",
        timeframe="m30",
    )

    assert loaded.symbol == "AUDUSD"
    assert loaded.timeframe == "M30"
    assert loaded.metadata == {}


def test_load_saved_data_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        data_common._load_saved_data(extension="csv", path=tmp_path / "missing.csv")


def test_serialize_frame_records_includes_index() -> None:
    frame = pd.DataFrame({"close": [1.2]}, index=pd.Index(["bar-1"], name="bar"))

    assert data_common._serialize_frame_records(frame) == [
        {"bar": "bar-1", "close": 1.2}
    ]


def test_dataframe_cache_loads_once_and_returns_copies() -> None:
    utils_common.clear_dataframe_cache()
    calls = 0

    def loader() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        return pd.DataFrame({"value": [1]})

    first = utils_common.get_cached_dataframe("cache-key", loader)
    first.loc[0, "value"] = 99
    second = utils_common.get_cached_dataframe("cache-key", loader)

    assert calls == 1
    assert second.loc[0, "value"] == 1


def test_dataframe_cache_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="cache key"):
        utils_common.get_cached_dataframe("", lambda: pd.DataFrame())

    with pytest.raises(ValueError, match="callable"):
        utils_common.get_cached_dataframe("key", object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="DataFrame"):
        utils_common.get_cached_dataframe("bad", lambda: object())  # type: ignore[arg-type,return-value]


def test_load_csv_rejects_invalid_options(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    with pytest.raises(ValueError, match="parse_dates"):
        csv_tools.load_csv(csv_path, parse_dates="yes")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="index_col"):
        csv_tools.load_csv(csv_path, index_col=object())  # type: ignore[arg-type]


def test_load_csv_can_skip_ohlc_validation(tmp_path: Path) -> None:
    csv_path = tmp_path / "generic.csv"
    csv_path.write_text("time,bid\n2026-01-01,1.1\n", encoding="utf-8")

    frame = csv_tools.load_csv(csv_path, index_col=None, require_ohlc=False)

    assert list(frame.columns) == ["time", "bid"]


def test_csv_data_source_rejects_invalid_constructor_arguments(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    with pytest.raises(ValueError, match="date_column"):
        csv_tools.CSVDataSource(csv_path, date_column=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="cache"):
        csv_tools.CSVDataSource(csv_path, cache="yes")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="require_ohlc"):
        csv_tools.CSVDataSource(csv_path, require_ohlc="yes")  # type: ignore[arg-type]


def test_csv_data_source_rejects_invalid_fetch_arguments(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")
    source = csv_tools.CSVDataSource(csv_path, cache=False)

    with pytest.raises(ValueError, match="symbol"):
        source.fetch_data("", "M1", 0, 1)

    with pytest.raises(ValueError, match="timeframe"):
        source.fetch_data("EURUSD", "", 0, 1)

    with pytest.raises(ValueError, match="greater than or equal"):
        source.fetch_data("EURUSD", "M1", -1, 1)


def test_csv_data_source_rejects_unknown_date_column(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")
    source = csv_tools.CSVDataSource(csv_path, date_column="missing", cache=False)

    with pytest.raises(ValueError, match="does not exist"):
        source.fetch_data("EURUSD", "M1", 0, 1)


def test_csv_data_source_rejects_unparseable_date_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad_date.csv"
    csv_path.write_text(
        "time,open,high,low,close\nnot-a-date,1.0,1.1,0.9,1.05\n",
        encoding="utf-8",
    )
    source = csv_tools.CSVDataSource(csv_path, cache=False)

    with pytest.raises(ValueError, match="Could not parse"):
        source.fetch_data("EURUSD", "M1", 0, 1)


def test_csv_data_load_missing_file_returns_data_not_found(tmp_path: Path) -> None:
    result = csv_tools.csv_data_load(tmp_path / "missing.csv", request_id="missing")

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_load_execution_failure_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    def broken_load_csv(*args: Any, **kwargs: Any) -> pd.DataFrame:
        raise RuntimeError("boom")

    monkeypatch.setattr(csv_tools, "load_csv", broken_load_csv)

    result = csv_tools.csv_data_load(csv_path, index_col=None)

    _assert_tool_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_csv_data_fetch_range_rejects_invalid_flags(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    result = csv_tools.csv_data_fetch_range(
        csv_path,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=0,
        end_pos=1,
        cache="yes",  # type: ignore[arg-type]
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_fetch_range_execution_failure_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    csv_path = _write_sample_csv(tmp_path / "EURUSD.csv")

    class BrokenSource:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def fetch_data(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
            raise RuntimeError("range failed")

    monkeypatch.setattr(csv_tools, "CSVDataSource", BrokenSource)

    result = csv_tools.csv_data_fetch_range(
        csv_path,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=0,
        end_pos=1,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_csv_data_saver_file_exists_default_path_success() -> None:
    result = csv_tools.csv_data_saver_file_exists(symbol="EURUSD", timeframe="M1")

    _assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["path"].endswith("EURUSD_M1.csv")


def test_csv_data_saver_file_exists_execution_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_path(**kwargs: Any) -> Path:
        raise RuntimeError("path failed")

    monkeypatch.setattr(csv_tools, "_saved_data_path", broken_path)

    result = csv_tools.csv_data_saver_file_exists(symbol="EURUSD", timeframe="M1")

    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_csv_data_saver_save_execution_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def broken_save(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("save failed")

    monkeypatch.setattr(csv_tools, "_save_data", broken_save)

    result = csv_tools.csv_data_saver_save(
        {"data": [{"open": 1.0}]},
        path=tmp_path / "saved.csv",
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_csv_data_saver_load_invalid_path_returns_invalid_input() -> None:
    result = csv_tools.csv_data_saver_load(path="not_csv.txt")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_csv_data_saver_load_execution_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    csv_path = tmp_path / "saved.csv"

    def broken_load(**kwargs: Any) -> DummyData:
        raise RuntimeError("load failed")

    monkeypatch.setattr(csv_tools, "_load_saved_data", broken_load)

    result = csv_tools.csv_data_saver_load(path=csv_path)

    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"
