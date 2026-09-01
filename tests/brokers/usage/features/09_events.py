"""FEAT-BRK-09: broker event normalization evidence."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import normalize_broker_event_envelope

import _support  # noqa: F401


def fr_brokers_151_event_normalization() -> None:
    """Normalize one ordered provider-authored event.

    Returns:
        None.
    """
    event = normalize_broker_event_envelope(
        source_id="ctrader:orders",
        source_sequence=1,
        event_id="event-1",
        correlation_id="corr-1",
        causation_id=None,
        emitted_at=datetime(2026, 8, 10, tzinfo=UTC),
        event_type="order_update",
        broker="ctrader",
        payload={"status": "accepted"},
    )
    print("SUCCESS: FEAT-BRK-09 broker event normalization completed")
    print(f"DATA: fields={sorted(event)}")


def main() -> None:
    """Run broker-event evidence.

    Returns:
        None.
    """
    fr_brokers_151_event_normalization()


if __name__ == "__main__":
    main()
