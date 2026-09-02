"""Unit tests for kernel deterministic random streams."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.kernel.errors import ValidationError
from app.kernel.random import (
    derive_random_stream,
    get_stream_identity,
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


def test_derive_random_stream_validation_errors() -> None:
    """Verify derive_random_stream rejects invalid seeds or names."""
    with pytest.raises(ValidationError, match="RANDOM_STREAM_INVALID"):
        derive_random_stream(True, "valid_name")  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="RANDOM_STREAM_INVALID"):
        derive_random_stream("not_an_int", "valid_name")  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="RANDOM_STREAM_INVALID"):
        derive_random_stream(12345, "")

    with pytest.raises(ValidationError, match="RANDOM_STREAM_INVALID"):
        derive_random_stream(12345, "  untrimmed  ")


def test_next_uniform_validation_errors() -> None:
    """Verify next_uniform validates bounds and decimal places."""
    stream = derive_random_stream(12345, "test")

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_uniform(stream, lower=Decimal(10), upper=Decimal(5))

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_uniform(stream, lower=float("inf"), upper=Decimal(10))

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_uniform(stream, decimal_places=0)

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_uniform(stream, decimal_places=30)


def test_next_int_validation_errors() -> None:
    """Verify next_int validates upper >= lower and non-boolean arguments."""
    stream = derive_random_stream(12345, "test")

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_int(stream, lower=10, upper=5)

    with pytest.raises(ValidationError, match="RANDOM_BOUNDS_INVALID"):
        next_int(stream, lower=True, upper=10)  # type: ignore[arg-type]


def test_next_choice_validation_errors_and_weights() -> None:
    """Verify next_choice handles weighted draws and validates inputs."""
    stream = derive_random_stream(12345, "test")

    # Empty choices
    with pytest.raises(ValidationError, match="RANDOM_CHOICES_INVALID"):
        next_choice(stream, choices=[])

    with pytest.raises(ValidationError, match="RANDOM_CHOICES_INVALID"):
        next_choice(stream, choices=["A", ""])

    # Invalid weights
    with pytest.raises(ValidationError, match="RANDOM_WEIGHTS_INVALID"):
        next_choice(stream, choices=["A", "B"], weights=[1])

    with pytest.raises(ValidationError, match="RANDOM_WEIGHTS_INVALID"):
        next_choice(stream, choices=["A", "B"], weights=[1, 0])

    # Valid weighted choices
    chosen, _ = next_choice(stream, choices=["A", "B"], weights=[10, 1])
    assert chosen in ["A", "B"]


def test_get_stream_identity_and_malformed_stream() -> None:
    """Verify get_stream_identity and malformed stream validation."""
    stream = derive_random_stream(12345, "test")
    identity = get_stream_identity(stream)
    assert identity["master_seed"] == 12345

    # Malformed stream missing draw_index
    malformed = {"master_seed": 12345, "stream_name": "test", "algorithm_version": "v1"}
    with pytest.raises(ValidationError, match="RANDOM_STREAM_INVALID"):
        next_int(malformed, lower=1, upper=10)
