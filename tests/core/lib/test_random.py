"""Tests for deterministic Mersenne Twister RandomGenerator primitives."""

from __future__ import annotations

import importlib
import math
import random

import pytest
from app.core.lib.random import (
    IRandomGenerator,
    MersenneTwisterRng,
    RandomGenerator,
)


def test_legacy_generator_modules_removed() -> None:
    """Verify legacy generator module paths are completely excised."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.core.generators")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.generators")


def test_protocol_conformance() -> None:
    """Verify RandomGenerator adheres to the IRandomGenerator protocol."""
    rng = RandomGenerator(42)
    assert isinstance(rng, IRandomGenerator)
    assert isinstance(MersenneTwisterRng(42), IRandomGenerator)
    assert MersenneTwisterRng is RandomGenerator


def test_generator_deterministic_draws_and_cloning() -> None:
    """Verify initial draw reproducibility and independent state preservation."""
    original = RandomGenerator(0)
    assert original.next_double() == 0.8444218515250481

    cloned = original.clone()
    draws_orig = [original.next_double() for _ in range(10)]
    draws_clone = [cloned.next_double() for _ in range(10)]
    assert draws_orig == draws_clone

    # Drawing from one instance must not advance the other
    c_snapshot = cloned.clone()
    original.next_double()
    assert cloned.next_double() == c_snapshot.next_double()


def test_explicit_clone_and_reseed() -> None:
    """Verify cloning with an explicit seed and re-seeding produces target sequence."""
    assert RandomGenerator(7).clone(0).next_double() == 0.8444218515250481

    gen = RandomGenerator(7)
    for _ in range(10):
        gen.next_double()
    assert gen.clone(0).next_double() == 0.8444218515250481

    # Re-seed resets sequence
    gen.seed(0)
    assert gen.next_double() == 0.8444218515250481

    # New instance with seed
    new_gen = gen.new_instance(0)
    assert new_gen.next_double() == 0.8444218515250481


def test_next_double_stepped_and_bounded() -> None:
    """Verify next_double bounded, stepped, and degenerated parameter handling."""
    rng = RandomGenerator(12345)

    # Degenerate bound (min >= max)
    assert rng.next_double(10.0, 5.0, decimals=2) == 10.0
    assert rng.next_double(5.0, 5.0, decimals=2) == 5.0

    # Stepped draws with math.ceil step alignment
    for _ in range(50):
        val = rng.next_double(1.0, 5.0, step=0.5, decimals=2)
        assert 1.0 <= val <= 5.0
        # Value must be an exact multiple of step from min_val
        steps_away = round((val - 1.0) / 0.5)
        assert math.isclose(val, 1.0 + steps_away * 0.5, abs_tol=1e-6)

    # Unstepped bounded draws
    for _ in range(50):
        val = rng.next_double(10.0, 20.0, step=0.0, decimals=3)
        assert 10.0 <= val <= 20.0


def test_next_int_stepped_and_bounded() -> None:
    """Verify next_int single-bound, range, and stepped draws."""
    rng = RandomGenerator(999)

    # Zero or negative single bound returns 0
    assert rng.next_int(0) == 0
    assert rng.next_int(-5) == 0

    # Single bound [0, bound)
    for _ in range(50):
        val = rng.next_int(10)
        assert 0 <= val < 10

    # Degenerate range min >= max
    assert rng.next_int(15, 10) == 15
    assert rng.next_int(10, 10) == 10

    # Range [min, max] with step=1
    for _ in range(50):
        val = rng.next_int(5, 12, step=1)
        assert 5 <= val <= 12

    # Stepped range [min, max] with step=5
    for _ in range(50):
        val = rng.next_int(10, 30, step=5)
        assert 10 <= val <= 30
        assert (val - 10) % 5 == 0


def test_next_long() -> None:
    """Verify next_long produces signed 64-bit integer values."""
    rng = RandomGenerator(42)
    min_int64 = -9_223_372_036_854_775_808
    max_int64 = 9_223_372_036_854_775_807
    for _ in range(25):
        val = rng.next_long()
        assert min_int64 <= val <= max_int64


def test_next_gaussian() -> None:
    """Verify next_gaussian returns standard normal distributed floats."""
    rng = RandomGenerator(42)
    draws = [rng.next_gaussian() for _ in range(100)]
    assert all(math.isfinite(d) for d in draws)
    # Approximate sanity check on finite normal sample
    mean = sum(draws) / len(draws)
    assert -1.0 < mean < 1.0


def test_probability() -> None:
    """Verify Bernoulli trial probability boundaries."""
    rng = RandomGenerator(42)
    assert not rng.probability(0.0)
    assert not rng.probability(-0.5)
    assert rng.probability(1.0)
    assert rng.probability(1.5)

    # 50% trial distribution over sample
    trials = [rng.probability(0.5) for _ in range(200)]
    assert 50 < sum(trials) < 150


def test_next_bool() -> None:
    """Verify next_bool returns boolean values."""
    rng = RandomGenerator(42)
    bools = [rng.next_bool() for _ in range(50)]
    assert all(isinstance(b, bool) for b in bools)
    assert True in bools
    assert False in bools


def test_get_random() -> None:
    """Verify get_random exposes the underlying random.Random instance."""
    rng = RandomGenerator(42)
    internal_rng = rng.get_random()
    assert isinstance(internal_rng, random.Random)
