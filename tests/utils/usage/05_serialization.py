"""Run real canonical serialization examples."""

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import ValidationError, canonical_json, to_json_safe


@dataclass(frozen=True)
class Position:
    """Example caller-owned serializable value."""

    symbol: str
    quantity: Decimal


def example_to_json_safe() -> None:
    """Convert a dataclass and Decimal into JSON-safe values."""
    safe = to_json_safe(Position(symbol="EURUSD", quantity=Decimal("1.25")))
    print("JSON-safe:", safe)


def example_canonical_json() -> None:
    """Serialize keys in a deterministic canonical order."""
    encoded = canonical_json({"b": 2, "a": 1})
    assert encoded == '{"a":1,"b":2}'
    print("Canonical JSON:", encoded)


def example_reject_unsafe_value() -> None:
    """Execute the unsupported-value rejection path."""
    try:
        canonical_json({"unsafe": {1, 2}})
    except ValidationError as error:
        print("Rejected unsafe value:", error.code)
    else:
        raise AssertionError("set was accepted")


if __name__ == "__main__":
    example_to_json_safe()
    example_canonical_json()
    example_reject_unsafe_value()
