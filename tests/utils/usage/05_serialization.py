"""Executable canonical-serialization examples."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import ValidationError, canonical_json, to_json_safe


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_to_json_safe() -> None:
    """Convert supported values into deterministic JSON-safe data."""
    _header("Example 1: To JSON Safe")
    print("JSON-safe value:", to_json_safe({"amount": Decimal("1.2300")}))


def example_canonical_json() -> None:
    """Serialize a mapping with stable key ordering."""
    _header("Example 2: Canonical JSON")
    print("Canonical JSON:", canonical_json({"b": 2, "a": 1}))


def example_reject_unsafe_value() -> None:
    """Demonstrate fail-closed unsupported-value handling."""
    _header("Example 3: Reject Unsafe Value")
    try:
        canonical_json({"unsafe": object()})
    except ValidationError:
        print("Serialization validation: unsafe value rejected")


def main() -> None:
    """Run all serialization examples."""
    example_to_json_safe()
    example_canonical_json()
    example_reject_unsafe_value()


if __name__ == "__main__":
    main()
