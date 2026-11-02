"""Unit tests for Monte Carlo manipulation methods."""

from typing import override

from app.extend.monte_carlo.manipulation import (
    MACHRBlockRandomization,
    RandomizeTradesOrder,
    RandomlyDegradeExecution,
    SimulateParameterJitter,
    SkipRandom,
)
from app.extend.what_if.base import WhatIfRecord


class QueueRng(SkipRandom):
    """Deterministic queued RNG."""

    def __init__(self, draws: list[int]) -> None:
        self.draws = list(draws)

    @override
    def next_index(self, upper_exclusive: int) -> int:
        if not self.draws:
            return 0
        return self.draws.pop(0)


def _make_record(
    record_id: int, profit: float = 100.0, kind: str = "trade"
) -> WhatIfRecord:
    return WhatIfRecord(
        record_id=record_id,
        kind=kind,  # type: ignore[arg-type]
        symbol="EURUSD",
        direction=1 if kind == "trade" else 0,
        time_open_msc=1000 + record_id * 100,
        time_close_msc=1050 + record_id * 100,
        volume=1.0 if kind == "trade" else 0.0,
        profit=profit,
    )


class TestManipulationMethods:
    """Test suite for MC manipulation methods."""

    def test_randomize_trades_order_exact(self) -> None:
        """Fisher-Yates exact shuffle reverses or shuffles trades."""
        records = tuple(_make_record(i) for i in range(1, 4))
        # Draw 2 (picks item 3), Draw 1 (picks item 2), Draw 0 (picks item 1)
        rng = QueueRng([2, 1, 0])
        shuffler = RandomizeTradesOrder(method="exact")
        result = shuffler.apply(records, rng=rng)
        assert [r.record_id for r in result] == [3, 2, 1]

    def test_randomize_trades_order_resampling(self) -> None:
        """Bootstrap resampling draws items with replacement."""
        records = tuple(_make_record(i) for i in range(1, 4))
        rng = QueueRng([0, 0, 0])
        shuffler = RandomizeTradesOrder(method="resampling")
        result = shuffler.apply(records, rng=rng)
        assert [r.record_id for r in result] == [1, 1, 1]

    def test_randomly_degrade_execution(self) -> None:
        """Winning trades have profit reduced when degradation triggers."""
        records = (_make_record(1, profit=100.0),)
        # probability check: draw 10 < 20 -> triggers. fraction: draw 500 -> 50% of max 10% = 5% degradation
        rng = QueueRng([10, 500])
        degrader = RandomlyDegradeExecution(probability=20, max_pct_degradation=10.0)
        result = degrader.apply(records, rng=rng)
        assert len(result) == 1
        assert result[0].profit == 95.0

    def test_machr_block_randomization(self) -> None:
        """Block randomization shuffles blocks of trades."""
        records = tuple(_make_record(i) for i in range(1, 5))
        # 4 records with block_size=2 -> 2 blocks: [1, 2] and [3, 4]
        # Pop index 1 (second block [3, 4]), then pop index 0 (first block [1, 2])
        rng = QueueRng([1, 0])
        blocker = MACHRBlockRandomization(block_size=2)
        result = blocker.apply(records, rng=rng)
        assert [r.record_id for r in result] == [3, 4, 1, 2]

    def test_simulate_parameter_jitter(self) -> None:
        """Parameter jitter scales profit by jitter factor."""
        records = (_make_record(1, profit=100.0),)
        # Draw 1500 -> offset = 1500 - 1000 = 500 -> multiplier = 1 + (0.5 * 0.1) = 1.05
        rng = QueueRng([1500])
        jitterer = SimulateParameterJitter(std_dev_pct=10.0)
        result = jitterer.apply(records, rng=rng)
        assert len(result) == 1
        assert result[0].profit == 105.0
