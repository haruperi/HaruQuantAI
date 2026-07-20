"""Broker-neutral translation of **Market Structure EA.mq5**.

This M5 strategy depends on the eight most recent non-zero extremes from the
MQL5 ``Examples\\ZigZag`` indicator (Depth 12, Deviation 5, BackStep 3 by
default).  The Python strategy deliberately does not recalculate ZigZag: the
indicator/data layer must supply ``features['zigzag_extremes']`` in newest-first
order.  This keeps feature calculation independently testable and prevents the
strategy from using an incompatible ZigZag implementation.

A bullish structure requires a close above the prior structural high after a
close below it, a descending/turning high sequence, and a rising/turning low
sequence.  A bearish structure mirrors those conditions.  When completely flat,
a bullish signal opens a market buy and creates an opposite sell-stop hedge below
the current structural low; bearish structure opens a market sell and an
opposite buy-stop hedge above the structural high.  Both legs receive profit
targets based on their hedge distance multiplied by ``profit_factor``.

After an execution event confirms the initial two-sided hedge, the EA creates
counter-averaging buy-limit and sell-limit orders at its saved next levels.  If
a side reaches more than one open position, it moves that side's TP to its
unweighted arithmetic average entry and cancels the opposite averaging order.
On new bars it also opens grid market positions when price reaches the stored
next level.  It removes orphaned hedge and averaging pending orders when their
source positions no longer exist.  This source is a hedged grid system without
a portfolio-level loss cap; the Risk Governor must impose all such limits.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from app.services.indicators import arithmetic_average, balance_scaled_volume
from app.services.strategy import (
    Direction,
    EntryType,
    MarketContext,
    PendingOrderSnapshot,
    PositionSnapshot,
    ProtectionRequest,
    SignalSet,
    StrategyDecision,
    TradeIntent,
)
from app.services.strategy.base import BaseStrategy
from app.services.strategy.pybots.mql5_translation_helpers import (
    by_direction,
    entry_price,
    pip_value,
    require_quote,
)


class MarketStructureStrategy(BaseStrategy):
    """ZigZag-structure breakout, opposite hedge, and event-driven grid ladder."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate market structure signals on the DataFrame."""
        df["long_entry"] = 0
        df["short_entry"] = 0
        df["long_exit"] = 0
        df["short_exit"] = 0

        bullish, bearish, _ = self._structure(context)
        if len(df) > 0:
            df.loc[df.index[-1], "long_entry"] = int(bullish)
            df.loc[df.index[-1], "short_entry"] = int(bearish)

        return df

    def build_custom_decision(self, context: MarketContext) -> StrategyDecision | None:
        if self.df_signals is None or len(self.df_signals) < len(context.bars):
            self.precalculate_signals(context)

        current_idx = len(context.bars) - 1
        if self.df_signals is not None and 0 <= current_idx < len(self.df_signals):
            row = self.df_signals.iloc[current_idx]
            bullish = bool(row["long_entry"])
            bearish = bool(row["short_entry"])
        else:
            bullish = bearish = False

        _, _, levels = self._structure(context)
        quote = require_quote(context)

        positions = self._owned_positions(context)
        buys = by_direction(positions, Direction.LONG)
        sells = by_direction(positions, Direction.SHORT)
        intents: list[TradeIntent] = []
        if (  # pragma: no cover
            not positions
            and not self._owned_pending_orders(context)
            and self._entries_allowed_now(context)
        ):
            if bullish:
                intents.extend(  # pragma: no cover
                    self._first_bundle(
                        context, Direction.LONG, levels, quote.ask, quote.bid
                    )
                )
            elif bearish:
                intents.extend(  # pragma: no cover
                    self._first_bundle(
                        context, Direction.SHORT, levels, quote.ask, quote.bid
                    )
                )
        intents.extend(
            self._grid_entry_intents(context, buys, sells, quote.ask, quote.bid)
        )
        return StrategyDecision(
            context.signal_bar.open_time, SignalSet(bullish, bearish), tuple(intents)
        )

    def build_execution_event_intents(
        self, context: MarketContext, event_id: str
    ) -> Sequence[TradeIntent]:
        """Rebuild source ``OnTrade`` actions from an execution-reconciled snapshot."""
        del event_id
        positions = self._owned_positions(context)
        pending = self._owned_pending_orders(context)
        buys = by_direction(positions, Direction.LONG)
        sells = by_direction(positions, Direction.SHORT)
        intents: list[TradeIntent] = []
        if (
            len(buys) == 1
            and len(sells) == 1
            and not self._find_pending(pending, "CABuy")
            and not self._find_pending(pending, "CASell")
        ):
            next_buy = self.state.get_custom("next_buy")  # pragma: no cover
            next_sell = self.state.get_custom("next_sell")  # pragma: no cover
            volume = self._volume(context)  # pragma: no cover
            first_buy_exists = any(  # pragma: no cover
                position.comment == "FirstBuy"
                for position in positions  # pragma: no cover
            )  # pragma: no cover
            first_sell_exists = any(  # pragma: no cover
                position.comment == "FirstSell"
                for position in positions  # pragma: no cover
            )  # pragma: no cover
            buy_step = (  # pragma: no cover
                float(
                    self.state.get_custom("buy_hedge_distance", 0.0)
                )  # pragma: no cover
                if first_buy_exists  # pragma: no cover
                else float(
                    self.state.get_custom("sell_hedge_distance", 0.0)
                )  # pragma: no cover
            )  # pragma: no cover
            sell_step = (  # pragma: no cover
                float(
                    self.state.get_custom("sell_hedge_distance", 0.0)
                )  # pragma: no cover
                if first_sell_exists  # pragma: no cover
                else float(
                    self.state.get_custom("buy_hedge_distance", 0.0)
                )  # pragma: no cover
            )  # pragma: no cover
            if next_buy is not None:  # pragma: no cover
                intents.append(  # pragma: no cover
                    self._make_open_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        Direction.LONG,  # pragma: no cover
                        entry_type=EntryType.LIMIT,  # pragma: no cover
                        requested_quantity=volume,  # pragma: no cover
                        limit_price=float(next_buy),  # pragma: no cover
                        comment="CABuy",  # pragma: no cover
                        operation_key="create_ca_buy",  # pragma: no cover
                    )  # pragma: no cover
                )  # pragma: no cover
                self.state.set_custom(
                    "next_buy", float(next_buy) - buy_step
                )  # pragma: no cover
            if next_sell is not None:  # pragma: no cover
                intents.append(  # pragma: no cover
                    self._make_open_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        Direction.SHORT,  # pragma: no cover
                        entry_type=EntryType.LIMIT,  # pragma: no cover
                        requested_quantity=volume,  # pragma: no cover
                        limit_price=float(next_sell),  # pragma: no cover
                        comment="CASell",  # pragma: no cover
                        operation_key="create_ca_sell",  # pragma: no cover
                    )  # pragma: no cover
                )  # pragma: no cover
                self.state.set_custom(
                    "next_sell", float(next_sell) + sell_step
                )  # pragma: no cover
        if len(buys) > 1:
            intents.extend(  # pragma: no cover
                self._basket_and_cancel(
                    context, buys, Direction.LONG, pending, "CASell"
                )
            )
        if len(sells) > 1:
            intents.extend(  # pragma: no cover
                self._basket_and_cancel(
                    context, sells, Direction.SHORT, pending, "CABuy"
                )
            )
        intents.extend(self._cleanup_orphans(context, positions, pending))
        return tuple(intents)

    def _structure(self, context: MarketContext) -> tuple[bool, bool, dict[str, float]]:
        raw = context.features.get("zigzag_extremes")
        if (
            not isinstance(raw, Sequence)
            or isinstance(raw, (str, bytes))
            or len(raw) < 8
            or len(context.bars) < 2
        ):
            return False, False, {}
        values = [float(item) for item in raw[:8]]  # pragma: no cover
        if values[0] > values[1]:  # pragma: no cover
            high0, low0, high1, low1, high2, low2, high3, low3 = (
                values  # pragma: no cover
            )
        else:  # pragma: no cover
            low0, high0, low1, high1, low2, high2, low3, high3 = (
                values  # pragma: no cover
            )
        previous_close, current_close = (
            context.bars[-2].close,
            context.bars[-1].close,
        )  # pragma: no cover
        bullish = (  # pragma: no cover
            current_close > high1  # pragma: no cover
            and previous_close < high1  # pragma: no cover
            and high1 > high2  # pragma: no cover
            and high2 < high3  # pragma: no cover
            and low0 > low1  # pragma: no cover
            and low1 < low2  # pragma: no cover
        )  # pragma: no cover
        bearish = (  # pragma: no cover
            current_close < low1  # pragma: no cover
            and previous_close > low1  # pragma: no cover
            and low1 < low2  # pragma: no cover
            and low2 > low3  # pragma: no cover
            and high0 < high1  # pragma: no cover
            and high1 > high2  # pragma: no cover
        )  # pragma: no cover
        return (  # pragma: no cover
            bullish,
            bearish,
            {"high0": high0, "low0": low0, "high1": high1, "low1": low1},
        )

    def _first_bundle(
        self,
        context: MarketContext,
        direction: Direction,
        levels: dict[str, float],
        ask: float,
        bid: float,
    ) -> list[TradeIntent]:
        volume = self._volume(context)  # pragma: no cover
        displacement = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("hedge_displacement_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        factor = float(self.config.parameter("profit_factor"))  # pragma: no cover
        intents: list[TradeIntent] = []  # pragma: no cover
        if direction is Direction.LONG:  # pragma: no cover
            hedge_price = levels["low0"] - displacement  # pragma: no cover
            hedge_distance = ask - hedge_price  # pragma: no cover
            delta = hedge_distance * factor  # pragma: no cover
            intents = [  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.LONG,  # pragma: no cover
                    entry_type=EntryType.MARKET,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    protection=ProtectionRequest(
                        profit_target_price=ask + delta
                    ),  # pragma: no cover
                    comment="FirstBuy",  # pragma: no cover
                    operation_key="first_buy",  # pragma: no cover
                ),  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.SHORT,  # pragma: no cover
                    entry_type=EntryType.STOP,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    stop_price=hedge_price,  # pragma: no cover
                    protection=ProtectionRequest(  # pragma: no cover
                        profit_target_price=hedge_price - delta  # pragma: no cover
                    ),  # pragma: no cover
                    comment="HedgeSell",  # pragma: no cover
                    operation_key="hedge_sell",  # pragma: no cover
                ),  # pragma: no cover
            ]  # pragma: no cover
            self.state.set_custom("next_buy", hedge_price - delta)  # pragma: no cover
            self.state.set_custom("next_sell", ask + delta)  # pragma: no cover
            self.state.set_custom("buy_hedge_distance", delta)  # pragma: no cover
        else:  # pragma: no cover
            hedge_price = levels["high0"] + displacement  # pragma: no cover
            hedge_distance = hedge_price - bid  # pragma: no cover
            delta = hedge_distance * factor  # pragma: no cover
            intents = [  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.SHORT,  # pragma: no cover
                    entry_type=EntryType.MARKET,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    protection=ProtectionRequest(
                        profit_target_price=bid - delta
                    ),  # pragma: no cover
                    comment="FirstSell",  # pragma: no cover
                    operation_key="first_sell",  # pragma: no cover
                ),  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.LONG,  # pragma: no cover
                    entry_type=EntryType.STOP,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    stop_price=hedge_price,  # pragma: no cover
                    protection=ProtectionRequest(  # pragma: no cover
                        profit_target_price=hedge_price + delta  # pragma: no cover
                    ),  # pragma: no cover
                    comment="HedgeBuy",  # pragma: no cover
                    operation_key="hedge_buy",  # pragma: no cover
                ),  # pragma: no cover
            ]  # pragma: no cover
            self.state.set_custom("next_sell", hedge_price + delta)  # pragma: no cover
            self.state.set_custom("next_buy", bid - delta)  # pragma: no cover
            self.state.set_custom("sell_hedge_distance", delta)  # pragma: no cover
        return intents  # pragma: no cover

    def _grid_entry_intents(
        self,
        context: MarketContext,
        buys: Sequence[PositionSnapshot],
        sells: Sequence[PositionSnapshot],
        ask: float,
        bid: float,
    ) -> list[TradeIntent]:
        volume = self._volume(context)
        intents: list[TradeIntent] = []
        next_buy = self.state.get_custom("next_buy")
        next_sell = self.state.get_custom("next_sell")
        first_buy_exists = any(
            position.comment == "FirstBuy" for position in (*buys, *sells)
        )
        first_sell_exists = any(
            position.comment == "FirstSell" for position in (*buys, *sells)
        )
        buy_distance = (
            float(self.state.get_custom("buy_hedge_distance", 0.0))
            if first_buy_exists
            else float(self.state.get_custom("sell_hedge_distance", 0.0))
        )
        sell_distance = (
            float(self.state.get_custom("sell_hedge_distance", 0.0))
            if first_sell_exists
            else float(self.state.get_custom("buy_hedge_distance", 0.0))
        )
        if len(buys) > 1 and next_buy is not None and ask <= float(next_buy):
            intents.append(  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.LONG,  # pragma: no cover
                    entry_type=EntryType.MARKET,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    comment="GridBuy",  # pragma: no cover
                    operation_key=f"grid_buy_{len(buys)}",  # pragma: no cover
                )  # pragma: no cover
            )  # pragma: no cover
            if buy_distance > 0:  # pragma: no cover
                self.state.set_custom(
                    "next_buy", float(next_buy) - buy_distance
                )  # pragma: no cover
        if len(sells) > 1 and next_sell is not None and bid >= float(next_sell):
            intents.append(  # pragma: no cover
                self._make_open_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    Direction.SHORT,  # pragma: no cover
                    entry_type=EntryType.MARKET,  # pragma: no cover
                    requested_quantity=volume,  # pragma: no cover
                    comment="GridSell",  # pragma: no cover
                    operation_key=f"grid_sell_{len(sells)}",  # pragma: no cover
                )  # pragma: no cover
            )  # pragma: no cover
            if sell_distance > 0:  # pragma: no cover
                self.state.set_custom(
                    "next_sell", float(next_sell) + sell_distance
                )  # pragma: no cover
        return intents

    def _basket_and_cancel(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        pending: Sequence[PendingOrderSnapshot],
        opposite_comment: str,
    ) -> list[TradeIntent]:
        intents = [  # pragma: no cover
            self._make_modify_intent(  # pragma: no cover
                context,  # pragma: no cover
                direction,  # pragma: no cover
                tuple(
                    position.position_id for position in positions
                ),  # pragma: no cover
                ProtectionRequest(  # pragma: no cover
                    profit_target_price=arithmetic_average(  # pragma: no cover
                        [
                            entry_price(position) for position in positions
                        ]  # pragma: no cover
                    )  # pragma: no cover
                ),  # pragma: no cover
                operation_key=f"basket_tp_{direction}",  # pragma: no cover
                comment="Basket average TP",  # pragma: no cover
            )  # pragma: no cover
        ]  # pragma: no cover
        opposite = self._find_pending(pending, opposite_comment)  # pragma: no cover
        if opposite:  # pragma: no cover
            intents.append(  # pragma: no cover
                self._make_cancel_pending_intent(  # pragma: no cover
                    context,  # pragma: no cover
                    direction,  # pragma: no cover
                    tuple(order.order_id for order in opposite),  # pragma: no cover
                    operation_key=f"cancel_{opposite_comment}",  # pragma: no cover
                )  # pragma: no cover
            )  # pragma: no cover
        return intents  # pragma: no cover

    def _cleanup_orphans(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        pending: Sequence[PendingOrderSnapshot],
    ) -> list[TradeIntent]:
        intents: list[TradeIntent] = []
        comments = {position.comment for position in positions}
        for expected, direction, source in (
            ("HedgeBuy", Direction.LONG, "FirstSell"),
            ("HedgeSell", Direction.SHORT, "FirstBuy"),
        ):
            orders = self._find_pending(pending, expected)
            if orders and source not in comments:
                intents.append(  # pragma: no cover
                    self._make_cancel_pending_intent(
                        context,
                        direction,
                        tuple(order.order_id for order in orders),
                        operation_key=f"orphan_{expected}",
                    )
                )
        if not positions:
            orders = tuple(order for order in pending if "CA" in order.comment)
            if orders:
                intents.append(  # pragma: no cover
                    self._make_cancel_pending_intent(
                        context,
                        Direction.LONG,
                        tuple(order.order_id for order in orders),
                        operation_key="flat_cancel_averaging",
                    )
                )
        return intents

    @staticmethod
    def _find_pending(
        pending: Sequence[PendingOrderSnapshot], comment: str
    ) -> tuple[PendingOrderSnapshot, ...]:
        return tuple(
            order for order in pending if comment.lower() in order.comment.lower()
        )

    def _volume(self, context: MarketContext) -> float:
        if context.account is None:
            raise ValueError(
                "MarketStructureStrategy requires MarketContext.account."
            )  # pragma: no cover
        return balance_scaled_volume(
            context.account.balance,
            float(self.config.parameter("balance_increase")),
            float(self.config.parameter("volume_increase")),
            context.account,
        )
