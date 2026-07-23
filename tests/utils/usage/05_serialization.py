"""Executable canonical-serialization examples."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    ValidationError,
    canonical_digest,
    canonical_json,
    to_json_safe,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_utils_013_to_json_safe() -> None:
    """FR-UTL-013: Convert supported values into deterministic JSON-safe data."""
    _header("Example 1: To JSON Safe")
    print("JSON-safe value:", to_json_safe({"amount": Decimal("1.2300")}))


def fr_utils_014_canonical_json() -> None:
    """FR-UTL-014: Serialize a mapping with stable key ordering."""
    _header("Example 2: Canonical JSON")
    print("Canonical JSON:", canonical_json({"b": 2, "a": 1}))


def fr_utils_015_reject_unsafe_value() -> None:
    """FR-UTL-015: Demonstrate fail-closed unsupported-value handling."""
    _header("Example 3: Reject Unsafe Value")
    try:
        canonical_json({"unsafe": object()})
    except ValidationError:
        print("Serialization validation: unsafe value rejected")


def fr_utils_036_canonical_digest() -> None:
    """FR-UTL-036: digest a trusted structure larger than the ceiling."""
    _header("Example 4: Canonical Digest")
    oversized = {"records": [{"i": index} for index in range(20_000)]}
    try:
        canonical_json(oversized)
    except ValidationError:
        print("canonical_json rejects >10,000 items for untrusted payloads")
    print("canonical_digest of 20,000 records:", canonical_digest(oversized))


def main() -> None:
    """Run all serialization examples."""
    fr_utils_013_to_json_safe()
    fr_utils_014_canonical_json()
    fr_utils_015_reject_unsafe_value()
    fr_utils_036_canonical_digest()


if __name__ == "__main__":
    main()
