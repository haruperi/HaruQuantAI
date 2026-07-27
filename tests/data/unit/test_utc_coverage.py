"""Unit test for app/services/data/time_sessions/utc.py to reach 100% coverage."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from app.services.data.time_sessions.utc import require_utc


def test_require_utc_valid() -> None:
    """Test require_utc returns valid aware UTC datetime."""
    now = datetime.now(UTC)
    assert require_utc(now) is now


def test_require_utc_naive() -> None:
    """Test require_utc raises ValueError for naive datetime."""
    naive = datetime.now(UTC)
    with pytest.raises(ValueError, match="timestamp must be aware UTC"):
        require_utc(naive)


def test_require_utc_non_utc_timezone() -> None:
    """Test require_utc raises ValueError for non-UTC timezone."""
    non_utc = datetime.now(timezone(timedelta(hours=5)))
    with pytest.raises(ValueError, match="timestamp must be aware UTC"):
        require_utc(non_utc)
