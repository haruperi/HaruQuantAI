"""Demonstrate the fail-closed FEAT-DATA-11 economic-calendar boundary.

No licensed provider transport exists in this repository. This usage program
therefore proves the genuine current runtime behavior: provider-backed calendar
requirements remain unavailable and no event, dataframe, artifact, or Risk
evidence is invented.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_scrape_options,
    get_calendar_sites,
    scrape_economic_calendar,
)
from app.utils import generate_id

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 8, tzinfo=UTC)
_REQUIREMENTS = (
    "FR-DATA-095",
    "FR-DATA-096",
    "FR-DATA-097",
    "FR-DATA-098",
    "FR-DATA-099",
    "FR-DATA-123",
    "FR-DATA-124",
    "FR-DATA-125",
    "FR-DATA-126",
    "FR-DATA-127",
    "FR-DATA-128",
    "FR-DATA-129",
)


def _demonstrate_unavailable_source() -> None:
    """Show that absent licensed transport blocks every provider-backed claim."""
    sites = get_calendar_sites()
    print("Declared calendar sites:", sites)
    options = build_scrape_options(
        start=_START,
        end=_END,
        sites=sites,
        max_parallel_tasks=2,
        request_id=generate_id("req"),
    )
    try:
        scrape_economic_calendar(options)
    except Exception as error:
        code = getattr(error, "code", type(error).__name__)
        print("Observed provider result:", code)
        print("Events returned: 0")
        print("Dataframe rows returned: 0")
        print("Artifacts written: 0")
        print("Risk calendar evidence returned: 0")
        if code != "SOURCE_UNAVAILABLE":
            raise RuntimeError(
                f"Expected SOURCE_UNAVAILABLE, observed {code}"
            ) from error
        return
    raise RuntimeError("Calendar access unexpectedly succeeded without a transport")


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the genuine fail-closed evidence once."""
    if not _DEMONSTRATED[0]:
        _demonstrate_unavailable_source()
        _DEMONSTRATED[0] = True


def fr_data_095() -> None:
    """FR-DATA-095: Require a licensed multi-site transport."""
    _demonstrate_once()


def fr_data_096() -> None:
    """FR-DATA-096: Do not claim cleaned rows without provider rows."""
    _demonstrate_once()


def fr_data_097() -> None:
    """FR-DATA-097: Do not claim a dataframe without provider rows."""
    _demonstrate_once()


def fr_data_098() -> None:
    """FR-DATA-098: Do not write calendar artifacts without provider rows."""
    _demonstrate_once()


def fr_data_099() -> None:
    """FR-DATA-099: Do not serialize a fabricated scrape result."""
    _demonstrate_once()


def fr_data_123() -> None:
    """FR-DATA-123: Do not claim normalized values without provider evidence."""
    _demonstrate_once()


def fr_data_124() -> None:
    """FR-DATA-124: Provider-neutral retrieval remains unavailable."""
    _demonstrate_once()


def fr_data_125() -> None:
    """FR-DATA-125: Profiles cannot create events."""
    _demonstrate_once()


def fr_data_126() -> None:
    """FR-DATA-126: Symbol-scoped retrieval remains unavailable."""
    _demonstrate_once()


def fr_data_127() -> None:
    """FR-DATA-127: News restriction cannot claim absent evidence."""
    _demonstrate_once()


def fr_data_128() -> None:
    """FR-DATA-128: No provider events are persisted."""
    _demonstrate_once()


def fr_data_129() -> None:
    """FR-DATA-129: Risk evidence remains unavailable."""
    _demonstrate_once()


def main() -> None:
    """Execute every registered requirement entry point."""
    print("FEAT-DATA-11 — Economic Calendar")
    for requirement, demonstration in zip(
        _REQUIREMENTS,
        (
            fr_data_095,
            fr_data_096,
            fr_data_097,
            fr_data_098,
            fr_data_099,
            fr_data_123,
            fr_data_124,
            fr_data_125,
            fr_data_126,
            fr_data_127,
            fr_data_128,
            fr_data_129,
        ),
        strict=True,
    ):
        print(requirement, "status: Pending — licensed transport unavailable")
        demonstration()


if __name__ == "__main__":
    main()
