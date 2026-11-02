"""Monte Carlo Retest: Randomize History Data.

Description:
    Randomizes price history data (by tick or bar) using directional
    up/down probabilities and ATR-scaled maximum price adjustments.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on historical price data.

Key Capabilities:
    - FR-mc-retest-history-data: Randomize historical prices by ATR adjustments.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_history_data import (
        RandomizeHistoryData,
    )
    retest = RandomizeHistoryData(probability_up=20, max_change_up=10)
    perturbed_bars = retest.perturb_bars(bars, rng)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeHistoryData
"""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any, override

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
    TickEvent,
)

logger = get_logger(__name__)


class RandomizeHistoryData(MonteCarloRetest):
    """Perturbs history price data using directional ATR-scaled random shifts."""

    def __init__(
        self,
        probability_up: int = 20,
        max_change_up: int = 10,
        probability_down: int = 20,
        max_change_down: int = 10,
        keep_connected: bool = True,
    ) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifyData,
            name="Randomize history data (by tick)",
        )
        self.probability_up: int = probability_up
        self.max_change_up: int = max_change_up
        self.probability_down: int = probability_down
        self.max_change_down: int = max_change_down
        self.keep_connected: bool = keep_connected
        self.last_tick: TickEvent = TickEvent()

    @override
    def modify_data(
        self, rng: random.Random, tick_event: TickEvent, global_atr: float
    ) -> None:
        """Modify tick price event data in-place."""
        up = rng.choice([True, False])
        prob = self.probability_up if up else self.probability_down
        max_chg = self.max_change_up if up else self.max_change_down

        if rng.random() * 100.0 <= prob:
            shift = (rng.uniform(0, max_chg) / 100.0) * global_atr
            if not up:
                shift = -shift
            tick_event.set_bid(tick_event.get_bid() + shift)
            tick_event.set_ask(tick_event.get_ask() + shift)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply random price shifts across bar sequence."""
        p = params or {}
        pct = float(p.get("pct", (self.max_change_up + self.max_change_down) / 200.0))
        new_bars: list[MarketBar] = []
        for b in bars:
            jitter = rng.uniform(-pct, pct) * 0.001
            new_bars.append(
                replace(
                    b,
                    open=round(b.open + jitter, 5),
                    high=round(b.high + jitter, 5),
                    low=round(b.low + jitter, 5),
                    close=round(b.close + jitter, 5),
                )
            )
        logger.info(
            "FR-mc-retest-history-data: perturbed %d bars (pct=%f)",
            len(new_bars),
            pct,
        )
        return tuple(new_bars)
