"""Unit tests for deterministic random streams."""

from app.utils import derive_random_stream, get_stream_identity, next_int


def test_derivation_is_deterministic_and_order_independent() -> None:
    first = derive_random_stream(7, "fills")
    second = derive_random_stream(7, "fills")
    assert next_int(first, lower=1, upper=10) == next_int(second, lower=1, upper=10)
    assert get_stream_identity(first)["algorithm_version"] == "v1"
