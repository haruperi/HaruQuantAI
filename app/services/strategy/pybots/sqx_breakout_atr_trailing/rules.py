"""Pure, no-lookahead SQX-style breakout signals."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.strategy import Bar, MarketContext
    from app.services.strategy.config import StrategyConfig


def long_entry_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return opening-price break above the prior high channel after being below it."""
    return _breakout_signals(context.bars, int(config.parameter("breakout_lookback")))[
        0
    ]


def short_entry_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return opening-price break below the prior low channel after being above it."""
    return _breakout_signals(context.bars, int(config.parameter("breakout_lookback")))[
        1
    ]


def _breakout_signals(bars: Sequence[Bar], lookback: int) -> tuple[bool, bool]:
    """Calculate the current completed-bar breakout with no future data.

    The final supplied bar is the signal bar. Its open is compared only with the
    preceding `lookback` bars. The bar before it must have opened on the other side
    of its own preceding channel, which expresses the SQX `after opened below/above`
    condition without accessing an unfinished or future bar.
    """
    minimum_bars = lookback + 2
    if len(bars) < minimum_bars:
        return False, False

    signal_bar = bars[-1]
    prior_bar = bars[-2]
    signal_reference = bars[-lookback - 1 : -1]
    prior_reference = bars[-lookback - 2 : -2]

    highest_for_signal = max(bar.high for bar in signal_reference)
    lowest_for_signal = min(bar.low for bar in signal_reference)
    highest_for_prior = max(bar.high for bar in prior_reference)
    lowest_for_prior = min(bar.low for bar in prior_reference)

    long_signal = (
        signal_bar.open > highest_for_signal and prior_bar.open <= highest_for_prior
    )
    short_signal = (
        signal_bar.open < lowest_for_signal and prior_bar.open >= lowest_for_prior
    )
    return long_signal, short_signal
