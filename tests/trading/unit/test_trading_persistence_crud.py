"""Unit tests for Trading domain CRUD persistence operations."""

from __future__ import annotations

from app.services.trading.persistence.create import (
    create_closed_position_record,
    create_event_record,
    create_execution_session_record,
)
from app.services.trading.persistence.delete import (
    archive_execution_session_record,
)
from app.services.trading.persistence.read import (
    read_event_records,
    read_execution_session_record,
)


def test_trading_persistence_exports() -> None:
    """Verify trading persistence functions can be imported."""
    assert create_closed_position_record is not None
    assert create_event_record is not None
    assert create_execution_session_record is not None
    assert read_event_records is not None
    assert read_execution_session_record is not None
    assert archive_execution_session_record is not None
