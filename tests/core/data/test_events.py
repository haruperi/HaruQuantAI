"""Source-backed primitive tests for donor TickEvent parity."""

from app.core.data.events import TickEvent


def test_set_and_string_preserve_timestamp_units() -> None:
    event = TickEvent()
    event.set(1700000000123, 17, 23, 1.25, 1.30, 0.5, 120, 130, True, False)
    assert event.time == 1700000000123
    assert (event.connection_hash, event.symbol_hash) == (17, 23)
    assert (event.bid, event.ask, event.volume) == (1.25, 1.3, 0.5)
    assert event.session_start_time == 120
    assert event.session_end_time == 130
    assert event.bar_open and not event.bar_close
    assert not event.is_set
    assert str(event) == "1.3,1.25"


def test_copy_values_differs_from_set_from_event_as_in_donor() -> None:
    original = TickEvent()
    original.set(222, 1, 2, 0.8, 0.9, 2.0, 8, 9, True, True)
    original.is_set = True
    copy_only = TickEvent(bar_open=False, is_set=False)
    copy_only.copy_values(original)
    assert copy_only.time == original.time
    assert copy_only.bar_close
    assert not copy_only.bar_open  # Recovered Java copyValues omission.
    assert not copy_only.is_set
    full = TickEvent()
    full.set_from_event(original)
    assert full.bar_open and full.bar_close
    assert not full.is_set
