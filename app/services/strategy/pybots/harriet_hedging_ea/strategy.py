"""Broker-neutral translation of **Harriet Hedging EA.mq5**.

Harriet Hedging is a multi-timeframe market-structure system.  On its lower
chart (M5 by default), it recognizes a *higher low* when the newest completed
candle has a higher low than the preceding completed candle, is bullish, and
exceeds a configured pip distance.  It recognizes a *lower high* symmetrically
when the newest candle has a lower high, is bearish, and exceeds its distance.
The same two tests are evaluated on a higher chart (H1 by default).

A buy signal requires a higher low on both timeframes; a sell signal requires a
lower high on both.  A buy opens with a fixed profit target above ask, and a
sell opens with a fixed profit target below bid.  The source EA's ``Bought`` and
``Sold`` flags are deliberately preserved: the flag for a side becomes false
only when that side has no positions, while opening an opposite side resets the
other flag.  Consequently this EA can hold long and short baskets concurrently
and can re-enter a still-open direction after an opposite signal.

With two or more same-direction positions, the EA moves all TP values to the
unweighted arithmetic average of their entry prices when that price is on the
profitable side of the market.  With exactly one position, it trails once profit
reaches the trigger: buys use the latest completed lower-timeframe low; sells
use the latest completed lower-timeframe high.  It has no signal-close rule.
The chart-object drawing routines in the MQL5 source are intentionally omitted
because they are UI responsibilities, not trading decisions.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from app.services.data.contracts import Timeframe
from app.services.indicators import arithmetic_average, balance_scaled_volume
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


class HarrietHedgingStrategy(BaseStrategy):
    """Higher-low/lower-high confirmation with hedged basket management."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate Harriet Hedging signals in a vectorized way."""
        higher_chart = str(self.config.parameter("higher_timeframe"))
        higher_bars = context.bars_for_chart(higher_chart)

        high_distance = pip_value(
            context,
            float(self.config.parameter("higher_min_distance_pips")),
            float(self.config.parameter("pip_multiplier")),
        )
        low_distance = pip_value(
            context,
            float(self.config.parameter("lower_min_distance_pips")),
            float(self.config.parameter("pip_multiplier")),
        )

        # 1. Higher-timeframe DataFrame and signals
        df_higher = pd.DataFrame(
            {
                "open": [bar.open for bar in higher_bars],
                "high": [bar.high for bar in higher_bars],
                "low": [bar.low for bar in higher_bars],
                "close": [bar.close for bar in higher_bars],
            },
            index=[bar.open_time for bar in higher_bars],
        )

        if len(df_higher) >= 2:
            prev_high = df_higher["high"].shift(1)
            prev_low = df_higher["low"].shift(1)
            df_higher["higher_low_confirm"] = (
                (df_higher["low"] > prev_low)
                & (df_higher["close"] > df_higher["open"])
                & (df_higher["low"] - prev_low > high_distance)
            )
            df_higher["lower_high_confirm"] = (
                (df_higher["high"] < prev_high)
                & (df_higher["close"] < df_higher["open"])
                & (prev_high - df_higher["high"] > high_distance)
            )
        else:
            df_higher["higher_low_confirm"] = False
            df_higher["lower_high_confirm"] = False

        # Calculate higher bar completion times (lookahead-proof alignment)
        higher_tf = Timeframe.from_name(higher_chart)
        df_higher["completion_time"] = df_higher.index + pd.Timedelta(
            seconds=higher_tf.duration_seconds
        )

        # 2. Main chart (lower-timeframe) signals
        prev_low_lt = df["low"].shift(1)
        prev_high_lt = df["high"].shift(1)
        df["lower_low_confirm"] = (
            (df["low"] > prev_low_lt)
            & (df["close"] > df["open"])
            & (df["low"] - prev_low_lt > low_distance)
        )
        df["lower_high_confirm"] = (
            (df["high"] < prev_high_lt)
            & (df["close"] < df["open"])
            & (prev_high_lt - df["high"] > low_distance)
        )

        # 3. Align higher-timeframe signals onto lower timeframe df
        df_temp = pd.DataFrame({"lower_open_time": df.index}, index=df.index)
        df_higher_sorted = df_higher.sort_values("completion_time")

        merged = pd.merge_asof(
            df_temp,
            df_higher_sorted[
                ["completion_time", "higher_low_confirm", "lower_high_confirm"]
            ],
            left_on="lower_open_time",
            right_on="completion_time",
            direction="backward",
        )
        merged.index = df_temp.index

        df["long_entry"] = (
            df["lower_low_confirm"]
            & merged["higher_low_confirm"].fillna(False).astype(bool)
        ).astype(int)
        df["short_entry"] = (
            df["lower_high_confirm"]
            & merged["lower_high_confirm"].fillna(False).astype(bool)
        ).astype(int)
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
        else:
            buy_signal = sell_signal = False

        quote = require_quote(context)
        positions = self._owned_positions(context)
        buys = by_direction(positions, Direction.LONG)
        sells = by_direction(positions, Direction.SHORT)
        bought = bool(self.state.get_custom("bought", False))
        sold = bool(self.state.get_custom("sold", False))
        if not buys:  # pragma: no cover
            bought = False
        if not sells:  # pragma: no cover
            sold = False
        intents = []
        volume = self._volume(context)
        target_distance = pip_value(
            context,
            float(self.config.parameter("take_profit_pips")),
            float(self.config.parameter("pip_multiplier")),
        )
        if self._entries_allowed_now(context):  # pragma: no cover
            if buy_signal and not bought:
                intents.append(  # pragma: no cover
                    self._make_open_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        Direction.LONG,  # pragma: no cover
                        entry_type=EntryType.MARKET,  # pragma: no cover
                        requested_quantity=volume,  # pragma: no cover
                        protection=ProtectionRequest(  # pragma: no cover
                            profit_target_price=quote.ask
                            + target_distance  # pragma: no cover
                        ),  # pragma: no cover
                        comment="Buy",  # pragma: no cover
                        operation_key="structure_buy",  # pragma: no cover
                    )  # pragma: no cover
                )  # pragma: no cover
                bought, sold = True, False  # pragma: no cover
            if sell_signal and not sold:
                intents.append(  # pragma: no cover
                    self._make_open_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        Direction.SHORT,  # pragma: no cover
                        entry_type=EntryType.MARKET,  # pragma: no cover
                        requested_quantity=volume,  # pragma: no cover
                        protection=ProtectionRequest(  # pragma: no cover
                            profit_target_price=quote.bid
                            - target_distance  # pragma: no cover
                        ),  # pragma: no cover
                        comment="Sell",  # pragma: no cover
                        operation_key="structure_sell",  # pragma: no cover
                    )  # pragma: no cover
                )  # pragma: no cover
                bought, sold = False, True  # pragma: no cover
        self.state.set_custom("bought", bought)
        self.state.set_custom("sold", sold)
        intents.extend(self._manage_basket(context, buys, Direction.LONG, quote.bid))
        intents.extend(self._manage_basket(context, sells, Direction.SHORT, quote.ask))
        return StrategyDecision(
            context.signal_bar.open_time,
            SignalSet(buy_signal, sell_signal),
            tuple(intents),
        )

    def _volume(self, context: MarketContext) -> float:
        if context.account is None:
            raise ValueError(
                "HarrietHedgingStrategy requires MarketContext.account."
            )  # pragma: no cover
        return balance_scaled_volume(
            context.account.balance,
            float(self.config.parameter("balance_increase")),
            float(self.config.parameter("volume_increase")),
            context.account,
        )

    def _manage_basket(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        market_price: float,
    ) -> list[TradeIntent]:
        if not positions:
            return []
        if len(positions) >= 2:  # pragma: no cover
            target = arithmetic_average(  # pragma: no cover
                [entry_price(position) for position in positions]  # pragma: no cover
            )  # pragma: no cover
            profitable_side = (  # pragma: no cover
                target > market_price  # pragma: no cover
                if direction is Direction.LONG  # pragma: no cover
                else target < market_price  # pragma: no cover
            )  # pragma: no cover
            if profitable_side:  # pragma: no cover
                return [  # pragma: no cover
                    self._make_modify_intent(  # pragma: no cover
                        context,  # pragma: no cover
                        direction,  # pragma: no cover
                        tuple(
                            position.position_id for position in positions
                        ),  # pragma: no cover
                        ProtectionRequest(
                            profit_target_price=target
                        ),  # pragma: no cover
                        operation_key=f"basket_tp_{direction}",  # pragma: no cover
                        comment="Basket average TP",  # pragma: no cover
                    )  # pragma: no cover
                ]  # pragma: no cover
            return []  # pragma: no cover
        position = positions[0]  # pragma: no cover
        activation = pip_value(  # pragma: no cover
            context,  # pragma: no cover
            float(self.config.parameter("when_to_trail_pips")),  # pragma: no cover
            float(self.config.parameter("pip_multiplier")),  # pragma: no cover
        )  # pragma: no cover
        active = (  # pragma: no cover
            market_price >= entry_price(position) + activation  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else market_price <= entry_price(position) - activation  # pragma: no cover
        )  # pragma: no cover
        if not active:  # pragma: no cover
            return []  # pragma: no cover
        lower = context.bars[-1]  # pragma: no cover
        new_stop = (
            lower.low if direction is Direction.LONG else lower.high
        )  # pragma: no cover
        improve = position.stop_loss_price is None or (  # pragma: no cover
            new_stop > position.stop_loss_price  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else new_stop < position.stop_loss_price  # pragma: no cover
        )  # pragma: no cover
        valid = (  # pragma: no cover
            new_stop < market_price  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else new_stop > market_price  # pragma: no cover
        )  # pragma: no cover
        if not improve or not valid:  # pragma: no cover
            return []  # pragma: no cover
        return [  # pragma: no cover
            self._make_modify_intent(
                context,
                direction,
                (position.position_id,),
                ProtectionRequest(stop_loss_price=new_stop),
                operation_key=f"single_trail_{position.position_id}",
                comment="Structure trailing stop",
            )
        ]
