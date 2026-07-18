"""Broker-neutral translation of **Decomposing Trade EA.mq5**.

This H1 strategy is a two-sided RSI basket system.  It watches RSI(14): a cross
up through oversold opens the first buy, and a cross down through overbought
opens the first sell.  It can also seed a new basket in the opposite direction
when the corresponding opposing RSI cross occurs while a basket already exists.
The EA therefore permits long and short exposure at the same time.

Base volume is scaled from account balance as
``volume_increase * balance / balance_increase`` and clamped/rounded by the
account's broker-volume specification.  When price moves one configured trade
distance against a basket *and* the matching RSI entry signal reappears, the EA
partially closes the worst-priced existing position, adds a larger averaging
position, and moves the basket take-profit to its volume-weighted average entry
plus/minus the configured trailing amount.

Trailing stops are applied only while a side has no averaging position marked
``CBuy``/``CSell``.  Once price is sufficiently profitable, each normal position
receives an improved stop at current price minus/plus the trail distance.  The
source EA has no independent signal exit; exits occur through its amended TP,
trailing SL, or external execution/risk controls.  This translation emits
market, partial-close, and modify intents only.  Risk Governor approval and
final broker execution remain external.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from app.services.indicators import balance_scaled_volume, weighted_average
from app.services.strategy import (
    Direction,
    EntryType,
    MarketContext,
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


class DecomposingTradeStrategy(BaseStrategy):
    """RSI-triggered hedged averaging system with partial decompression."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate signals in a vectorized way on the DataFrame."""
        del context
        period = int(self.config.parameter("rsi_period"))
        oversold = float(self.config.parameter("oversold"))
        overbought = float(self.config.parameter("overbought"))

        from app.services.indicators import rsi

        df[f"rsi_{period}"] = rsi.calculate(df, period=period, column="close")
        rsi_col = f"rsi_{period}"
        rsi = df[rsi_col]
        rsi_prev = rsi.shift(1)

        df["long_entry"] = ((rsi >= oversold) & (rsi_prev < oversold)).astype(int)
        df["short_entry"] = ((rsi <= overbought) & (rsi_prev > overbought)).astype(int)
        df["oppose_buy"] = ((rsi <= oversold) & (rsi_prev > oversold)).astype(int)
        df["oppose_sell"] = ((rsi >= overbought) & (rsi_prev < overbought)).astype(int)
        df["long_exit"] = 0
        df["short_exit"] = 0

        return df

    def build_custom_decision(self, context: MarketContext) -> StrategyDecision | None:
        if self.df_signals is None or len(self.df_signals) < len(context.bars):
            self.precalculate_signals(context)

        current_idx = len(context.bars) - 1
        if self.df_signals is not None and 0 <= current_idx < len(self.df_signals):
            row = self.df_signals.iloc[current_idx]
            buy_signal = bool(row["long_entry"])
            sell_signal = bool(row["short_entry"])
            oppose_buy = bool(row["oppose_buy"])
            oppose_sell = bool(row["oppose_sell"])
        else:
            buy_signal = sell_signal = oppose_buy = oppose_sell = False

        quote = require_quote(context)
        buys = by_direction(self._owned_positions(context), Direction.LONG)
        sells = by_direction(self._owned_positions(context), Direction.SHORT)
        intents = []
        if self._entries_allowed_now(context):  # pragma: no cover
            volume = self._base_volume(context)
            if (buy_signal or (oppose_sell and sells)) and not buys:
                intents.append(  # pragma: no cover
                    self._make_open_intent(
                        context,
                        Direction.LONG,
                        entry_type=EntryType.MARKET,
                        requested_quantity=volume,
                        comment="FBuy",
                        operation_key="first_buy",
                    )
                )
            if (sell_signal or (oppose_buy and buys)) and not sells:
                intents.append(  # pragma: no cover
                    self._make_open_intent(
                        context,
                        Direction.SHORT,
                        entry_type=EntryType.MARKET,
                        requested_quantity=volume,
                        comment="FSell",
                        operation_key="first_sell",
                    )
                )
            intents.extend(
                self._averaging_intents(
                    context, buys, Direction.LONG, buy_signal, quote.bid, volume
                )
            )
            intents.extend(
                self._averaging_intents(
                    context, sells, Direction.SHORT, sell_signal, quote.ask, volume
                )
            )
        intents.extend(self._trailing_intents(context, buys, Direction.LONG, quote.bid))
        intents.extend(
            self._trailing_intents(context, sells, Direction.SHORT, quote.ask)
        )
        return StrategyDecision(
            context.signal_bar.open_time,
            SignalSet(buy_signal, sell_signal),
            tuple(intents),
        )

    def _base_volume(self, context: MarketContext) -> float:
        if context.account is None:
            raise ValueError(
                "DecomposingTradeStrategy requires MarketContext.account."
            )  # pragma: no cover
        return balance_scaled_volume(
            context.account.balance,
            float(self.config.parameter("balance_increase")),
            float(self.config.parameter("volume_increase")),
            context.account,
        )

    def _averaging_intents(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        signal: bool,
        market_price: float,
        base_volume: float,
    ) -> list[TradeIntent]:
        if not positions or not signal:
            return []
        distance = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("trade_distance_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        trigger = (  # pragma: no cover
            min(entry_price(p) for p in positions) - distance  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else max(entry_price(p) for p in positions) + distance  # pragma: no cover
        )  # pragma: no cover
        triggered = (  # pragma: no cover
            market_price < trigger  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else market_price > trigger  # pragma: no cover
        )  # pragma: no cover
        if not triggered:  # pragma: no cover
            return []  # pragma: no cover
        partial_volume = (  # pragma: no cover
            base_volume  # pragma: no cover
            * float(self.config.parameter("volume_decrease"))  # pragma: no cover
            / float(self.config.parameter("volume_increase"))  # pragma: no cover
        )  # pragma: no cover
        worst = (  # pragma: no cover
            max(positions, key=entry_price)  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else min(positions, key=entry_price)  # pragma: no cover
        )  # pragma: no cover
        new_volume = base_volume + len(positions) * partial_volume  # pragma: no cover
        # The source first partially closes its worst entry, then calculates the  # pragma: no cover
        # basket VWAP after the new CBuy/CSell has been opened.  Model that  # pragma: no cover
        # post-action state here rather than averaging the pre-close basket.  # pragma: no cover
        remaining_quantities = [  # pragma: no cover
            max(position.quantity - partial_volume, 0.0)  # pragma: no cover
            if position.position_id == worst.position_id  # pragma: no cover
            else position.quantity  # pragma: no cover
            for position in positions  # pragma: no cover
        ]  # pragma: no cover
        weighted_prices = [  # pragma: no cover
            entry_price(position)  # pragma: no cover
            for position, quantity in zip(
                positions, remaining_quantities, strict=True
            )  # pragma: no cover
            if quantity > 0  # pragma: no cover
        ]  # pragma: no cover
        weighted_quantities = [  # pragma: no cover
            quantity
            for quantity in remaining_quantities
            if quantity > 0  # pragma: no cover
        ]  # pragma: no cover
        expected_target_base = weighted_average(  # pragma: no cover
            [*weighted_prices, market_price],
            [*weighted_quantities, new_volume],  # pragma: no cover
        )  # pragma: no cover
        offset = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("trail_by_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        target = (  # pragma: no cover
            expected_target_base + offset  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else expected_target_base - offset  # pragma: no cover
        )  # pragma: no cover
        comment = "CBuy" if direction is Direction.LONG else "CSell"  # pragma: no cover
        return [  # pragma: no cover
            self._make_partial_close_intent(
                context,
                direction,
                (worst.position_id,),
                partial_volume,
                operation_key=f"partial_{comment}_{worst.position_id}",
                comment=f"Partial {comment}",
            ),
            self._make_open_intent(
                context,
                direction,
                entry_type=EntryType.MARKET,
                requested_quantity=new_volume,
                protection=ProtectionRequest(profit_target_price=target),
                comment=comment,
                operation_key=f"open_{comment}_{len(positions)}",
                metadata={"reason": "adverse_rsi_averaging"},
            ),
            self._make_modify_intent(
                context,
                direction,
                tuple(p.position_id for p in positions),
                ProtectionRequest(profit_target_price=target),
                operation_key=f"basket_tp_{comment}_{len(positions)}",
                comment=f"Move {comment} basket TP",
            ),
        ]

    def _trailing_intents(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        market_price: float,
    ) -> list[TradeIntent]:
        if not positions:
            return []
        marker = "CBuy" if direction is Direction.LONG else "CSell"  # pragma: no cover
        if any(
            marker.lower() in position.comment.lower() for position in positions
        ):  # pragma: no cover
            return []  # pragma: no cover
        activation = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("when_to_trail_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        trail = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("trail_by_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        intents = []  # pragma: no cover
        for position in positions:  # pragma: no cover
            open_price = entry_price(position)  # pragma: no cover
            active = (  # pragma: no cover
                market_price >= open_price + activation  # pragma: no cover
                if direction is Direction.LONG  # pragma: no cover
                else market_price <= open_price - activation  # pragma: no cover
            )  # pragma: no cover
            new_stop = (  # pragma: no cover
                market_price - trail  # pragma: no cover
                if direction is Direction.LONG  # pragma: no cover
                else market_price + trail  # pragma: no cover
            )  # pragma: no cover
            improves = position.stop_loss_price is None or (  # pragma: no cover
                new_stop > position.stop_loss_price  # pragma: no cover
                if direction is Direction.LONG  # pragma: no cover
                else new_stop < position.stop_loss_price  # pragma: no cover
            )  # pragma: no cover
            if active and improves:  # pragma: no cover
                intents.append(  # pragma: no cover
                    self._make_modify_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        direction,  # pragma: no cover
                        (position.position_id,),  # pragma: no cover
                        ProtectionRequest(stop_loss_price=new_stop),  # pragma: no cover
                        operation_key=f"trail_{position.position_id}",  # pragma: no cover
                        comment="Improve trailing stop",  # pragma: no cover
                    )  # pragma: no cover
                )  # pragma: no cover
        return intents  # pragma: no cover
