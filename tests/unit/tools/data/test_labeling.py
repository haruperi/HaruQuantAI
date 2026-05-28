"""Unit tests for tools.data.labeling."""

from __future__ import annotations

import pandas as pd
import pytest

from tools.data.labeling import labeler_lexlb


def assert_standard_response(result: dict) -> None:
    """Assert a HaruQuantAI standard tool response shape."""

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


def test_labeler_lexlb_success_with_datetime_series() -> None:
    series = pd.Series(
        [100, 105, 110, 100, 95, 104],
        index=pd.date_range("2024-01-01", periods=6, freq="D"),
    )

    result = labeler_lexlb(
        series, up_threshold=0.05, down_threshold=0.05, request_id="test-001"
    )

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["metadata"]["tool_name"] == "labeler_lexlb"
    assert result["metadata"]["read_only"] is True
    assert result["metadata"]["places_trade"] is False
    assert result["metadata"]["requires_network"] is False
    assert result["data"]["summary"]["rows"] == 6
    assert all(isinstance(record, dict) for record in result["data"]["labels"])


def test_labeler_lexlb_short_series_returns_success() -> None:
    series = pd.Series([100.0], index=pd.date_range("2024-01-01", periods=1))

    result = labeler_lexlb(series, 0.01, 0.01)

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"]["summary"]["rows"] == 1


@pytest.mark.parametrize(
    "up_threshold,down_threshold", [(0, 0.1), (0.1, 0), ("bad", 0.1), (0.1, None)]
)
def test_labeler_lexlb_invalid_thresholds(up_threshold, down_threshold) -> None:
    series = pd.Series([1, 2, 3])

    result = labeler_lexlb(series, up_threshold, down_threshold)

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_labeler_lexlb_rejects_empty_series() -> None:
    result = labeler_lexlb(pd.Series(dtype=float), 0.01, 0.01)

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_labeler_lexlb_rejects_non_numeric_series() -> None:
    result = labeler_lexlb(pd.Series(["a", "b", "c"]), 0.01, 0.01)

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_labeler_lexlb_never_returns_none() -> None:
    result = labeler_lexlb(pd.Series([1, 2, 3]), 0.01, 0.01)

    assert result is not None
