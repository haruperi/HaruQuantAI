"""Usage example for stateful TradeDecompositionStrategy action proposals."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.strategy import StrategyContext, validate_strategy_actions
from tools.strategy.examples.trade_decomposition import TradeDecompositionStrategy


def main() -> None:
    """Run a stateful strategy event and validate proposed actions."""
    data = pd.DataFrame({"bid": [1.1000 + index * 0.0001 for index in range(30)]})
    data["ask"] = data["bid"] + 0.0001
    strategy = TradeDecompositionStrategy({"symbol": "EURUSD", "rsi_period": 3})
    strategy.on_init()
    strategy.state["previous_rsi"] = 20.0
    context = StrategyContext(
        strategy_id="usage-td",
        symbol="EURUSD",
        market_data=data,
        current_tick={"bid": 1.1030, "ask": 1.1031, "is_bar_close": "close"},
        metadata={"tick_index": len(data) - 1},
    )
    actions = [action.to_dict() for action in strategy.on_event(context)]
    result = validate_strategy_actions(actions, request_id="usage-stateful-actions-001")
    if result["status"] == "success":
        print(result["data"]["actions"])
    else:
        print(result["error"])


if __name__ == "__main__":
    main()
