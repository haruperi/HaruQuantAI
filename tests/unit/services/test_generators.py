"""Unit tests for RandomGenerator seeded PRNG primitive.

Verifies deterministic reproducibility, multi-arity overloads, Gaussian statistics,
discretization step quantization, 64-bit integer bounds, and clone state isolation.
"""

from __future__ import annotations

import random

from app.services.include.generators import RandomGenerator


def test_seed_reproducibility() -> None:
    """Verify that identical seeds produce identical random sequences."""
    rng1 = RandomGenerator(seed=42)
    rng2 = RandomGenerator(seed=42)

    seq1 = [rng1.next_double() for _ in range(5)]
    seq2 = [rng2.next_double() for _ in range(5)]
    assert seq1 == seq2

    int_seq1 = [rng1.next_int(100) for _ in range(5)]
    int_seq2 = [rng2.next_int(100) for _ in range(5)]
    assert int_seq1 == int_seq2


def test_seed_re_seeding() -> None:
    """Verify re-seeding restarts sequence reproducibly."""
    rng = RandomGenerator(seed=100)
    seq1 = [rng.next_double() for _ in range(5)]

    rng.seed(100)
    seq2 = [rng.next_double() for _ in range(5)]
    assert seq1 == seq2


def test_next_double_unbounded() -> None:
    """Verify default next_double generates floats in [0.0, 1.0)."""
    rng = RandomGenerator(seed=123)
    for _ in range(100):
        val = rng.next_double()
        assert 0.0 <= val < 1.0


def test_next_double_bounded_continuous() -> None:
    """Verify next_double within continuous bounds."""
    rng = RandomGenerator(seed=123)
    for _ in range(50):
        val = rng.next_double(10.0, 20.0, step=0.0, decimals=3)
        assert 10.0 <= val <= 20.0

    # Inverted or equal bounds
    assert rng.next_double(15.0, 15.0) == 15.0
    assert rng.next_double(20.0, 10.0) == 20.0


def test_next_double_stepped_quantization() -> None:
    """Verify next_double snaps to valid discrete step values."""
    rng = RandomGenerator(seed=42)
    allowed = {10.0, 12.5, 15.0, 17.5, 20.0}
    for _ in range(100):
        val = rng.next_double(10.0, 20.0, step=2.5, decimals=1)
        assert val in allowed


def test_next_int_unbounded() -> None:
    """Verify next_int(bound) returns integers in [0, bound)."""
    rng = RandomGenerator(seed=77)
    for _ in range(50):
        val = rng.next_int(10)
        assert 0 <= val < 10

    # Non-positive bounds
    assert rng.next_int(0) == 0
    assert rng.next_int(-5) == 0


def test_next_int_bounded_and_stepped() -> None:
    """Verify next_int with min, max, and step parameters."""
    rng = RandomGenerator(seed=88)
    for _ in range(50):
        val = rng.next_int(5, 15)
        assert 5 <= val <= 15

    # Stepped integer draws
    allowed = {10, 20, 30, 40, 50}
    for _ in range(100):
        val = rng.next_int(10, 50, step=10)
        assert val in allowed

    # Equal/inverted bounds
    assert rng.next_int(20, 20) == 20
    assert rng.next_int(30, 20) == 30


def test_next_long_signed_64bit_bounds() -> None:
    """Verify next_long generates within 64-bit signed integer range."""
    rng = RandomGenerator(seed=999)
    min_long = -9_223_372_036_854_775_808
    max_long = 9_223_372_036_854_775_807

    has_pos = False
    has_neg = False
    for _ in range(100):
        val = rng.next_long()
        assert min_long <= val <= max_long
        if val > 0:
            has_pos = True
        elif val < 0:
            has_neg = True
    assert has_pos and has_neg


def test_next_gaussian_properties() -> None:
    """Verify next_gaussian generates standard normal distribution."""
    rng = RandomGenerator(seed=12345)
    samples = [rng.next_gaussian() for _ in range(1000)]
    mean = sum(samples) / len(samples)
    variance = sum((x - mean) ** 2 for x in samples) / len(samples)

    # Standard normal: mean approx 0, variance approx 1
    assert abs(mean) < 0.15
    assert abs(variance - 1.0) < 0.2


def test_probability_boundaries() -> None:
    """Verify probability edge cases and distribution."""
    rng = RandomGenerator(seed=55)
    assert not rng.probability(0.0)
    assert not rng.probability(-0.2)
    assert rng.probability(1.0)
    assert rng.probability(1.5)

    trials = [rng.probability(0.7) for _ in range(1000)]
    success_rate = sum(trials) / len(trials)
    assert 0.65 <= success_rate <= 0.75


def test_next_bool() -> None:
    """Verify next_bool generates booleans."""
    rng = RandomGenerator(seed=66)
    bools = [rng.next_bool() for _ in range(200)]
    assert True in bools
    assert False in bools


def test_clone_state_isolation() -> None:
    """Verify clone captures exact generator state and runs independently."""
    rng = RandomGenerator(seed=321)
    # Advance state
    for _ in range(10):
        rng.next_double()

    # Clone without seed copies current internal state
    cloned = rng.clone()
    assert [rng.next_double() for _ in range(10)] == [
        cloned.next_double() for _ in range(10)
    ]

    # Clone with new seed
    seeded_clone = rng.clone(seed=777)
    ref_seeded = RandomGenerator(seed=777)
    assert seeded_clone.next_double() == ref_seeded.next_double()


def test_new_instance() -> None:
    """Verify new_instance creates fresh generator."""
    rng = RandomGenerator(seed=111)
    inst1 = rng.new_instance(seed=999)
    inst2 = RandomGenerator(seed=999)
    assert inst1.next_double() == inst2.next_double()


def test_get_random() -> None:
    """Verify get_random exposes underlying random.Random."""
    rng = RandomGenerator(seed=500)
    underlying = rng.get_random()
    assert isinstance(underlying, random.Random)
