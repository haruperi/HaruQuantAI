"""Executable trace and stable-identity examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import derive_stable_id, generate_id, validate_id


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_generate_id() -> None:
    """Generate a canonical UUID4 request identifier."""
    _header("Example 1: Generate ID")
    print("Generated request ID:", generate_id("req"))


def example_validate_id() -> None:
    """Validate a canonical UUID4 workflow identifier."""
    _header("Example 2: Validate ID")
    value = generate_id("wf")
    print("Validated workflow ID:", validate_id(value, expected_prefix="wf"))


def example_derive_stable_id() -> None:
    """Derive a deterministic non-trace artifact identity."""
    _header("Example 3: Derive Stable ID")
    print("Stable artifact ID:", derive_stable_id("id", "strategy:v1"))


def main() -> None:
    """Run all identity examples."""
    example_generate_id()
    example_validate_id()
    example_derive_stable_id()


if __name__ == "__main__":
    main()
