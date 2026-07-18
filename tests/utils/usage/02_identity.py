"""Executable trace-identifier examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.identity import derive_stable_id, generate_id, validate_id


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Generates a random prefixed UUID4 trace identifier.")
generated = generate_id("req")
print("Generated ID:", generated)

_header("Example 2: Validates a trace identifier against prefix and syntax rules.")
validated = validate_id(generated, expected_prefix="req")
print("Validated ID:", validated)

_header("Example 3: Derives a deterministic SHA-256 trace identifier.")
stable = derive_stable_id("cor", "strategy:v1")
print("Stable Derived ID:", stable)
