"""Unit tests for strategy registry and standard tool schema."""

from __future__ import annotations

from tools.strategy import (
    get_strategy_metadata,
    list_strategy_names,
    register_builtin_strategy_tools,
    validate_strategy_dataframe,
)


def assert_standard_response(result: dict) -> None:
    """Assert HaruQuant standard response shape."""
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["status"] in {"success", "error"}
    assert "tool_name" in result["metadata"]
    assert "execution_ms" in result["metadata"]
    assert "request_id" in result["metadata"]


def test_register_and_list_builtin_strategies() -> None:
    result = register_builtin_strategy_tools(request_id="unit-reg-001")
    assert_standard_response(result)
    assert result["status"] == "success"
    names = list_strategy_names(request_id="unit-reg-002")
    assert_standard_response(names)
    assert "TrendFollowingStrategy" in names["data"]["strategies"]
    assert "TradeDecompositionStrategy" in names["data"]["strategies"]


def test_get_strategy_metadata_for_one_strategy() -> None:
    result = get_strategy_metadata("TrendFollowingStrategy", request_id="unit-meta-001")
    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"]["strategy"]["strategy_type"] == "vectorized"


def test_get_strategy_metadata_unknown_returns_error() -> None:
    result = get_strategy_metadata("MissingStrategy", request_id="unit-meta-err")
    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_validate_strategy_dataframe_success(ohlc_data) -> None:
    result = validate_strategy_dataframe(ohlc_data, request_id="unit-df-001")
    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"]["valid"] is True


def test_validate_strategy_dataframe_invalid_input() -> None:
    result = validate_strategy_dataframe("not a dataframe", request_id="unit-df-err")
    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
