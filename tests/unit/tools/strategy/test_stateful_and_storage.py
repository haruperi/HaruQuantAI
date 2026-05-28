"""Unit tests for stateful strategy support and guarded storage."""

from __future__ import annotations

import pandas as pd

from tools.strategy import PositionSnapshot, StrategyContext, validate_strategy_actions
from tools.strategy.examples.trade_decomposition import TradeDecompositionStrategy
from tools.strategy.storage import save_strategy_source_file


def _tick_data() -> pd.DataFrame:
    prices = [1.1000 + (index * 0.0001) for index in range(30)]
    return pd.DataFrame(
        {"bid": prices, "ask": [price + 0.0001 for price in prices]},
        index=pd.date_range("2026-01-01", periods=len(prices), freq="min"),
    )


def test_trade_decomposition_returns_actions_on_initial_buy_trigger() -> None:
    data = _tick_data()
    strategy = TradeDecompositionStrategy({"symbol": "EURUSD", "rsi_period": 3})
    strategy.on_init()
    strategy.state["previous_rsi"] = 20.0
    context = StrategyContext(
        strategy_id="td-001",
        symbol="EURUSD",
        market_data=data,
        current_tick={"bid": 1.1030, "ask": 1.1031, "is_bar_close": "close"},
        positions=[],
        metadata={"tick_index": len(data) - 1},
    )
    actions = strategy.on_event(context)
    assert actions
    assert actions[0].action_type == "OPEN"


def test_validate_strategy_actions_success() -> None:
    actions = [
        {"action_type": "OPEN", "symbol": "EURUSD", "side": "BUY", "volume": 0.1},
        {
            "action_type": "CLOSE",
            "symbol": "EURUSD",
            "side": "BUY",
            "volume": 0.1,
            "ticket": "1",
        },
    ]
    result = validate_strategy_actions(actions, request_id="unit-actions-001")
    assert result["status"] == "success"
    assert result["data"]["count"] == 2


def test_validate_strategy_actions_invalid() -> None:
    result = validate_strategy_actions(
        [{"action_type": "OPEN", "symbol": "EURUSD", "side": "BUY", "volume": 0}],
        request_id="unit-actions-err",
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_save_strategy_source_file_writes_snapshot(tmp_path) -> None:
    result = save_strategy_source_file(
        base_dir=str(tmp_path),
        strategy_name="demo_strategy",
        version="1.0.0",
        source_code="class Demo: pass\n",
        request_id="unit-save-001",
    )
    assert result["status"] == "success"
    assert result["metadata"]["tool_risk_level"] == "medium"
    assert result["metadata"]["writes_file"] is True


def test_save_strategy_source_file_rejects_unsafe_path(tmp_path) -> None:
    result = save_strategy_source_file(
        base_dir=str(tmp_path),
        strategy_name="../bad",
        version="1.0.0",
        source_code="class Demo: pass\n",
        request_id="unit-save-err",
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
