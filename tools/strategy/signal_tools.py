"""Official AI tools for running vectorized strategy signal workflows.

Exported AI Tools:
    - run_vectorized_strategy
    - extract_strategy_signals
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.strategy.base import BaseStrategy
from tools.strategy.registry import get_strategy_class
from tools.utils.standard import execute_tool_boundary
from tools.utils.validators import assert_ohlc_dataframe, serialize_dataframe

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def run_vectorized_strategy(
    strategy_name: str,
    data: pd.DataFrame,
    *,
    params: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Run a registered vectorized strategy over OHLC data.

    Use this AI tool for backtest preparation, strategy validation, or signal
    inspection. It returns processed data and extracted non-neutral signals. It
    does not place trades or mutate the input DataFrame.
    """

    def operation() -> dict[str, Any]:
        assert_ohlc_dataframe(data, min_rows=1)
        strategy_cls = get_strategy_class(strategy_name)
        strategy = strategy_cls(params or {})
        if not isinstance(strategy, BaseStrategy):
            raise TypeError("registered strategy must instantiate BaseStrategy.")
        strategy.on_init()
        processed = strategy.on_bar(data.copy(deep=True))
        signals = _extract_signals(strategy, processed)
        return {
            "strategy_name": strategy_name,
            "rows": len(processed),
            "signals": signals,
            "processed_data": serialize_dataframe(processed),
        }

    return execute_tool_boundary(
        tool_name="run_vectorized_strategy",
        request_id=request_id,
        operation=operation,
        success_message="Vectorized strategy executed.",
    )


def extract_strategy_signals(
    strategy_name: str,
    processed_data: pd.DataFrame,
    *,
    params: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Extract non-neutral signal dictionaries from processed strategy data.

    Use this AI tool after a strategy has already generated signal columns.
    """

    def operation() -> dict[str, Any]:
        strategy_cls = get_strategy_class(strategy_name)
        strategy = strategy_cls(params or {})
        return {"signals": _extract_signals(strategy, processed_data)}

    return execute_tool_boundary(
        tool_name="extract_strategy_signals",
        request_id=request_id,
        operation=operation,
        success_message="Strategy signals extracted.",
    )


def _extract_signals(
    strategy: BaseStrategy, processed_data: pd.DataFrame
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for row_index in range(len(processed_data)):
        signal = strategy.get_signal(processed_data, row_index)
        if signal is not None:
            signals.append(
                {
                    key: str(value) if key == "time" else value
                    for key, value in signal.items()
                }
            )
    return signals
