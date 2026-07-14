"""Run real trace-identifier examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import derive_stable_id, generate_id, validate_id


def example_generate_id() -> str:
    """Generate a new request identifier."""
    request_id = generate_id("req")
    print("Generated:", request_id)
    return request_id


def example_validate_id(value: str) -> None:
    """Validate the generated request identifier."""
    assert validate_id(value, expected_prefix="req") == value
    print("Validated:", value)


def example_derive_stable_id() -> None:
    """Derive and verify a deterministic event identifier."""
    first = derive_stable_id("evt", "dataset:demo:v1")
    second = derive_stable_id("evt", "dataset:demo:v1")
    assert first == second
    print("Stable:", first)


if __name__ == "__main__":
    generated = example_generate_id()
    example_validate_id(generated)
    example_derive_stable_id()
