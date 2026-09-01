"""Unit tests for kernel deterministic random streams."""

from __future__ import annotations

from app.kernel.random import (
    derive_random_stream,
    next_choice,
    next_int,
    next_uniform,
)


def test_derive_random_stream_deterministic() -> None:
    """Verify random streams generate reproducible sequence draws."""
    stream_a = derive_random_stream(12345, "simulation_run")
    stream_b = derive_random_stream(12345, "simulation_run")

    val_a, stream_a = next_uniform(stream_a)
    val_b, stream_b = next_uniform(stream_b)
    assert val_a == val_b

    int_a, stream_a = next_int(stream_a, lower=1, upper=100)
    int_b, stream_b = next_int(stream_b, lower=1, upper=100)
    assert int_a == int_b
    assert 1 <= int_a <= 100

    choice_a, _ = next_choice(stream_a, choices=["A", "B", "C"])
    choice_b, _ = next_choice(stream_b, choices=["A", "B", "C"])
    assert choice_a == choice_b
