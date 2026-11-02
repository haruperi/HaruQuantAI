"""Tests for centralized deterministic RandomGenerator contracts and state cloning."""

from __future__ import annotations

import importlib

import pytest
from app.core.generators import RandomGenerator


def test_generator_move_preserves_state() -> None:
    """Verify legacy bridge is removed, initial draw value, and state isolation across clones."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.generators")

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


def test_explicit_clone_seed() -> None:
    """Verify cloning with an explicit seed produces exact target sequence."""
    assert RandomGenerator(7).clone(0).next_double() == 0.8444218515250481

    # Regardless of draws already made from the original
    gen = RandomGenerator(7)
    for _ in range(10):
        gen.next_double()
    assert gen.clone(0).next_double() == 0.8444218515250481
