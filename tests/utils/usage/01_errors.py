"""Executable shared-error examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.errors import (
    ValidationError,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    route_error_event,
)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Normalizes a string error code.")
normalized = normalize_error_code("validation-failed")
print("Normalized Code:", normalized)

_header("Example 2: Resolves an error code to its built-in metadata.")
metadata = get_error_metadata("VALIDATION_FAILED")
print("Error Code:", metadata.code)
print("Error Title:", metadata.title)

_header("Example 3: Maps an exception to a secret-safe error dictionary.")
mapped = map_exception(ValueError("invalid input value"))
print("Mapped Exception Payload:", mapped)

_header("Example 4: Routes a mapped exception's payload to an injected sink.")
events = []
error = ValidationError("VALIDATION_FAILED", "FIELD_MISSING")
route_error_event(error, events.append)
print("Routed Events:", events)
