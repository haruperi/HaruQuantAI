"""Exclusive-account and foreign/manual activity replay evidence."""

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state.runtime import validate_account_activity_ownership


def test_exclusive_interval_accepts_no_foreign_activity() -> None:
    """A verified exclusive account interval needs no replay events."""
    validate_account_activity_ownership({"mode": "exclusive"}, ())


def test_nonexclusive_interval_accepts_complete_ordered_replay() -> None:
    """Every contiguous source event is admitted in authority order."""
    validate_account_activity_ownership(
        {"mode": "replay"},
        (
            {"source_sequence": 1, "event_type": "manual_deal"},
            {"source_sequence": 2, "event_type": "foreign_close"},
        ),
    )


@pytest.mark.parametrize(
    ("ownership", "activity"),
    [
        ({"mode": "unknown"}, ()),
        ({"mode": "replay"}, ()),
        (
            {"mode": "replay"},
            ({"source_sequence": 2, "event_type": "manual_deal"},),
        ),
        (
            {"mode": "exclusive"},
            ({"source_sequence": 1, "event_type": "manual_deal"},),
        ),
    ],
)
def test_missing_external_activity_blocks_certification(
    ownership: object, activity: tuple[dict[str, object], ...]
) -> None:
    """Incomplete activity evidence never enters the parity envelope."""
    with pytest.raises(SimulationError):
        validate_account_activity_ownership(ownership, activity)
