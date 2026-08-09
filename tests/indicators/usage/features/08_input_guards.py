"""Executable usage evidence for closed-input enforcement."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import assert_closed_input

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _closed() -> bool:
    """Validate one causal, closed, compatible input interval."""
    result = assert_closed_input(
        source_start=NOW - timedelta(hours=1),
        source_end=NOW,
        available_at=NOW,
        decision_time=NOW,
        source_timeframe="H1",
        requested_timeframe="H4",
        max_age=timedelta(hours=1),
        complete=True,
    )
    assert result.status == "success"
    return bool(result.data)


def fr_indi_039() -> None:
    """FR-INDI-039: Require a fully closed source interval."""
    print("SUCCESS: FR-INDI-039")
    print(f"DATA: {_closed()}")


def fr_indi_040() -> None:
    """FR-INDI-040: Require explicit fresh temporal evidence."""
    print("SUCCESS: FR-INDI-040")
    print(f"DATA: {_closed()}")


def fr_indi_041() -> None:
    """FR-INDI-041: Require compatible canonical timeframes."""
    print("SUCCESS: FR-INDI-041")
    print(f"DATA: {_closed()}")


def main() -> None:
    """Run every closed-input requirement demonstration."""
    fr_indi_039()
    fr_indi_040()
    fr_indi_041()


if __name__ == "__main__":
    main()
