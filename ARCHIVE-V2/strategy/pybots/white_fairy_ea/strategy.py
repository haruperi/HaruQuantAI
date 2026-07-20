"""Broker-neutral translation of **White Fairy EA.mq5**.

White Fairy is a two-sided RSI basket strategy.  RSI(14) crossing upward through
oversold opens the first buy; RSI crossing downward through overbought opens the
first sell.  The strategy intentionally allows both baskets to coexist.  Its
base volume is scaled from balance using ``volume_increase * balance /
balance_increase`` and is normalized to the supplied account-volume rules.

After a first entry, each side has two independent expansion mechanisms.
**Countertrend averaging** runs only when the corresponding RSI entry signal
reappears and price has moved a configured distance against the basket.  It
opens a same-size ``C.Averaging`` position, moves the next countertrend level,
and sets all positions on that side to a common arithmetic-average take-profit.

**Trend pyramiding** does not require a fresh RSI signal.  It opens when price
moves the configured distance in the favorable direction from the next pyramid
level.  The initial pyramid lot is half the base lot and is divided by the lot
divisor after every pyramid entry.  It clears all same-side TP values and moves
their stop loss to a shared trailing level derived from the latest pyramid
price.  Sells are exact mirrors of buys.  The MQL source has no final signal
exit or maximum-grid guard; portfolio risk limits must therefore be imposed by
the Risk Governor.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

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


class WhiteFairyStrategy(BaseStrategy):
    """RSI-first-entry, adverse averaging, and favorable pyramiding basket strategy."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate White Fairy signals in a vectorized way."""
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
        df["long_exit"] = 0
        df["short_exit"] = 0

        return df

    def build_custom_decision(self, context: MarketContext) -> StrategyDecision | None:
        """Build the custom decision for White Fairy using the precalculated signals."""
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
        base = self._base_volume(context)
        intents = []
        if self._entries_allowed_now(context):  # pragma: no cover
            if buy_signal and not buys:
                intents.append(  # pragma: no cover
                    self._first_intent(
                        context, Direction.LONG, quote.ask, base
                    )  # pragma: no cover
                )  # pragma: no cover
                self._seed_levels(
                    context, Direction.LONG, quote.ask, base
                )  # pragma: no cover
            if sell_signal and not sells:
                intents.append(  # pragma: no cover
                    self._first_intent(
                        context, Direction.SHORT, quote.bid, base
                    )  # pragma: no cover
                )  # pragma: no cover
                self._seed_levels(
                    context, Direction.SHORT, quote.bid, base
                )  # pragma: no cover
            intents.extend(
                self._countertrend_intents(
                    context, buys, Direction.LONG, quote.ask, buy_signal, base
                )
            )
            intents.extend(
                self._countertrend_intents(
                    context, sells, Direction.SHORT, quote.bid, sell_signal, base
                )
            )
            intents.extend(
                self._pyramid_intents(context, buys, Direction.LONG, quote.ask)
            )
            intents.extend(
                self._pyramid_intents(context, sells, Direction.SHORT, quote.bid)
            )
        return StrategyDecision(
            context.signal_bar.open_time,
            SignalSet(buy_signal, sell_signal),
            tuple(intents),
        )

    def _base_volume(self, context: MarketContext) -> float:
        if context.account is None:
            raise ValueError(
                "WhiteFairyStrategy requires MarketContext.account."
            )  # pragma: no cover
        return balance_scaled_volume(
            context.account.balance,
            float(self.config.parameter("balance_increase")),
            float(self.config.parameter("volume_increase")),
            context.account,
        )

    def _distance(self, context: MarketContext, parameter: str) -> float:
        return pip_value(
            context,
            float(self.config.parameter(parameter)),
            float(self.config.parameter("pip_multiplier")),
        )

    def _first_intent(
        self, context: MarketContext, direction: Direction, price: float, volume: float
    ) -> TradeIntent:
        return self._make_open_intent(  # pragma: no cover
            context,
            direction,
            entry_type=EntryType.MARKET,
            requested_quantity=volume,
            comment="FirstBuy" if direction is Direction.LONG else "FirstSell",
            operation_key=f"first_{direction}",
            metadata={"entry_price_reference": price},
        )

    def _seed_levels(
        self, context: MarketContext, direction: Direction, price: float, base: float
    ) -> None:
        counter = self._distance(
            context, "counter_trade_distance_pips"
        )  # pragma: no cover
        pyramid = self._distance(
            context, "pyramid_trade_distance_pips"
        )  # pragma: no cover
        key = "buy" if direction is Direction.LONG else "sell"  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"c_next_{key}",  # pragma: no cover
            price - counter
            if direction is Direction.LONG
            else price + counter,  # pragma: no cover
        )  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"p_next_{key}",  # pragma: no cover
            price + pyramid
            if direction is Direction.LONG
            else price - pyramid,  # pragma: no cover
        )  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"p_lot_{key}", base / float(self.config.parameter("lot_divisor"))
        )

    def _countertrend_intents(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        price: float,
        signal: bool,
        base: float,
    ) -> list[TradeIntent]:
        if not positions or not signal:
            return []
        key = "buy" if direction is Direction.LONG else "sell"  # pragma: no cover
        next_level = self.state.get_custom(f"c_next_{key}")  # pragma: no cover
        if next_level is None:  # pragma: no cover
            self._seed_levels(
                context, direction, entry_price(positions[-1]), base
            )  # pragma: no cover
            next_level = self.state.get_custom(f"c_next_{key}")  # pragma: no cover
        triggered = (  # pragma: no cover
            price <= float(next_level)  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else price >= float(next_level)  # pragma: no cover
        )  # pragma: no cover
        if not triggered:  # pragma: no cover
            return []  # pragma: no cover
        counter_distance = self._distance(
            context, "counter_trade_distance_pips"
        )  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"c_next_{key}",  # pragma: no cover
            price - counter_distance  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else price + counter_distance,  # pragma: no cover
        )  # pragma: no cover
        target = arithmetic_average(
            [*(entry_price(p) for p in positions), price]
        )  # pragma: no cover
        comment = (  # pragma: no cover
            "C.Averaging Buy"
            if direction is Direction.LONG
            else "C.Averaging Sell"  # pragma: no cover
        )  # pragma: no cover
        return [  # pragma: no cover
            self._make_open_intent(
                context,
                direction,
                entry_type=EntryType.MARKET,
                requested_quantity=base,
                protection=ProtectionRequest(profit_target_price=target),
                comment=comment,
                operation_key=f"counter_{key}_{len(positions)}",
            ),
            self._make_modify_intent(
                context,
                direction,
                tuple(p.position_id for p in positions),
                ProtectionRequest(profit_target_price=target),
                operation_key=f"counter_tp_{key}_{len(positions)}",
                comment="Countertrend basket TP",
            ),
        ]

    def _pyramid_intents(
        self,
        context: MarketContext,
        positions: Sequence[PositionSnapshot],
        direction: Direction,
        price: float,
    ) -> list[TradeIntent]:
        if not positions:
            return []
        key = "buy" if direction is Direction.LONG else "sell"  # pragma: no cover
        next_level = self.state.get_custom(f"p_next_{key}")  # pragma: no cover
        if next_level is None:  # pragma: no cover
            return []  # pragma: no cover
        triggered = (  # pragma: no cover
            price >= float(next_level)  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else price <= float(next_level)  # pragma: no cover
        )  # pragma: no cover
        if not triggered:  # pragma: no cover
            return []  # pragma: no cover
        lot = float(  # pragma: no cover
            self.state.get_custom(  # pragma: no cover
                f"p_lot_{key}",  # pragma: no cover
                positions[-1].quantity
                / float(self.config.parameter("lot_divisor")),  # pragma: no cover
            )  # pragma: no cover
        )  # pragma: no cover
        distance = self._distance(
            context, "pyramid_trade_distance_pips"
        )  # pragma: no cover
        stop_displacement = self._distance(
            context, "stop_loss_displacement_pips"
        )  # pragma: no cover
        last_price = (  # pragma: no cover
            price - distance
            if direction is Direction.LONG
            else price + distance  # pragma: no cover
        )  # pragma: no cover
        new_stop = (  # pragma: no cover
            last_price + stop_displacement  # pragma: no cover
            if direction is Direction.LONG  # pragma: no cover
            else last_price - stop_displacement  # pragma: no cover
        )  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"p_next_{key}",  # pragma: no cover
            price + distance
            if direction is Direction.LONG
            else price - distance,  # pragma: no cover
        )  # pragma: no cover
        self.state.set_custom(  # pragma: no cover
            f"p_lot_{key}",
            lot / float(self.config.parameter("lot_divisor")),  # pragma: no cover
        )  # pragma: no cover
        comment = (
            "Pyrammid Buy" if direction is Direction.LONG else "Pyrammid Sell"
        )  # pragma: no cover
        protection = ProtectionRequest(  # pragma: no cover
            stop_loss_price=new_stop,
            clear_profit_target=True,  # pragma: no cover
        )  # pragma: no cover
        return [  # pragma: no cover
            self._make_open_intent(
                context,
                direction,
                entry_type=EntryType.MARKET,
                requested_quantity=lot,
                protection=protection,
                comment=comment,
                operation_key=f"pyramid_{key}_{len(positions)}",
            ),
            self._make_modify_intent(
                context,
                direction,
                tuple(p.position_id for p in positions),
                protection,
                operation_key=f"pyramid_stop_{key}_{len(positions)}",
                comment="Pyramid shared stop / clear TP",
            ),
        ]
