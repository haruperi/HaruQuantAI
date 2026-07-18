"""Executable feeds examples for live feed status monitoring."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_feed_status
from app.services.data.contracts import (
    DataError,
    FeedStatusRequest,
)
from app.utils import generate_id

_FEED_ID = "usage-btcusd-ticks"
_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Query live feed status (buffer, drift, heartbeat metrics).")
try:
    status = get_feed_status(
        FeedStatusRequest(feed_id=_FEED_ID, request_id=generate_id("req"))
    )
    print("Feed ID:", status.feed_id)
except DataError as err:
    print("Expected feed status query error:", err.code)
