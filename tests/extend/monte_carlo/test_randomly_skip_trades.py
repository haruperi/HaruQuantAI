"""Unit tests for RandomlySkipTrades per RET-004 specification."""

from typing import cast, override

import pytest
from app.extend.monte_carlo.manipulation.randomly_skip_trades import (
    RandomlySkipTrades,
    SkipRandom,
)
from app.extend.what_if.base import WhatIfRecord
from pydantic import ValidationError


class FakeRng(SkipRandom):
    """Deterministic queued RNG tracking bounds and returning queued indices."""

    def __init__(self, draws: list[int]) -> None:
        self.draws = list(draws)
        self.requested_bounds: list[int] = []

    @override
    def next_index(self, upper_exclusive: int) -> int:
        self.requested_bounds.append(upper_exclusive)
        return self.draws.pop(0)


def _make_record(record_id: int, kind: str = "trade") -> WhatIfRecord:
    return WhatIfRecord(
        record_id=record_id,
        kind=kind,  # type: ignore[arg-type]
        symbol="EURUSD",
        direction=1 if kind == "trade" else 0,
        time_open_msc=1000 + record_id * 100,
        time_close_msc=1050 + record_id * 100,
        volume=1.0 if kind == "trade" else 0.0,
        profit=50.0,
    )


class TestRandomlySkipTrades:
    """Test suite for RandomlySkipTrades."""

    def test_skip_deterministic(self) -> None:
        """Five records IDs 1..5, probability 50 and draws 0,2,0 produce IDs 3,5 and bounds 5,4,3."""
        records = tuple(_make_record(i) for i in range(1, 6))
        rng = FakeRng([0, 2, 0])
        skipper = RandomlySkipTrades(probability=50)

        result = skipper.apply(records, rng=rng)

        assert [r.record_id for r in result] == [3, 5]
        assert rng.requested_bounds == [5, 4, 3]
        # Assert input sequence was not mutated
        assert [r.record_id for r in records] == [1, 2, 3, 4, 5]

    def test_pending_and_balance_eligible(self) -> None:
        """Pending and balance records are eligible for deletion."""
        records = (
            _make_record(1, kind="pending"),
            _make_record(2, kind="balance"),
        )
        rng = FakeRng([0])
        skipper = RandomlySkipTrades(probability=50)
        result = skipper.apply(records, rng=rng)
        assert len(result) == 1
        assert result[0].record_id == 2

    def test_rounding_cases(self) -> None:
        """Probability 100 removes all; n=5 prob=10 removes 1; n=4 prob=10 removes 0."""
        # 100% removes all
        rec5 = tuple(_make_record(i) for i in range(1, 6))
        rng = FakeRng([0, 0, 0, 0, 0])
        assert RandomlySkipTrades(probability=100).apply(rec5, rng=rng) == []

        # n=5 prob=10 -> removes 1 (floor(0.5 + 0.5) == 1)
        rng1 = FakeRng([0])
        res1 = RandomlySkipTrades(probability=10).apply(rec5, rng=rng1)
        assert len(res1) == 4

        # n=4 prob=10 -> removes 0 (floor(0.4 + 0.5) == 0)
        rec4 = tuple(_make_record(i) for i in range(1, 5))
        rng0 = FakeRng([])
        res0 = RandomlySkipTrades(probability=10).apply(rec4, rng=rng0)
        assert len(res0) == 4
        assert rng0.requested_bounds == []

    def test_empty_records(self) -> None:
        """Empty records returns [] and makes no RNG call."""
        rng = FakeRng([])
        assert RandomlySkipTrades(probability=50).apply((), rng=rng) == []
        assert rng.requested_bounds == []

    def test_validation_errors(self) -> None:
        """Invalid 0, 101, bool probability rejects with ValidationError."""
        with pytest.raises(ValidationError):
            RandomlySkipTrades(probability=0)

        with pytest.raises(ValidationError):
            RandomlySkipTrades(probability=101)

        with pytest.raises(ValidationError):
            RandomlySkipTrades(probability=True)

    def test_rng_out_of_bounds_errors(self) -> None:
        """RNG returning out of bounds or non-int raises exact ValueError."""
        rec = (_make_record(1),)

        # Index >= bound
        rng_high = FakeRng([1])
        with pytest.raises(ValueError, match="random index outside requested bounds"):
            RandomlySkipTrades(probability=100).apply(rec, rng=rng_high)

        # Negative index
        rng_neg = FakeRng([-1])
        with pytest.raises(ValueError, match="random index outside requested bounds"):
            RandomlySkipTrades(probability=100).apply(rec, rng=rng_neg)

        # Bool returned
        class BoolRng(SkipRandom):
            @override
            def next_index(self, upper_exclusive: int) -> int:
                return cast("int", True)

        with pytest.raises(ValueError, match="random index outside requested bounds"):
            RandomlySkipTrades(probability=100).apply(rec, rng=BoolRng())
