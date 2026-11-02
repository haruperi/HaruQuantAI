"""Monte Carlo Retest: Randomize History Data (Fixed Range).

Description:
    Randomizes price history data using fixed-range percentage of tick
    or bar price movements to allow price to wander away from original data.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation with fixed range data shifts.

Key Capabilities:
    - FR-mc-retest-history-fixed-range: Fixed-range price data randomization.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_history_data_fixed_range import (
        RandomizeHistoryDataFixedRange,
    )
    retest = RandomizeHistoryDataFixedRange(max_change=40)
    perturbed_bars = retest.perturb_bars(bars, rng)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeHistoryDataFixedRange
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


class RandomizeHistoryDataFixedRange(MonteCarloRetest):
    """Perturbs price history with fixed-range offsets based on tick movements."""

    def __init__(self, max_change: int = 40) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifyData,
            name="Randomize history data (by tick, fixed range)",
        )
        self.max_change: int = max_change
        self.last_bid: float = 0.0
        self.last_org_bid: float = 0.0
        self.last_tick_time: int = 0

    @override
    def modify_data(
        self, rng: random.Random, tick_event: TickEvent, global_atr: float
    ) -> None:
        """Modify tick price event data in-place."""
        del global_atr
        bid = tick_event.get_bid()
        curr_time = tick_event.get_time()
        if self.last_tick_time <= curr_time and self.last_tick_time != 0:
            tick_org_change = bid - self.last_org_bid
        else:
            self.last_bid = bid
            tick_org_change = 0.0

        self.last_org_bid = bid
        self.last_tick_time = curr_time

        effective_max = max(1, self.max_change)
        change_pct = (rng.randint(0, effective_max) / 100.0) * 0.01
        offset = tick_org_change * change_pct
        tick_event.set_bid(bid + offset)
        tick_event.set_ask(tick_event.get_ask() + offset)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply fixed pip/range offsets across bars."""
        p = params or {}
        max_pips = float(p.get("max_pips", float(self.max_change) / 10.0))
        new_bars: list[MarketBar] = []
        for b in bars:
            offset = rng.uniform(-max_pips, max_pips) * 0.0001
            new_bars.append(
                replace(
                    b,
                    open=round(b.open + offset, 5),
                    high=round(b.high + offset, 5),
                    low=round(b.low + offset, 5),
                    close=round(b.close + offset, 5),
                )
            )
        logger.info(
            "FR-mc-retest-history-fixed-range: perturbed %d bars (max_pips=%f)",
            len(new_bars),
            max_pips,
        )
        return tuple(new_bars)
