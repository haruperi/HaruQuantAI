"""Deterministic donor RNG primitives and executable Java reference evidence.

vectors.jsonl was captured from recovered MersenneTwisterFast.java/MTRandom.java
with Java 26.0.2.1 on 2026-11-04: six seeds, 11 operations, 640 draws each.
SHA-256 donor sources: Fast 9f63f4e34c90f4457e359723bf99b1135cb6bb14413c1bfdf161361bf1679b8b;
MTRandom ce3cda9949a62c23dd80fa8b50ae2b2b8e4140d6d3f937f719409027c650df93.
Expected outputs use no Python RNG. Exact comparison covers integer/double
streams; Gaussian comparison permits 1e-14 absolute/relative libm tolerance.
Wrapper formulas follow MersenneTwisterRng.java; Python entropy initialization,
state-copy cloning and unstepped ranges are retained conveniences. The capture
harness and build files are temporary and are removed after generating evidence.
"""

from __future__ import annotations

import importlib
import json
import logging
import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

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
    assert original.next_double() == 0.5488135008937808

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
    assert RandomGenerator(7).clone(0).next_double() == 0.5488135008937808

    gen = RandomGenerator(7)
    for _ in range(10):
        gen.next_double()
    assert gen.clone(0).next_double() == 0.5488135008937808

    # Re-seed resets sequence
    gen.seed(0)
    assert gen.next_double() == 0.5488135008937808

    # New instance with seed
    new_gen = gen.new_instance(0)
    assert new_gen.next_double() == 0.5488135008937808


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

    # Donor rejects nonpositive bounds.
    for bound in (0, -5):
        with pytest.raises(ValueError):
            rng.next_int(bound)

    # Single bound [0, bound)
    for _ in range(50):
        val = rng.next_int(10)
        assert 0 <= val < 10

    # Degenerate range min >= max
    with pytest.raises(ValueError):
        rng.next_int(15, 10)
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
    """Verify the independent donor stream retains the random.Random interface."""
    rng = RandomGenerator(42)
    internal_rng = rng.get_random()
    assert isinstance(internal_rng, random.Random)


class _Vector(TypedDict):
    seed: int
    op: str
    values: list[float | int | bool]


_VECTORS: list[_Vector] = [
    json.loads(line)
    for line in (Path(__file__).parent / "fixtures/stage01_random/vectors.jsonl")
    .read_text(encoding="utf-8-sig")
    .splitlines()
]


@pytest.mark.parametrize("vector", _VECTORS, ids=lambda v: f"{v['seed']}-{v['op']}")
def test_recovered_java_vectors(vector: _Vector) -> None:
    rng = RandomGenerator(vector["seed"])
    operations: dict[str, Callable[[], float | int | bool]] = {
        "double": rng.next_double,
        "int": lambda: rng.next_int(37),
        "power": lambda: rng.next_int(1024),
        "reject": lambda: rng.next_int(1073741825),
        "long": rng.next_long,
        "gaussian": rng.next_gaussian,
        "bool": rng.next_bool,
        "stepped": lambda: rng.next_double(-2.0, 1.5, 0.5, 0),
        "range": lambda: rng.next_int(-7, 14, 3),
        "secondary": rng.get_random().random,
    }
    actual: list[float | int | bool] = []
    for i in range(len(vector["values"])):
        if vector["op"] == "probability":
            actual.append(rng.probability((0, -0.5, 1, 1.5, 0.5, math.nan)[i % 6]))
        else:
            actual.append(operations[vector["op"]]())
    if vector["op"] == "gaussian":
        assert actual == pytest.approx(vector["values"], rel=1e-14, abs=1e-14)
    else:
        assert actual == vector["values"]


def test_separate_streams_clone_cache_and_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    rng = RandomGenerator(42)
    untouched = RandomGenerator(42)
    with caplog.at_level(logging.DEBUG):
        rng.next_gaussian()
        clone = rng.clone()
        assert clone.next_gaussian() == rng.next_gaussian()
        for _ in range(20):
            rng.get_random().random()
        assert clone.next_double() == rng.next_double()
        assert clone.get_random().random() == untouched.get_random().random()
        rng.seed(42)
        assert rng.get_random().random() == RandomGenerator(42).get_random().random()
    messages = " ".join(record.message for record in caplog.records)
    for requirement in ("seeding", "cloning", "drawing"):
        assert f"FR-core-lib-random-{requirement}" in messages


def test_rounding_steps_and_invalid_ranges() -> None:
    assert RandomGenerator(42).next_double(1.125, 1.125, 0.5, 2) == 1.13
    assert RandomGenerator(42).next_double(-1.125, -1.125, 0.5, 2) == -1.12
    with pytest.raises(ZeroDivisionError):
        RandomGenerator(42).next_int(1, 3, 0)
    with pytest.raises(ValueError):
        RandomGenerator(42).next_int(2**31)
    assert RandomGenerator(42).next_int(3, 3) == 3
