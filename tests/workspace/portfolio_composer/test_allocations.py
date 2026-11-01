"""Unit tests for ComposerAllocations (PC-004)."""

from __future__ import annotations

import pytest
from app.workspace.portfolio_composer.allocations import ComposerAllocations


class FakeRNG:
    """Deterministic fake RNG recording requested bounds and returning queued draws."""

    def __init__(self, draws: list[int] | None = None) -> None:
        self.draws: list[int] = list(draws or [])
        self.requested_bounds: list[int] = []

    def next_index(self, upper_exclusive: int) -> int:
        self.requested_bounds.append(upper_exclusive)
        if not self.draws:
            raise RuntimeError("RNG draw queue empty")
        return self.draws.pop(0)


class TestComposerAllocations:
    """Test suite for ComposerAllocations.generate."""

    def test_allocations_fixture_3_members(self) -> None:
        """Verify member_count=3, simulations=1 produces ((21, 31, 48),)."""
        rng = FakeRNG([20, 30])
        result = ComposerAllocations.generate(member_count=3, simulations=1, rng=rng)
        assert result == ((21, 31, 48),)
        assert rng.requested_bounds == [98, 78]
        assert sum(result[0]) == 100

    def test_single_member_no_draws(self) -> None:
        """Verify member_count=1, simulations=2 produces ((100,), (100,))."""
        rng = FakeRNG([])
        result = ComposerAllocations.generate(member_count=1, simulations=2, rng=rng)
        assert result == ((100,), (100,))
        assert rng.requested_bounds == []

    def test_zero_simulations_no_draws(self) -> None:
        """Verify simulations=0 returns empty tuple and makes zero draws."""
        rng = FakeRNG([])
        result = ComposerAllocations.generate(member_count=5, simulations=0, rng=rng)
        assert result == ()
        assert rng.requested_bounds == []

    def test_member_count_80_minimum_zero(self) -> None:
        """Verify member_count=80 with 79 zero draws produces 79 zeros then 100."""
        rng = FakeRNG([0] * 79)
        result = ComposerAllocations.generate(member_count=80, simulations=1, rng=rng)
        expected_row = (0,) * 79 + (100,)
        assert result == (expected_row,)
        assert rng.requested_bounds == [101] * 79
        assert sum(result[0]) == 100

    def test_member_count_79_minimum_one(self) -> None:
        """Verify member_count=79 with 78 zero draws produces 78 ones then 22."""
        rng = FakeRNG([0] * 78)
        result = ComposerAllocations.generate(member_count=79, simulations=1, rng=rng)
        expected_row = (1,) * 78 + (22,)
        assert result == (expected_row,)
        assert rng.requested_bounds == [22] * 78
        assert sum(result[0]) == 100

    @pytest.mark.parametrize(
        ("members", "sims"),
        [
            (0, 1),
            (-1, 5),
            (3, -1),
            (True, 5),
            (3, False),
            (1.5, 2),
            (2, 3.0),
        ],
    )
    def test_invalid_counts_raise_value_error(
        self,
        members: object,
        sims: object,
    ) -> None:
        """Verify invalid member_count or simulations raises exact ValueError."""
        rng = FakeRNG([])
        with pytest.raises(
            ValueError,
            match=r"^member_count must be positive and simulations non-negative integers$",
        ):
            ComposerAllocations.generate(
                member_count=members,  # type: ignore[arg-type]
                simulations=sims,  # type: ignore[arg-type]
                rng=rng,
            )

    @pytest.mark.parametrize(
        "invalid_draw",
        [-1, 98, 99, 1000, True, False, "0"],
    )
    def test_invalid_fake_draw_raises_value_error(self, invalid_draw: object) -> None:
        """Verify draw outside [0, bound) or non-int raises exact ValueError."""
        rng = FakeRNG([invalid_draw])  # type: ignore[list-item]
        with pytest.raises(
            ValueError, match=r"^random index outside requested bounds$"
        ):
            ComposerAllocations.generate(member_count=3, simulations=1, rng=rng)

    def test_rng_exception_propagates_unchanged(self) -> None:
        """Verify exceptions from RNG propagate unchanged."""

        class FailingRNG:
            def next_index(self, upper_exclusive: int) -> int:
                raise ConnectionError("RNG hardware failure")

        with pytest.raises(ConnectionError, match=r"^RNG hardware failure$"):
            ComposerAllocations.generate(
                member_count=3,
                simulations=1,
                rng=FailingRNG(),
            )
