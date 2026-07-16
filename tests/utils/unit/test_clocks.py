from datetime import UTC, datetime

import pytest
from app.utils import SystemClock, ValidationError, utc_now


class _FixedClock:
    def __init__(self, value: datetime) -> None:
        self._value = value

    def now(self) -> datetime:
        return self._value


def test_system_clock_returns_aware_utc() -> None:
    current = SystemClock().now()
    assert current.tzinfo is not None
    assert current.utcoffset() is not None
    assert current.utcoffset().total_seconds() == 0


def test_utc_now_uses_injected_clock_and_rejects_naive() -> None:
    expected = datetime(2026, 1, 1, tzinfo=UTC)
    assert utc_now(_FixedClock(expected)) == expected
    with pytest.raises(ValidationError):
        utc_now(_FixedClock(expected.replace(tzinfo=None)))
