"""Executable UTC clock and timestamp examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from decimal import Decimal

from app.utils.time import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Returns the current timezone-aware UTC datetime.")
now = utc_now()
print("UTC Now:", now)

_header("Example 2: Formats a datetime into a canonical ISO 8601 string.")
formatted = format_utc_timestamp(now)
print("Formatted Timestamp:", formatted)

_header("Example 3: Parses an ISO 8601 UTC timestamp string.")
parsed = parse_utc_timestamp(formatted)
print("Parsed Timestamp:", parsed)

_header("Example 4: Calculates the elapsed duration between datetimes in seconds.")
age = age_seconds(parsed, reference=now)
print("Age in Seconds:", age)

_header("Example 5: Checks if a datetime is within a specified age threshold.")
fresh = is_fresh(parsed, reference=now, max_age_seconds=Decimal(60))
print("Is Fresh (within 60s):", fresh)
