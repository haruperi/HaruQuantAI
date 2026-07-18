"""Broker-neutral translation of **RandomWalk EA.mq5**.

Despite its name, the source Expert Advisor does not generate a random walk and
contains no market-direction signal.  On each new M5 bar, it checks two separate
magic-number portfolios.  If no long position exists under the buy magic number,
it creates a complete long basket.  If no short position exists under the sell
magic number, it creates a complete short basket.  Therefore a flat account
starts both baskets at once and remains deliberately hedged.

The number of orders is ``round(total_volume / volume_per_trade)``.  Each order
uses the same volume but a progressively wider protective ladder: the first
long uses SL = ask − 1 × stop-loss pips and TP = ask + 1 × take-profit pips;
the nth long uses n times each distance.  Shorts mirror those prices around
bid.  Orders are tagged Buy1 … BuyN and Sell1 … SellN and retain the separate
MQL magic numbers.  There are no signal exits, averaging rules, or randomness.
Broker fills, stops, targets, and the Risk Governor determine the eventual
lifecycle of each layer.
"""

from __future__ import annotations

import pandas as pd

from app.services.strategy import (
    Direction,
    EntryType,
    MarketContext,
    ProtectionRequest,
    SignalSet,
    StrategyDecision,
)
from app.services.strategy.base import BaseStrategy
from app.services.strategy.pybots.mql5_translation_helpers import require_quote


class RandomWalkStrategy(BaseStrategy):
    """Dual fixed-size long/short basket launcher with layered SL and TP prices."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """The original EA has no directional signal calculation."""
        del context
        df["long_entry"] = 0
        df["short_entry"] = 0
        df["long_exit"] = 0
        df["short_exit"] = 0
        return df

    def build_custom_decision(self, context: MarketContext) -> StrategyDecision | None:
        quote = require_quote(context)
        buy_magic = int(self.config.parameter("buy_magic_number"))
        sell_magic = int(self.config.parameter("sell_magic_number"))
        positions = context.positions
        has_buys = any(
            position.symbol == context.symbol and position.magic_number == buy_magic
            for position in positions
        )
        has_sells = any(
            position.symbol == context.symbol and position.magic_number == sell_magic
            for position in positions
        )
        count = round(
            float(self.config.parameter("total_volume"))
            / float(self.config.parameter("volume_per_trade"))
        )
        volume = float(self.config.parameter("volume_per_trade"))
        multiplier = float(self.config.parameter("pip_multiplier"))
        stop_distance = (
            float(self.config.parameter("stop_loss_pips"))
            * quote.point_size
            * multiplier
        )
        target_distance = (
            float(self.config.parameter("take_profit_pips"))
            * quote.point_size
            * multiplier
        )
        intents = []
        if self._entries_allowed_now(context) and not has_buys:
            for number in range(1, count + 1):
                intents.append(
                    self._make_open_intent(
                        context,
                        Direction.LONG,
                        entry_type=EntryType.MARKET,
                        requested_quantity=volume,
                        protection=ProtectionRequest(
                            stop_loss_price=quote.ask - stop_distance * number,
                            profit_target_price=quote.ask + target_distance * number,
                        ),
                        comment=f"Buy{number}",
                        magic_number=buy_magic,
                        operation_key=f"buy_layer_{number}",
                        metadata={"layer": number, "source": "RandomWalk EA"},
                    )
                )
        if self._entries_allowed_now(context) and not has_sells:
            for number in range(1, count + 1):
                intents.append(
                    self._make_open_intent(
                        context,
                        Direction.SHORT,
                        entry_type=EntryType.MARKET,
                        requested_quantity=volume,
                        protection=ProtectionRequest(
                            stop_loss_price=quote.bid + stop_distance * number,
                            profit_target_price=quote.bid - target_distance * number,
                        ),
                        comment=f"Sell{number}",
                        magic_number=sell_magic,
                        operation_key=f"sell_layer_{number}",
                        metadata={"layer": number, "source": "RandomWalk EA"},
                    )
                )
        return StrategyDecision(
            context.signal_bar.open_time, SignalSet(), tuple(intents)
        )
