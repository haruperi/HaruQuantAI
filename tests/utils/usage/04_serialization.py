"""Executable canonical serialization examples."""

import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.serialization import canonical_json, to_json_safe


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Converts supported Python types to deterministic, JSON-safe data.")
safe_data = to_json_safe({"price": Decimal("1.23"), "items": (1, 2, 3)})
print("JSON Safe Data:", safe_data)

_header("Example 2: Generates a stable sorted-key, UTF-8 encoded JSON string.")
canonical = canonical_json(safe_data)
print("Canonical JSON String:", canonical)
