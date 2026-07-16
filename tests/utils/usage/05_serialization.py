"""Executable canonical-serialization examples."""

from decimal import Decimal

from app.utils import ValidationError, canonical_json, to_json_safe


def example_to_json_safe() -> object:
    """Convert supported exact values."""
    return to_json_safe({"amount": Decimal("1.20"), "items": (1, 2)})


def example_canonical_json() -> str:
    """Produce stable sorted-key JSON."""
    return canonical_json({"b": 2, "a": 1})


def example_reject_unsafe_value() -> None:
    """Reject a non-finite value."""
    try:
        canonical_json(float("nan"))
    except ValidationError:
        return
    raise AssertionError("unsafe value was accepted")


def main() -> None:
    """Run all serialization examples."""
    json_safe = example_to_json_safe()
    canonical = example_canonical_json()
    assert json_safe == {"amount": "1.20", "items": [1, 2]}
    assert canonical == '{"a":1,"b":2}'
    example_reject_unsafe_value()
    print("JSON-safe value:", json_safe)
    print("Canonical JSON:", canonical)
    print("Serialization validation: non-finite value rejected")


if __name__ == "__main__":
    main()
