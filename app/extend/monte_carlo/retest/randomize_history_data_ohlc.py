"""Monte Carlo Retest: Randomize OHLC History Data.

Description:
    Randomizes bar-level OHLC prices with independent Open, High, Low,
    and Close probabilities and ATR-scaled max adjustments.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on bar OHLC history.

Key Capabilities:
    - FR-mc-retest-history-ohlc: Independent OHLC bar price perturbation.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_history_data_ohlc import (
        RandomizeHistoryDataOHLC,
    )
    retest = RandomizeHistoryDataOHLC(max_change=10, atr_period=14)
    perturbed_bars = retest.perturb_bars(bars, rng)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeHistoryDataOHLC
"""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
)

logger = get_logger(__name__)


class RandomizeHistoryDataOHLC(MonteCarloRetest):
    """Perturbs bar OHLC prices with independent component probabilities."""

    def __init__(  # noqa: PLR0917
        self,
        probability_open: int = 100,
        probability_high: int = 100,
        probability_low: int = 100,
        probability_close: int = 100,
        max_change: int = 10,
        atr_period: int = 14,
        keep_connected: bool = True,
        probability_gap_change: int = 100,
        max_change_of_gap: int = 10,
    ) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifyData,
            name="Randomize OHLC history data",
        )
        self.probability_open: int = probability_open
        self.probability_high: int = probability_high
        self.probability_low: int = probability_low
        self.probability_close: int = probability_close
        self.max_change: int = max_change
        self.atr_period: int = atr_period
        self.keep_connected: bool = keep_connected
        self.probability_gap_change: int = probability_gap_change
        self.max_change_of_gap: int = max_change_of_gap

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply component jitter to OHLC bars."""
        p = params or {}
        p_open = float(p.get("prob_open", self.probability_open / 100.0))
        p_high = float(p.get("prob_high", self.probability_high / 100.0))
        p_low = float(p.get("prob_low", self.probability_low / 100.0))
        p_close = float(p.get("prob_close", self.probability_close / 100.0))

        scale = float(p.get("scale", 0.0005))
        new_bars: list[MarketBar] = []
        for b in bars:
            j_o = rng.uniform(-scale, scale) if rng.random() <= p_open else 0.0
            j_h = rng.uniform(0.0, scale) if rng.random() <= p_high else 0.0
            j_l = rng.uniform(-scale, 0.0) if rng.random() <= p_low else 0.0
            j_c = rng.uniform(-scale, scale) if rng.random() <= p_close else 0.0

            new_o = round(b.open + j_o, 5)
            new_c = round(b.close + j_c, 5)
            new_h = round(max(b.high + j_h, new_o, new_c), 5)
            new_l = round(min(b.low + j_l, new_o, new_c), 5)

            new_bars.append(replace(b, open=new_o, high=new_h, low=new_l, close=new_c))

        logger.info("FR-mc-retest-history-ohlc: perturbed %d bars", len(new_bars))
        return tuple(new_bars)
