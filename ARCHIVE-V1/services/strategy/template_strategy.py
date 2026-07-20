"""Standard HaruQuant strategy template.

Purpose:
    Standard HaruQuant strategy template.

Classes:
    TemplateStrategy: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in package __init__.py files;
    private underscore helpers remain implementation details.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from app.services.strategy.base import BaseStrategy, SignalDict
from app.services.utils.logger import logger

TOOL_NAME = "template_strategy"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


class TemplateStrategy(BaseStrategy):
    """Replace this class with a concrete simple, stateful, or hybrid strategy."""

    strategy_name = "TemplateStrategy"
    strategy_type = "simple"  # simple | stateful | hybrid
    signal_schema_version = "1.0"
    action_schema_version = "1.0"

    def __init__(self, params: dict[str, Any] | None = None):
        """Internal function for template_strategy.__init__."""
        super().__init__(params)
        self._load_params()
        self._validate_params()

    def _load_params(self) -> None:
        """Internal function for template_strategy._load_params."""
        self.symbol = str(self.params.get("symbol", "UNKNOWN"))
        self.fast_period = int(self.params.get("fast_period", 20))
        self.slow_period = int(self.params.get("slow_period", 50))

    def _validate_params(self) -> None:
        """Internal function for template_strategy._validate_params."""
        if not self.symbol:
            raise ValueError("symbol must be provided.")
        if self.fast_period <= 0:
            raise ValueError("fast_period must be positive.")
        if self.slow_period <= 0:
            raise ValueError("slow_period must be positive.")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period.")

    def on_init(self) -> None:
        """Public function for template_strategy.on_init."""
        logger.info(
            "%s initialized for %s fast=%s slow=%s",
            self.strategy_name,
            self.symbol,
            self.fast_period,
            self.slow_period,
        )

    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate features, simple signal columns, and event activators."""
        data = data.copy()
        data = self._calculate_indicators(data)
        data = self._shift_features(data)
        data = self._ensure_signal_columns(data)
        data = self._generate_simple_signals(data)
        data = self._generate_event_activators(data)
        return data

    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Internal function for template_strategy._calculate_indicators."""
        data[f"sma_{self.fast_period}"] = data["close"].rolling(self.fast_period).mean()
        data[f"sma_{self.slow_period}"] = data["close"].rolling(self.slow_period).mean()
        return data

    def _shift_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Internal function for template_strategy._shift_features."""
        fast = f"sma_{self.fast_period}"
        slow = f"sma_{self.slow_period}"
        data[f"{fast}_signal"] = data[fast].shift(1)
        data[f"{slow}_signal"] = data[slow].shift(1)
        data[f"prev_{fast}_signal"] = data[f"{fast}_signal"].shift(1)
        data[f"prev_{slow}_signal"] = data[f"{slow}_signal"].shift(1)
        return data

    def _ensure_signal_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Internal function for template_strategy._ensure_signal_columns."""
        defaults: dict[str, Any] = {
            "entry_signal": 0,
            "exit_signal": 0,
            "pending_signal": 0,
            "cancel_pending_signal": 0,
            "pending_signal_2": 0,
            "cancel_pending_signal_2": 0,
            "price": float("nan"),
            "price_2": float("nan"),
            "stop_loss": float("nan"),
            "take_profit": float("nan"),
            "signal_reason": "",
            "setup_id": "",
            "group_id": "",
            "buy_setup_active": False,
            "sell_setup_active": False,
            "buy_add_active": False,
            "sell_add_active": False,
            "buy_exit_active": False,
            "sell_exit_active": False,
            "buy_pyramid_active": False,
            "sell_pyramid_active": False,
            "buy_martingale_active": False,
            "sell_martingale_active": False,
            "buy_decompose_active": False,
            "sell_decompose_active": False,
            "buy_trail_active": False,
            "sell_trail_active": False,
        }
        for column, default in defaults.items():
            if column not in data.columns:
                data[column] = default
        return data

    def _generate_simple_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Internal function for template_strategy._generate_simple_signals."""
        fast = f"sma_{self.fast_period}_signal"
        slow = f"sma_{self.slow_period}_signal"
        prev_fast = f"prev_sma_{self.fast_period}_signal"
        prev_slow = f"prev_sma_{self.slow_period}_signal"

        buy = (data[fast] > data[slow]) & (data[prev_fast] <= data[prev_slow])
        sell = (data[fast] < data[slow]) & (data[prev_fast] >= data[prev_slow])

        data.loc[buy, "entry_signal"] = 1
        data.loc[buy, "price"] = data.loc[buy, "open"]
        data.loc[buy, "signal_reason"] = "Bullish moving average crossover"
        data.loc[buy, "setup_id"] = "template_buy"
        data.loc[buy, "group_id"] = "template_buy"

        data.loc[sell, "entry_signal"] = -1
        data.loc[sell, "price"] = data.loc[sell, "open"]
        data.loc[sell, "signal_reason"] = "Bearish moving average crossover"
        data.loc[sell, "setup_id"] = "template_sell"
        data.loc[sell, "group_id"] = "template_sell"
        return data

    def _generate_event_activators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Internal function for template_strategy._generate_event_activators."""
        data["buy_setup_active"] = data["entry_signal"] == 1
        data["sell_setup_active"] = data["entry_signal"] == -1
        return data

    def get_signal(self, data: pd.DataFrame, index: int) -> SignalDict | None:
        """Public function for template_strategy.get_signal."""
        return super().get_signal(data, index)
