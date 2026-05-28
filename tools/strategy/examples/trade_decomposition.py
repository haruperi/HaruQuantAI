"""Production-ready stateful trade decomposition example strategy.

This strategy preserves the uploaded running strategy pattern: it proposes
basket actions such as OPEN, REDUCE, MODIFY_TP, CLOSE, and MOVE_TO_BREAKEVEN.
It never directly executes broker actions.
"""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd

from tools.strategy.base import StatefulEventStrategy
from tools.strategy.contracts import PositionSnapshot, StrategyContext, TradeAction
from tools.strategy.stateful_helpers import (
    current_mid_price,
    historical_mid_prices,
    is_bar_close,
    oldest_position,
    positions_for_side,
    rolling_rsi,
    weighted_average_price,
)
from tools.utils.validators import ensure_no_signal_columns

TradeSide = Literal["BUY", "SELL"]


class TradeDecompositionStrategy(StatefulEventStrategy):
    """Partially reduce older trades and re-enter at better basket prices."""

    strategy_name = "TradeDecompositionStrategy"
    strategy_type = "stateful"
    signal_schema_version = "1.0"
    action_schema_version = "1.0"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        """Initialize decomposition parameters and risk limits."""
        super().__init__(params)
        self.rsi_period = int(self.params.get("rsi_period", 14))
        self.os_level = float(self.params.get("os_level", 30.0))
        self.ob_level = float(self.params.get("ob_level", 70.0))
        self.initial_lot = float(self.params.get("initial_lot", 0.06))
        self.vol_increase = float(self.params.get("vol_increase", 0.06))
        self.vol_decrease = float(self.params.get("vol_decrease", 0.02))
        self.trade_distance = float(self.params.get("trade_distance", 20.0))
        self.trail_points = float(self.params.get("trail_points", 10.0))
        self.child_take_profit_pips = float(
            self.params.get("child_take_profit_pips", self.trail_points)
        )
        self.pip_value = float(self.params.get("pip_value", 0.0001))
        self.max_positions_per_side = int(self.params.get("max_positions_per_side", 5))
        self.max_actions_per_event = int(self.params.get("max_actions_per_event", 10))
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate decomposition parameters and safety limits."""
        if self.rsi_period <= 0:
            raise ValueError("rsi_period must be positive.")
        if not 0 < self.os_level < self.ob_level < 100:
            raise ValueError("RSI levels must satisfy 0 < os_level < ob_level < 100.")
        for field_name in (
            "initial_lot",
            "vol_increase",
            "vol_decrease",
            "trade_distance",
            "trail_points",
            "child_take_profit_pips",
            "pip_value",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive.")
        if self.vol_decrease > self.vol_increase:
            raise ValueError("vol_decrease must not exceed vol_increase.")
        if self.max_positions_per_side <= 0 or self.max_actions_per_event <= 0:
            raise ValueError("max positions/actions limits must be positive.")

    def on_init(self) -> None:
        """Initialize state needed for RSI crossing detection."""
        self.state.setdefault("previous_rsi", None)

    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return neutral signal columns for compatibility with bar engines."""
        return ensure_no_signal_columns(data)

    def on_event(self, context: StrategyContext) -> list[TradeAction]:
        """Return proposed decomposition actions for bar-close events."""
        if not is_bar_close(context):
            return []
        prices = historical_mid_prices(context)
        rsi = rolling_rsi(prices, self.rsi_period)
        if rsi is None:
            return []
        previous_rsi = self.state.get("previous_rsi")
        self.state["previous_rsi"] = rsi
        actions: list[TradeAction] = []
        actions.extend(self._process_side("BUY", rsi, previous_rsi, context))
        actions.extend(self._process_side("SELL", rsi, previous_rsi, context))
        return actions[: self.max_actions_per_event]

    def _process_side(
        self,
        side: TradeSide,
        rsi: float,
        previous_rsi: float | None,
        context: StrategyContext,
    ) -> list[TradeAction]:
        positions = positions_for_side(context, side)
        current_price = current_mid_price(context)
        child_actions = self._child_take_profit_actions(side, current_price, positions)
        if child_actions:
            return child_actions
        if not positions:
            if self._initial_trigger(side, rsi, previous_rsi):
                group_id = self._group_id(context, side)
                return [
                    TradeAction(
                        action_type="OPEN",
                        symbol=context.symbol,
                        side=side,
                        volume=self.initial_lot,
                        setup_id=group_id,
                        group_id=group_id,
                        metadata={"role": "parent"},
                        reason=f"Initial {side} decomposition entry",
                    )
                ]
            return []
        if len(positions) >= self.max_positions_per_side:
            return []
        if not self._drawdown_trigger(side, current_price, positions):
            return []
        if not self._rsi_confirmed(side, rsi):
            return []
        oldest = oldest_position(positions)
        if oldest is None:
            return []
        subtract_amount = min(self.vol_decrease, float(oldest.volume or 0.0))
        if subtract_amount <= 0.0:
            return []
        group_id = self._group_id(context, side, positions)
        new_lot = self.initial_lot + (len(positions) * subtract_amount)
        average_price = weighted_average_price(positions) or current_price
        target_tp = (
            average_price + (self.trail_points * self.pip_value)
            if side == "BUY"
            else average_price - (self.trail_points * self.pip_value)
        )
        return [
            TradeAction(
                action_type="REDUCE",
                symbol=context.symbol,
                side=side,
                ticket=oldest.ticket,
                volume=subtract_amount,
                setup_id=group_id,
                group_id=group_id,
                reason=f"Decompose oldest {side} position",
            ),
            TradeAction(
                action_type="OPEN",
                symbol=context.symbol,
                side=side,
                volume=new_lot,
                setup_id=group_id,
                group_id=group_id,
                metadata={"role": "child", "parent_ticket": oldest.ticket},
                reason=f"{side} decomposition cycle add",
            ),
            TradeAction(
                action_type="MODIFY_TP",
                symbol=context.symbol,
                side=side,
                ticket=oldest.ticket,
                take_profit=target_tp,
                setup_id=group_id,
                group_id=group_id,
                reason=f"Consolidate {side} basket TP",
            ),
        ]

    def _child_take_profit_actions(
        self, side: TradeSide, current_price: float, positions: list[PositionSnapshot]
    ) -> list[TradeAction]:
        child = self._first_child_at_target(side, current_price, positions)
        if child is None:
            return []
        group_id = (
            self._position_group_id(child) or f"{child.symbol}:{side}:decomposition"
        )
        actions = [
            TradeAction(
                action_type="CLOSE",
                symbol=child.symbol,
                side=side,
                ticket=child.ticket,
                volume=child.volume,
                setup_id=child.setup_id or group_id,
                group_id=group_id,
                reason=f"Close first {side} decomposition child at TP",
            )
        ]
        for position in positions:
            if position.ticket == child.ticket:
                continue
            actions.append(
                TradeAction(
                    action_type="MOVE_TO_BREAKEVEN",
                    symbol=position.symbol,
                    side=side,
                    ticket=position.ticket,
                    setup_id=position.setup_id or group_id,
                    group_id=self._position_group_id(position) or group_id,
                    reason=f"Move remaining {side} decomposition trade to breakeven",
                )
            )
        return actions

    def _first_child_at_target(
        self, side: TradeSide, current_price: float, positions: list[PositionSnapshot]
    ) -> PositionSnapshot | None:
        target_distance = self.child_take_profit_pips * self.pip_value
        children = [position for position in positions if self._is_child(position)]
        for position in sorted(children, key=lambda item: str(item.opened_at or "")):
            if side == "BUY" and current_price >= position.open_price + target_distance:
                return position
            if (
                side == "SELL"
                and current_price <= position.open_price - target_distance
            ):
                return position
        return None

    @staticmethod
    def _is_child(position: PositionSnapshot) -> bool:
        return position.metadata.get("role") == "child" or bool(
            position.metadata.get("decomposition_child")
        )

    def _group_id(
        self,
        context: StrategyContext,
        side: TradeSide,
        positions: list[PositionSnapshot] | None = None,
    ) -> str:
        for position in positions or []:
            group_id = self._position_group_id(position)
            if group_id:
                return group_id
        return f"{context.strategy_id}:{context.symbol}:{side}:decomposition"

    @staticmethod
    def _position_group_id(position: PositionSnapshot) -> str | None:
        return (
            position.group_id
            or position.setup_id
            or position.metadata.get("group_id")
            or position.metadata.get("setup_id")
        )

    def _initial_trigger(
        self, side: TradeSide, rsi: float, previous_rsi: float | None
    ) -> bool:
        if previous_rsi is None:
            return False
        return (
            previous_rsi < self.os_level <= rsi
            if side == "BUY"
            else previous_rsi > self.ob_level >= rsi
        )

    def _rsi_confirmed(self, side: TradeSide, rsi: float) -> bool:
        return rsi <= self.os_level if side == "BUY" else rsi >= self.ob_level

    def _drawdown_trigger(
        self, side: TradeSide, current_price: float, positions: list[PositionSnapshot]
    ) -> bool:
        distance = self.trade_distance * self.pip_value
        prices = [float(position.open_price or 0.0) for position in positions]
        return (
            current_price <= min(prices) - distance
            if side == "BUY"
            else current_price >= max(prices) + distance
        )
